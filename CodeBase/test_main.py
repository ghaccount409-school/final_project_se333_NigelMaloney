import runpy
import json
import pytest
from unittest.mock import patch
from main import (
    analyze_coverage, generate_test_report, detect_code_smells,
    scan_security_risks, enforce_style_guide, check_complexity,
    evaluate_jacoco_report, evaluate_pmd_report,
    evaluate_spotbugs_report, evaluate_codeql_sarif,
    check_java_quality_prerequisites,
    run_java_quality_evaluation,
)


# ============================================================================
# COVERAGE ANALYSIS TESTS (tester.prompt.md)
# ============================================================================

class TestAnalyzeCoverage:
    def test_perfect_coverage(self):
        result = analyze_coverage(100, 100)
        assert result["coverage"] == 100.0
        assert result["status"] == "excellent"
        assert "100% coverage achieved" in result["recommendation"]

    def test_good_coverage(self):
        result = analyze_coverage(95, 100)
        assert result["coverage"] == 95.0
        assert result["status"] == "good"

    def test_acceptable_coverage(self):
        result = analyze_coverage(75, 100)
        assert result["coverage"] == 75.0
        assert result["status"] == "acceptable"

    def test_poor_coverage(self):
        result = analyze_coverage(50, 100)
        assert result["coverage"] == 50.0
        assert result["status"] == "poor"

    def test_zero_lines_handled(self):
        result = analyze_coverage(0, 0)
        assert result["status"] == "error"

    def test_partial_coverage(self):
        result = analyze_coverage(7, 10)
        assert result["coverage"] == 70.0
        assert result["status"] == "acceptable"


class TestGenerateTestReport:
    def test_all_tests_passed(self):
        result = generate_test_report(10, 10, 0, 0)
        assert result["status"] == "passed"
        assert result["metrics"]["pass_rate"] == 100.0
        assert "All tests passed" in result["action"]

    def test_some_tests_failed(self):
        result = generate_test_report(10, 6, 4, 0)
        assert result["status"] == "failed"
        assert result["metrics"]["pass_rate"] == 60.0
        assert result["metrics"]["failure_rate"] == 40.0

    def test_some_tests_skipped(self):
        result = generate_test_report(10, 8, 0, 2)
        assert result["status"] == "partial"
        assert result["metrics"]["skip_rate"] == 20.0

    def test_all_tests_skipped(self):
        result = generate_test_report(10, 0, 0, 10)
        assert result["status"] == "skipped"

    def test_zero_tests_error(self):
        result = generate_test_report(0, 0, 0, 0)
        assert result["status"] == "error"

    def test_test_summary_accuracy(self):
        result = generate_test_report(5, 3, 1, 1)
        assert result["summary"]["total"] == 5
        assert result["summary"]["passed"] == 3
        assert result["summary"]["failed"] == 1
        assert result["summary"]["skipped"] == 1


# ============================================================================
# CODE SMELL DETECTION TESTS (codereview.prompt.md)
# ============================================================================

class TestDetectCodeSmells:
    def test_no_smells_detected(self):
        result = detect_code_smells(False, False, False)
        assert result["detected_smells"] == 0
        assert result["severity"] == "low"
        assert result["priority"] == "soon"

    def test_code_duplication_detected(self):
        result = detect_code_smells(True, False, False)
        assert result["detected_smells"] == 1
        assert "code_duplication" in result["smells"]
        assert any("Extract" in s for s in result["refactoring_suggestions"])

    def test_long_functions_detected(self):
        result = detect_code_smells(False, True, False)
        assert result["detected_smells"] == 1
        assert "long_functions" in result["smells"]
        assert result["severity"] == "medium"

    def test_unused_variables_detected(self):
        result = detect_code_smells(False, False, True)
        assert result["detected_smells"] == 1
        assert "unused_variables" in result["smells"]

    def test_multiple_smells_high_priority(self):
        result = detect_code_smells(True, True, True)
        assert result["detected_smells"] == 3
        assert result["severity"] == "high"
        assert result["priority"] == "immediate"

    def test_two_smells_high_severity(self):
        result = detect_code_smells(True, True, False)
        assert result["detected_smells"] == 2
        assert result["severity"] == "high"


# ============================================================================
# SECURITY SCANNING TESTS (codereview.prompt.md)
# ============================================================================

class TestScanSecurityRisks:
    def test_no_vulnerabilities(self):
        result = scan_security_risks(False, False, False)
        assert result["vulnerabilities_found"] == 0
        assert result["risk_level"] == "low"
        assert result["action_required"] is False

    def test_sql_injection_critical(self):
        result = scan_security_risks(True, False, False)
        assert result["vulnerabilities_found"] == 1
        assert result["risk_level"] == "critical"
        assert any(v["type"] == "SQL_INJECTION" for v in result["vulnerabilities"])

    def test_hardcoded_secrets_high(self):
        result = scan_security_risks(False, True, False)
        assert result["vulnerabilities_found"] == 1
        assert result["risk_level"] == "high"
        assert any("HARDCODED" in v["type"] for v in result["vulnerabilities"])

    def test_weak_crypto_high(self):
        result = scan_security_risks(False, False, True)
        assert result["vulnerabilities_found"] == 1
        assert result["risk_level"] == "high"

    def test_multiple_vulnerabilities_critical(self):
        result = scan_security_risks(True, True, True)
        assert result["vulnerabilities_found"] == 3
        assert result["risk_level"] == "critical"
        assert result["action_required"] is True

    def test_vulnerability_remediation_included(self):
        result = scan_security_risks(True, False, False)
        vuln = result["vulnerabilities"][0]
        assert "remediation" in vuln
        assert "cve" in vuln
        assert "CWE" in vuln["cve"]


# ============================================================================
# STYLE GUIDE ENFORCEMENT TESTS (codereview.prompt.md)
# ============================================================================

class TestEnforceStyleGuide:
    def test_fully_compliant(self):
        result = enforce_style_guide(True, True, True)
        assert result["violations"] == 0
        assert result["compliant"] is True
        assert result["style_score"] == 100

    def test_naming_convention_violation(self):
        result = enforce_style_guide(False, True, True)
        assert result["violations"] == 1
        assert any(d["rule"] == "naming_convention" for d in result["details"])

    def test_pep8_violation(self):
        result = enforce_style_guide(True, False, True)
        assert result["violations"] == 1
        assert any(d["rule"] == "pep8_compliance" for d in result["details"])

    def test_documentation_violation(self):
        result = enforce_style_guide(True, True, False)
        assert result["violations"] == 1
        assert any(d["rule"] == "documentation" for d in result["details"])

    def test_multiple_violations(self):
        result = enforce_style_guide(False, False, False)
        assert result["violations"] == 3
        assert result["compliant"] is False
        assert result["style_score"] == 25  # 100 - (3 * 25)

    def test_violation_contains_fixes(self):
        result = enforce_style_guide(False, False, False)
        assert all("fix" in d for d in result["details"])


# ============================================================================
# COMPLEXITY CHECKING TESTS (codereview.prompt.md)
# ============================================================================

class TestCheckComplexity:
    def test_low_complexity(self):
        result = check_complexity(3, 50)
        assert result["complexity_level"] == "low"
        assert "well-structured" in result["recommendation"]
        assert result["needs_refactoring"] is False

    def test_moderate_complexity(self):
        result = check_complexity(7, 100)
        assert result["complexity_level"] == "moderate"
        assert result["needs_refactoring"] is False

    def test_high_complexity(self):
        result = check_complexity(15, 100)
        assert result["complexity_level"] == "high"
        assert "Refactor" in result["recommendation"]
        assert result["needs_refactoring"] is True

    def test_complexity_density_calculation(self):
        result = check_complexity(10, 100)
        assert result["density"] == 0.1

    def test_high_density_warning(self):
        result = check_complexity(20, 50)
        assert result["density"] == 0.4
        assert result["complexity_level"] == "high"

    def test_boundary_cases(self):
        result_5 = check_complexity(5, 50)
        assert result_5["complexity_level"] == "low"
        
        result_10 = check_complexity(10, 50)
        assert result_10["complexity_level"] == "moderate"


class TestRealQualityIntegration:
    def test_check_java_quality_prerequisites_ready_with_wrapper(self, tmp_path):
        project_path = tmp_path / "java-project"
        project_path.mkdir(parents=True)
        (project_path / "pom.xml").write_text("<project></project>", encoding="utf-8")
        (project_path / "mvnw.cmd").write_text("echo maven", encoding="utf-8")

        with patch("main.shutil.which") as mock_which:
            mock_which.side_effect = lambda cmd: "C:/Java/bin/java.exe" if cmd == "java" else None
            result = check_java_quality_prerequisites(str(project_path))

        assert result["ready"] is True
        assert result["checks"]["java_available"] is True
        assert result["checks"]["maven_wrapper_available"] is True

    def test_check_java_quality_prerequisites_missing_requirements(self, tmp_path):
        project_path = tmp_path / "java-project"
        project_path.mkdir(parents=True)

        with patch("main.shutil.which", return_value=None):
            result = check_java_quality_prerequisites(str(project_path))

        assert result["ready"] is False
        assert "pom.xml not found in project path" in result["missing"]
        assert "Java runtime not found in PATH" in result["missing"]

    def test_evaluate_jacoco_report(self, tmp_path):
        report_path = tmp_path / "jacoco.xml"
        report_path.write_text(
            '<report><counter type="LINE" missed="10" covered="90"/></report>',
            encoding="utf-8",
        )

        result = evaluate_jacoco_report(str(report_path))

        assert result["status"] == "ok"
        assert result["coverage"] == 90.0
        assert result["level"] == "good"

    def test_evaluate_pmd_report(self, tmp_path):
        report_path = tmp_path / "pmd.xml"
        report_path.write_text(
            """
            <pmd>
              <file name="X.java">
                <violation priority="1">critical issue</violation>
                <violation priority="3">minor issue</violation>
              </file>
            </pmd>
            """,
            encoding="utf-8",
        )

        result = evaluate_pmd_report(str(report_path))

        assert result["status"] == "ok"
        assert result["violations"] == 2
        assert result["risk_level"] == "high"

    def test_evaluate_spotbugs_report(self, tmp_path):
        report_path = tmp_path / "spotbugsXml.xml"
        report_path.write_text(
            """
            <BugCollection>
              <BugInstance priority="2" category="SECURITY"/>
              <BugInstance priority="4" category="STYLE"/>
            </BugCollection>
            """,
            encoding="utf-8",
        )

        result = evaluate_spotbugs_report(str(report_path))

        assert result["status"] == "ok"
        assert result["findings"] == 2
        assert result["category_counts"]["SECURITY"] == 1
        assert result["risk_level"] == "high"

    def test_evaluate_codeql_sarif(self, tmp_path):
        report_path = tmp_path / "codeql.sarif"
        report_path.write_text(
            json.dumps(
                {
                    "runs": [
                        {
                            "results": [
                                {"level": "error", "ruleId": "java/sql-injection"},
                                {"level": "warning", "ruleId": "java/path-injection"},
                            ]
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        result = evaluate_codeql_sarif(str(report_path))

        assert result["status"] == "ok"
        assert result["results"] == 2
        assert result["level_counts"]["error"] == 1
        assert result["risk_level"] == "critical"

    def test_run_java_quality_evaluation_with_mocked_commands(self, tmp_path):
        project_path = tmp_path / "java-project"
        (project_path / "target" / "site" / "jacoco").mkdir(parents=True)
        (project_path / "target").mkdir(parents=True, exist_ok=True)

        (project_path / "pom.xml").write_text("<project></project>", encoding="utf-8")
        (project_path / "target" / "site" / "jacoco" / "jacoco.xml").write_text(
            '<report><counter type="LINE" missed="0" covered="10"/></report>',
            encoding="utf-8",
        )
        (project_path / "target" / "pmd.xml").write_text("<pmd></pmd>", encoding="utf-8")
        (project_path / "target" / "spotbugsXml.xml").write_text(
            "<BugCollection></BugCollection>",
            encoding="utf-8",
        )

        class Completed:
            def __init__(self):
                self.returncode = 0
                self.stdout = "ok"
                self.stderr = ""

        with patch("main.subprocess.run", return_value=Completed()), patch(
            "main.check_java_quality_prerequisites",
            return_value={"ready": True, "checks": {}, "resolved": {}, "missing": []},
        ):
            result = run_java_quality_evaluation(str(project_path))

        assert result["status"] == "ok"
        assert result["evaluations"]["jacoco"]["coverage"] == 100.0
        assert result["evaluations"]["pmd"]["violations"] == 0
        assert result["evaluations"]["spotbugs"]["findings"] == 0
        assert result["evaluations"]["codeql"]["status"] == "not_provided"

    def test_run_java_quality_evaluation_fails_preflight(self, tmp_path):
        project_path = tmp_path / "java-project"
        project_path.mkdir(parents=True)

        with patch(
            "main.check_java_quality_prerequisites",
            return_value={
                "ready": False,
                "checks": {"java_available": False},
                "resolved": {},
                "missing": ["Java runtime not found in PATH"],
            },
        ):
            result = run_java_quality_evaluation(str(project_path))

        assert result["status"] == "error"
        assert result["message"] == "Prerequisite check failed"
        assert result["preflight"]["ready"] is False


# ============================================================================
# SERVER ENTRYPOINT TEST
# ============================================================================

class TestMainEntrypoint:
    def test_main_runs_mcp_server(self):
        with patch("mcp.server.fastmcp.FastMCP.run") as mock_run:
            runpy.run_module("main", run_name="__main__")
            mock_run.assert_called_once_with(transport="sse")
