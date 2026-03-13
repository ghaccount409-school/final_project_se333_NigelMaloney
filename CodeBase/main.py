from mcp.server.fastmcp import FastMCP
import json
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET

mcp = FastMCP("SE333 MCP Server")


def _run_command(command: list[str], cwd: str) -> dict:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        return {
            "success": completed.returncode == 0,
            "command": " ".join(command),
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    except FileNotFoundError as exc:
        return {
            "success": False,
            "command": " ".join(command),
            "returncode": -1,
            "stdout": "",
            "stderr": str(exc),
        }


def _resolve_maven_command(project_path: str) -> list[str]:
    mvnw_cmd = os.path.join(project_path, "mvnw.cmd")
    mvnw_unix = os.path.join(project_path, "mvnw")

    if os.path.isfile(mvnw_cmd):
        return [mvnw_cmd]
    if os.path.isfile(mvnw_unix):
        return [mvnw_unix]
    return ["mvn"]


def _collect_java_quality_prerequisites(project_path: str, codeql_sarif_path: str = "") -> dict:
    java_executable = shutil.which("java")
    maven_executable = shutil.which("mvn")
    has_maven_wrapper = (
        os.path.isfile(os.path.join(project_path, "mvnw.cmd"))
        or os.path.isfile(os.path.join(project_path, "mvnw"))
    )

    checks = {
        "project_path_exists": os.path.isdir(project_path),
        "pom_exists": os.path.isfile(os.path.join(project_path, "pom.xml")),
        "java_available": java_executable is not None,
        "maven_available": maven_executable is not None,
        "maven_wrapper_available": has_maven_wrapper,
        "codeql_sarif_provided": bool(codeql_sarif_path),
        "codeql_sarif_exists": True if not codeql_sarif_path else os.path.isfile(codeql_sarif_path),
    }

    missing = []
    if not checks["project_path_exists"]:
        missing.append("Project path does not exist")
    if not checks["pom_exists"]:
        missing.append("pom.xml not found in project path")
    if not checks["java_available"]:
        missing.append("Java runtime not found in PATH")
    if not (checks["maven_available"] or checks["maven_wrapper_available"]):
        missing.append("Maven not found and no Maven wrapper (mvnw/mvnw.cmd) present")
    if codeql_sarif_path and not checks["codeql_sarif_exists"]:
        missing.append("Provided CodeQL SARIF file does not exist")

    return {
        "ready": len(missing) == 0,
        "checks": checks,
        "resolved": {
            "java": java_executable,
            "maven": maven_executable,
        },
        "missing": missing,
    }


def _parse_jacoco_xml(report_path: str) -> dict:
    tree = ET.parse(report_path)
    root = tree.getroot()

    line_counter = None
    for counter in root.findall("counter"):
        if counter.get("type") == "LINE":
            line_counter = counter
            break

    if line_counter is None:
        return {
            "status": "error",
            "message": "LINE counter not found in JaCoCo report",
            "report_path": report_path,
        }

    missed = int(line_counter.get("missed", "0"))
    covered = int(line_counter.get("covered", "0"))
    total = missed + covered

    if total == 0:
        return {
            "status": "error",
            "message": "No executable lines found in JaCoCo report",
            "report_path": report_path,
            "coverage": 0,
            "covered_lines": covered,
            "total_lines": total,
        }

    coverage = round((covered / total) * 100, 2)

    if coverage == 100:
        level = "excellent"
    elif coverage >= 90:
        level = "good"
    elif coverage >= 70:
        level = "acceptable"
    else:
        level = "poor"

    return {
        "status": "ok",
        "report_path": report_path,
        "coverage": coverage,
        "covered_lines": covered,
        "total_lines": total,
        "level": level,
    }


def _parse_pmd_xml(report_path: str) -> dict:
    tree = ET.parse(report_path)
    root = tree.getroot()

    violations = root.findall(".//violation")
    total = len(violations)

    by_priority = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
    for violation in violations:
        priority = violation.get("priority", "5")
        if priority not in by_priority:
            by_priority[priority] = 0
        by_priority[priority] += 1

    if by_priority.get("1", 0) > 0 or by_priority.get("2", 0) > 0:
        risk = "high"
    elif total > 0:
        risk = "medium"
    else:
        risk = "low"

    return {
        "status": "ok",
        "report_path": report_path,
        "violations": total,
        "priority_counts": by_priority,
        "risk_level": risk,
    }


def _parse_spotbugs_xml(report_path: str) -> dict:
    tree = ET.parse(report_path)
    root = tree.getroot()

    findings = root.findall(".//BugInstance")
    total = len(findings)

    by_priority = {"1": 0, "2": 0, "3": 0, "4": 0}
    by_category = {}

    for finding in findings:
        priority = finding.get("priority", "4")
        category = finding.get("category", "UNKNOWN")

        if priority not in by_priority:
            by_priority[priority] = 0
        by_priority[priority] += 1

        if category not in by_category:
            by_category[category] = 0
        by_category[category] += 1

    if by_priority.get("1", 0) > 0 or by_priority.get("2", 0) > 0:
        risk = "high"
    elif total > 0:
        risk = "medium"
    else:
        risk = "low"

    return {
        "status": "ok",
        "report_path": report_path,
        "findings": total,
        "priority_counts": by_priority,
        "category_counts": by_category,
        "risk_level": risk,
    }


def _parse_codeql_sarif(report_path: str) -> dict:
    with open(report_path, "r", encoding="utf-8") as report_file:
        payload = json.load(report_file)

    runs = payload.get("runs", [])
    results = []
    for run in runs:
        results.extend(run.get("results", []))

    by_level = {"error": 0, "warning": 0, "note": 0}
    rule_ids = {}
    for result in results:
        level = result.get("level", "warning")
        rule_id = result.get("ruleId", "UNKNOWN_RULE")

        if level not in by_level:
            by_level[level] = 0
        by_level[level] += 1

        if rule_id not in rule_ids:
            rule_ids[rule_id] = 0
        rule_ids[rule_id] += 1

    if by_level.get("error", 0) > 0:
        risk = "critical"
    elif by_level.get("warning", 0) > 0:
        risk = "high"
    elif len(results) > 0:
        risk = "medium"
    else:
        risk = "low"

    return {
        "status": "ok",
        "report_path": report_path,
        "results": len(results),
        "level_counts": by_level,
        "rule_counts": rule_ids,
        "risk_level": risk,
    }

# ============================================================================
# TESTING & CODE QUALITY ANALYSIS TOOLS (from tester.prompt.md)
# ============================================================================

@mcp.tool()
def analyze_coverage(covered_lines: int, total_lines: int) -> dict:
    """Analyze code coverage and identify gaps.
    
    Args:
        covered_lines: Number of lines covered by tests
        total_lines: Total lines in codebase
        
    Returns:
        Dictionary with coverage percentage and recommendations
    """
    if total_lines == 0:
        return {"coverage": 0, "status": "error", "message": "No lines to analyze"}
    
    coverage_percent = (covered_lines / total_lines) * 100
    
    if coverage_percent == 100:
        status = "excellent"
        recommendation = "100% coverage achieved. Maintain this standard."
    elif coverage_percent >= 90:
        status = "good"
        recommendation = "High coverage. Consider testing edge cases."
    elif coverage_percent >= 70:
        status = "acceptable"
        recommendation = "Increase coverage by testing untested branches."
    else:
        status = "poor"
        recommendation = "Significant gaps. Write tests for uncovered code."
    
    return {
        "coverage": round(coverage_percent, 2),
        "covered_lines": covered_lines,
        "total_lines": total_lines,
        "status": status,
        "recommendation": recommendation
    }


@mcp.tool()
def generate_test_report(total_tests: int, passed_tests: int, 
                         failed_tests: int, skipped_tests: int) -> dict:
    """Generate a comprehensive test execution report.
    
    Args:
        total_tests: Total number of tests executed
        passed_tests: Number of passing tests
        failed_tests: Number of failing tests
        skipped_tests: Number of skipped tests
        
    Returns:
        Dictionary with test results and recommendations
    """
    if total_tests == 0:
        return {"status": "error", "message": "No tests executed"}
    
    pass_rate = (passed_tests / total_tests) * 100
    
    if failed_tests > 0:
        status = "failed"
        action = "Debug and fix failing tests before release."
    elif skipped_tests == total_tests:
        status = "skipped"
        action = "Enable and fix skipped tests."
    elif pass_rate == 100:
        status = "passed"
        action = "All tests passed. Ready for deployment."
    else:
        status = "partial"
        action = "Address skipped tests."
    
    return {
        "summary": {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "skipped": skipped_tests
        },
        "metrics": {
            "pass_rate": round(pass_rate, 2),
            "failure_rate": round((failed_tests / total_tests) * 100, 2),
            "skip_rate": round((skipped_tests / total_tests) * 100, 2)
        },
        "status": status,
        "action": action
    }


# ============================================================================
# CODE REVIEW & QUALITY TOOLS (from codereview.prompt.md)
# ============================================================================

@mcp.tool()
def detect_code_smells(has_duplicates: bool, has_long_functions: bool, 
                      has_unused_vars: bool) -> dict:
    """Detect common code quality issues (code smells).
    
    Args:
        has_duplicates: Whether code duplication is present
        has_long_functions: Whether functions exceed recommended length
        has_unused_vars: Whether unused variables exist
        
    Returns:
        Dictionary with detected smells and refactoring suggestions
    """
    smells = []
    suggestions = []
    
    if has_duplicates:
        smells.append("code_duplication")
        suggestions.append("Extract common code into reusable functions.")
    
    if has_long_functions:
        smells.append("long_functions")
        suggestions.append("Break long functions into smaller, focused methods.")
    
    if has_unused_vars:
        smells.append("unused_variables")
        suggestions.append("Remove unused variables and clean up imports.")
    
    return {
        "detected_smells": len(smells),
        "smells": smells,
        "severity": "high" if len(smells) >= 2 else "medium" if len(smells) == 1 else "low",
        "refactoring_suggestions": suggestions,
        "priority": "immediate" if len(smells) >= 2 else "soon"
    }


@mcp.tool()
def scan_security_risks(has_sql_injection: bool, has_hardcoded_secrets: bool,
                        has_weak_crypto: bool) -> dict:
    """Scan for common security vulnerabilities.
    
    Args:
        has_sql_injection: Whether SQL injection vulnerabilities exist
        has_hardcoded_secrets: Whether credentials are hardcoded
        has_weak_crypto: Whether weak cryptography is used
        
    Returns:
        Dictionary with security findings and remediation steps
    """
    vulnerabilities = []
    risk_level = "low"
    
    if has_sql_injection:
        vulnerabilities.append({
            "type": "SQL_INJECTION",
            "cve": "CWE-89",
            "remediation": "Use parameterized queries and ORM frameworks."
        })
        risk_level = "critical"
    
    if has_hardcoded_secrets:
        vulnerabilities.append({
            "type": "HARDCODED_CREDENTIALS",
            "cve": "CWE-798",
            "remediation": "Move secrets to environment variables or secure vaults."
        })
        if risk_level != "critical":
            risk_level = "high"
    
    if has_weak_crypto:
        vulnerabilities.append({
            "type": "WEAK_CRYPTOGRAPHY",
            "cve": "CWE-327",
            "remediation": "Use standard libraries (hashlib, cryptography) with modern algorithms."
        })
        if risk_level == "low":
            risk_level = "high"
    
    return {
        "vulnerabilities_found": len(vulnerabilities),
        "vulnerabilities": vulnerabilities,
        "risk_level": risk_level,
        "action_required": len(vulnerabilities) > 0
    }


@mcp.tool()
def enforce_style_guide(uses_consistent_naming: bool, follows_pep8: bool,
                        has_docstrings: bool) -> dict:
    """Enforce code style guide compliance.
    
    Args:
        uses_consistent_naming: Whether naming conventions are consistent
        follows_pep8: Whether code follows PEP 8 guidelines
        has_docstrings: Whether functions and classes have documentation
        
    Returns:
        Dictionary with style violations and corrections
    """
    violations = []
    
    if not uses_consistent_naming:
        violations.append({
            "rule": "naming_convention",
            "severity": "warning",
            "fix": "Use snake_case for functions/variables, PascalCase for classes."
        })
    
    if not follows_pep8:
        violations.append({
            "rule": "pep8_compliance",
            "severity": "error",
            "fix": "Run 'black' or 'autopep8' to auto-format code."
        })
    
    if not has_docstrings:
        violations.append({
            "rule": "documentation",
            "severity": "warning",
            "fix": "Add docstrings to all public functions and classes."
        })
    
    return {
        "violations": len(violations),
        "details": violations,
        "style_score": max(0, 100 - (len(violations) * 25)),
        "compliant": len(violations) == 0
    }


@mcp.tool()
def check_complexity(cyclomatic_complexity: int, lines_of_code: int) -> dict:
    """Check code complexity metrics.
    
    Args:
        cyclomatic_complexity: McCabe complexity score
        lines_of_code: Total lines in analyzed code
        
    Returns:
        Dictionary with complexity assessment and recommendations
    """
    if cyclomatic_complexity <= 5:
        complexity_level = "low"
        recommendation = "Code is well-structured and maintainable."
    elif cyclomatic_complexity <= 10:
        complexity_level = "moderate"
        recommendation = "Consider simplifying complex conditionals."
    else:
        complexity_level = "high"
        recommendation = "Refactor: Extract methods, use design patterns."
    
    density = cyclomatic_complexity / max(1, lines_of_code) if lines_of_code > 0 else 0
    
    return {
        "cyclomatic_complexity": cyclomatic_complexity,
        "lines_of_code": lines_of_code,
        "complexity_level": complexity_level,
        "density": round(density, 3),
        "recommendation": recommendation,
        "needs_refactoring": complexity_level == "high"
    }


@mcp.tool()
def evaluate_jacoco_report(report_path: str) -> dict:
    """Parse and evaluate a JaCoCo XML report file."""
    if not os.path.isfile(report_path):
        return {
            "status": "error",
            "message": "JaCoCo report not found",
            "report_path": report_path,
        }

    try:
        return _parse_jacoco_xml(report_path)
    except Exception as exc:
        return {
            "status": "error",
            "message": f"Failed to parse JaCoCo report: {exc}",
            "report_path": report_path,
        }


@mcp.tool()
def evaluate_pmd_report(report_path: str) -> dict:
    """Parse and evaluate a PMD XML report file."""
    if not os.path.isfile(report_path):
        return {
            "status": "error",
            "message": "PMD report not found",
            "report_path": report_path,
        }

    try:
        return _parse_pmd_xml(report_path)
    except Exception as exc:
        return {
            "status": "error",
            "message": f"Failed to parse PMD report: {exc}",
            "report_path": report_path,
        }


@mcp.tool()
def evaluate_spotbugs_report(report_path: str) -> dict:
    """Parse and evaluate a SpotBugs XML report file."""
    if not os.path.isfile(report_path):
        return {
            "status": "error",
            "message": "SpotBugs report not found",
            "report_path": report_path,
        }

    try:
        return _parse_spotbugs_xml(report_path)
    except Exception as exc:
        return {
            "status": "error",
            "message": f"Failed to parse SpotBugs report: {exc}",
            "report_path": report_path,
        }


@mcp.tool()
def evaluate_codeql_sarif(report_path: str) -> dict:
    """Parse and evaluate a CodeQL SARIF report file."""
    if not os.path.isfile(report_path):
        return {
            "status": "error",
            "message": "CodeQL SARIF report not found",
            "report_path": report_path,
        }

    try:
        return _parse_codeql_sarif(report_path)
    except Exception as exc:
        return {
            "status": "error",
            "message": f"Failed to parse CodeQL SARIF report: {exc}",
            "report_path": report_path,
        }


@mcp.tool()
def run_java_quality_evaluation(
    project_path: str,
    codeql_sarif_path: str = "",
    include_integration_tests: bool = False,
) -> dict:
    """Run JaCoCo, PMD, and SpotBugs against a Java Maven project and evaluate outputs.

    Args:
        project_path: Path to the Java project root (must contain pom.xml)
        codeql_sarif_path: Optional path to a CodeQL SARIF file for evaluation
        include_integration_tests: Whether to include integration tests in JaCoCo run
    """
    preflight = check_java_quality_prerequisites(project_path, codeql_sarif_path)
    if not preflight["ready"]:
        return {
            "status": "error",
            "message": "Prerequisite check failed",
            "project_path": project_path,
            "preflight": preflight,
        }

    maven_cmd = _resolve_maven_command(project_path)

    jacoco_cmd = maven_cmd + ["-B"]
    if not include_integration_tests:
        jacoco_cmd.extend(
            [
                "-Dsurefire.excludes=**/*IT.java,**/*IntegrationTests.java",
                "-DskipITs=true",
            ]
        )
    jacoco_cmd.extend(["test", "jacoco:report"])

    jacoco_exec = _run_command(jacoco_cmd, project_path)
    pmd_exec = _run_command(maven_cmd + ["-B", "pmd:pmd"], project_path)
    spotbugs_exec = _run_command(
        maven_cmd + ["-B", "com.github.spotbugs:spotbugs-maven-plugin:4.8.6.6:spotbugs"],
        project_path,
    )

    jacoco_path = os.path.join(project_path, "target", "site", "jacoco", "jacoco.xml")
    pmd_path = os.path.join(project_path, "target", "pmd.xml")
    spotbugs_path = os.path.join(project_path, "target", "spotbugsXml.xml")

    jacoco_result = evaluate_jacoco_report(jacoco_path)
    pmd_result = evaluate_pmd_report(pmd_path)
    spotbugs_result = evaluate_spotbugs_report(spotbugs_path)

    codeql_result = {
        "status": "not_provided",
        "message": "No CodeQL SARIF report path provided",
    }
    if codeql_sarif_path:
        codeql_result = evaluate_codeql_sarif(codeql_sarif_path)

    overall_status = "ok"
    for execution in (jacoco_exec, pmd_exec, spotbugs_exec):
        if not execution["success"]:
            overall_status = "partial"
            break

    for evaluation in (jacoco_result, pmd_result, spotbugs_result):
        if evaluation.get("status") == "error":
            overall_status = "partial"
            break

    return {
        "status": overall_status,
        "project_path": project_path,
        "preflight": preflight,
        "execution_mode": {
            "include_integration_tests": include_integration_tests,
        },
        "commands": {
            "jacoco": jacoco_exec,
            "pmd": pmd_exec,
            "spotbugs": spotbugs_exec,
        },
        "evaluations": {
            "jacoco": jacoco_result,
            "pmd": pmd_result,
            "spotbugs": spotbugs_result,
            "codeql": codeql_result,
        },
    }


@mcp.tool()
def check_java_quality_prerequisites(project_path: str, codeql_sarif_path: str = "") -> dict:
    """Check whether Java quality evaluation prerequisites are available.

    Validates Java runtime, Maven or wrapper, project path/pom.xml,
    and optional CodeQL SARIF path.
    """
    return _collect_java_quality_prerequisites(project_path, codeql_sarif_path)


if __name__ == "__main__":
    # IMPORTANT: Use SSE transport so VS Code can connect via URL.
    mcp.run(transport="sse")
