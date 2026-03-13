import json
from unittest.mock import patch

from main import (
    analyze_coverage,
    generate_test_report,
    detect_code_smells,
    scan_security_risks,
    enforce_style_guide,
    check_complexity,
    evaluate_codeql_sarif,
    run_java_quality_evaluation,
)


class TestFunctionalWorkflows:
    def test_tester_workflow_end_to_end(self):
        initial_coverage = analyze_coverage(68, 100)
        assert initial_coverage["status"] == "poor"

        improved_coverage = analyze_coverage(100, 100)
        test_report = generate_test_report(42, 42, 0, 0)

        assert improved_coverage["coverage"] == 100.0
        assert improved_coverage["status"] == "excellent"
        assert test_report["status"] == "passed"
        assert test_report["metrics"]["pass_rate"] == 100.0

    def test_codereview_workflow_end_to_end(self):
        smells = detect_code_smells(True, True, False)
        security = scan_security_risks(False, True, False)
        style = enforce_style_guide(True, False, True)
        complexity = check_complexity(12, 80)

        assert smells["severity"] == "high"
        assert security["risk_level"] == "high"
        assert style["compliant"] is False
        assert complexity["needs_refactoring"] is True

    def test_codeql_sarif_functional_evaluation(self, tmp_path):
        sarif_path = tmp_path / "codeql.sarif"
        sarif_path.write_text(
            json.dumps(
                {
                    "runs": [
                        {
                            "results": [
                                {"level": "error", "ruleId": "java/sql-injection"},
                                {"level": "warning", "ruleId": "java/path-injection"},
                                {"level": "note", "ruleId": "java/log-forging"},
                            ]
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        result = evaluate_codeql_sarif(str(sarif_path))

        assert result["status"] == "ok"
        assert result["results"] == 3
        assert result["level_counts"]["error"] == 1
        assert result["risk_level"] == "critical"

    def test_java_quality_evaluation_functional_path(self, tmp_path):
        project_path = tmp_path / "java-project"
        (project_path / "target" / "site" / "jacoco").mkdir(parents=True)

        (project_path / "pom.xml").write_text("<project></project>", encoding="utf-8")
        (project_path / "target" / "site" / "jacoco" / "jacoco.xml").write_text(
            '<report><counter type="LINE" missed="5" covered="95"/></report>',
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

        with patch(
            "main.check_java_quality_prerequisites",
            return_value={"ready": True, "checks": {}, "resolved": {}, "missing": []},
        ), patch("main.subprocess.run", return_value=Completed()):
            result = run_java_quality_evaluation(str(project_path), include_integration_tests=False)

        assert result["status"] == "ok"
        assert result["execution_mode"]["include_integration_tests"] is False
        assert result["evaluations"]["jacoco"]["coverage"] == 95.0
        assert result["evaluations"]["pmd"]["status"] == "ok"
        assert result["evaluations"]["spotbugs"]["status"] == "ok"
