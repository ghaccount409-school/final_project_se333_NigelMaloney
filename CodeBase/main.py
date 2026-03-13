from mcp.server.fastmcp import FastMCP

mcp = FastMCP("SE333 MCP Server")

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


if __name__ == "__main__":
    # IMPORTANT: Use SSE transport so VS Code can connect via URL.
    mcp.run(transport="sse")
