# SE333 Final Project — MCP Server

A Python-based **Model Context Protocol (MCP) server** providing automated code quality analysis and testing analysis tools, built with `fastmcp` over SSE transport.

**Repository:** [github.com/ghaccount409-school/final_project_se333_NigelMaloney](https://github.com/ghaccount409-school/final_project_se333_NigelMaloney)

---

## Table of Contents

1. [Overview](#overview)
2. [Installation & Setup](#installation--setup)
3. [Configuration](#configuration)
4. [MCP Tools Reference](#mcp-tools-reference)
   - [analyze_coverage](#analyze_coverage)
   - [generate_test_report](#generate_test_report)
   - [detect_code_smells](#detect_code_smells)
   - [scan_security_risks](#scan_security_risks)
   - [enforce_style_guide](#enforce_style_guide)
   - [check_complexity](#check_complexity)
5. [Testing](#testing)
6. [Troubleshooting & FAQ](#troubleshooting--faq)

---

## Overview

This MCP server exposes six code quality analysis tools aligned with the workflows described in `tester.prompt.md` and `codereview.prompt.md`. All tools are callable by any MCP-compatible client (VS Code, Claude Desktop, etc.) over HTTP/SSE.

**Technology stack:**

| Component | Version |
|-----------|---------|
| Python | 3.14.0 |
| fastmcp / mcp | 3.1.0+ / 1.26.0+ |
| Transport | SSE (`http://127.0.0.1:8000/sse`) |
| Test runner | pytest 9.0+ with pytest-cov |

---

## Installation & Setup

### Prerequisites

- Python 3.14+
- [`uv`](https://docs.astral.sh/uv/) package manager

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/ghaccount409-school/final_project_se333_NigelMaloney.git
cd final_project_se333_NigelMaloney

# 2. Install dependencies (creates .venv automatically)
uv sync

# 3. Install dev dependencies (pytest, pytest-cov)
uv add pytest pytest-cov --dev

# 4. Start the server
uv run python main.py
```

The server starts on `http://127.0.0.1:8000`. You should see:

```
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

## Configuration

### VS Code (`mcp.json`)

Add the following to `%APPDATA%\Code\User\mcp.json` (Windows) or `~/.config/Code/User/mcp.json` (macOS/Linux):

```json
{
  "servers": {
    "se333-MCP-server": {
      "url": "http://127.0.0.1:8000/sse",
      "type": "http"
    }
  }
}
```

### Claude Desktop

```json
{
  "mcpServers": {
    "se333-server": {
      "command": "uv",
      "args": ["run", "python", "/absolute/path/to/main.py"]
    }
  }
}
```

### Server defaults

| Setting | Default | Notes |
|---------|---------|-------|
| Host | `127.0.0.1` | Loopback only — not exposed to network |
| Port | `8000` | Change in `fastmcp` if needed |
| Transport | `sse` | Required for VS Code HTTP-type connections |

---

## MCP Tools Reference

### `analyze_coverage`

**Source:** `tester.prompt.md` — step 5 (parse Jacoco/coverage output and identify gaps)

Evaluates a code coverage ratio and returns a structured status with a recommendation.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `covered_lines` | `int` | Lines covered by tests |
| `total_lines` | `int` | Total lines in the codebase |

**Returns:** `dict`

| Key | Type | Description |
|-----|------|-------------|
| `coverage` | `float` | Percentage rounded to 2 decimal places |
| `covered_lines` | `int` | Echo of input |
| `total_lines` | `int` | Echo of input |
| `status` | `str` | `"excellent"` \| `"good"` \| `"acceptable"` \| `"poor"` \| `"error"` |
| `recommendation` | `str` | Human-readable guidance |

**Status thresholds:**

| Status | Condition |
|--------|-----------|
| `excellent` | 100% |
| `good` | ≥ 90% |
| `acceptable` | ≥ 70% |
| `poor` | < 70% |
| `error` | `total_lines == 0` |

**Example:**

```python
analyze_coverage(covered_lines=95, total_lines=100)
# → {"coverage": 95.0, "status": "good", "recommendation": "High coverage. Consider testing edge cases.", ...}
```

---

### `generate_test_report`

**Source:** `tester.prompt.md` — steps 2–3 (run tests, interpret results)

Generates a summary report from raw test execution counters.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `total_tests` | `int` | Total tests executed |
| `passed_tests` | `int` | Tests that passed |
| `failed_tests` | `int` | Tests that failed |
| `skipped_tests` | `int` | Tests that were skipped |

**Returns:** `dict`

| Key | Type | Description |
|-----|------|-------------|
| `summary` | `dict` | Raw counts (`total`, `passed`, `failed`, `skipped`) |
| `metrics` | `dict` | `pass_rate`, `failure_rate`, `skip_rate` (percentages) |
| `status` | `str` | `"passed"` \| `"failed"` \| `"partial"` \| `"skipped"` \| `"error"` |
| `action` | `str` | Recommended next step |

**Example:**

```python
generate_test_report(total_tests=37, passed_tests=37, failed_tests=0, skipped_tests=0)
# → {"status": "passed", "metrics": {"pass_rate": 100.0, ...}, "action": "All tests passed. Ready for deployment."}
```

---

### `detect_code_smells`

**Source:** `codereview.prompt.md` — code smell detection and refactoring suggestions

Identifies the presence of common code quality anti-patterns.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `has_duplicates` | `bool` | Code duplication detected |
| `has_long_functions` | `bool` | Functions exceed recommended length |
| `has_unused_vars` | `bool` | Unused variables or imports present |

**Returns:** `dict`

| Key | Type | Description |
|-----|------|-------------|
| `detected_smells` | `int` | Number of smells found |
| `smells` | `list[str]` | Identifiers: `"code_duplication"`, `"long_functions"`, `"unused_variables"` |
| `severity` | `str` | `"low"` \| `"medium"` \| `"high"` |
| `refactoring_suggestions` | `list[str]` | One suggestion per smell |
| `priority` | `str` | `"soon"` (0–1 smells) \| `"immediate"` (2+ smells) |

**Severity logic:** `high` if ≥ 2 smells, `medium` if exactly 1, `low` if none.

**Example:**

```python
detect_code_smells(has_duplicates=True, has_long_functions=True, has_unused_vars=False)
# → {"detected_smells": 2, "severity": "high", "priority": "immediate", ...}
```

---

### `scan_security_risks`

**Source:** `codereview.prompt.md` — security vulnerability scanning (CodeQL-equivalent checks)

Checks for three high-impact vulnerability classes with CWE references and remediation steps.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `has_sql_injection` | `bool` | SQL injection risk present |
| `has_hardcoded_secrets` | `bool` | Credentials/tokens hardcoded in source |
| `has_weak_crypto` | `bool` | Weak or deprecated cryptographic algorithm used |

**Returns:** `dict`

| Key | Type | Description |
|-----|------|-------------|
| `vulnerabilities_found` | `int` | Count of detected vulnerabilities |
| `vulnerabilities` | `list[dict]` | Each entry has `type`, `cve` (CWE ID), `remediation` |
| `risk_level` | `str` | `"low"` \| `"high"` \| `"critical"` |
| `action_required` | `bool` | `True` if any vulnerabilities found |

**Risk level logic:** SQL injection → `"critical"` (takes precedence). Secrets or weak crypto → `"high"` if no SQL injection.

**Vulnerability reference table:**

| Type | CWE | Remediation |
|------|-----|-------------|
| `SQL_INJECTION` | CWE-89 | Use parameterized queries / ORM |
| `HARDCODED_CREDENTIALS` | CWE-798 | Move to env vars or secret vaults |
| `WEAK_CRYPTOGRAPHY` | CWE-327 | Use `hashlib` / `cryptography` with modern algorithms |

**Example:**

```python
scan_security_risks(has_sql_injection=False, has_hardcoded_secrets=True, has_weak_crypto=False)
# → {"vulnerabilities_found": 1, "risk_level": "high", "action_required": True, ...}
```

---

### `enforce_style_guide`

**Source:** `codereview.prompt.md` — style guide enforcement with auto-fix guidance

Checks three PEP 8 / style guide criteria and returns a numeric compliance score.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `uses_consistent_naming` | `bool` | Naming conventions are consistent (snake_case, PascalCase) |
| `follows_pep8` | `bool` | Code is PEP 8 compliant |
| `has_docstrings` | `bool` | Public functions and classes are documented |

**Returns:** `dict`

| Key | Type | Description |
|-----|------|-------------|
| `violations` | `int` | Number of violations (0–3) |
| `details` | `list[dict]` | Each entry has `rule`, `severity`, `fix` |
| `style_score` | `int` | `100 − (violations × 25)` |
| `compliant` | `bool` | `True` only when `violations == 0` |

**Severity per rule:**

| Rule | Severity |
|------|----------|
| `naming_convention` | `"warning"` |
| `pep8_compliance` | `"error"` |
| `documentation` | `"warning"` |

**Example:**

```python
enforce_style_guide(uses_consistent_naming=True, follows_pep8=False, has_docstrings=True)
# → {"violations": 1, "style_score": 75, "compliant": False, "details": [{"rule": "pep8_compliance", ...}]}
```

---

### `check_complexity`

**Source:** `codereview.prompt.md` — static analysis / complexity metrics (analogous to SpotBugs/PMD output)

Classifies McCabe cyclomatic complexity and computes a density metric.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `cyclomatic_complexity` | `int` | McCabe complexity score for the code unit |
| `lines_of_code` | `int` | Total lines in the analyzed unit |

**Returns:** `dict`

| Key | Type | Description |
|-----|------|-------------|
| `cyclomatic_complexity` | `int` | Echo of input |
| `lines_of_code` | `int` | Echo of input |
| `complexity_level` | `str` | `"low"` \| `"moderate"` \| `"high"` |
| `density` | `float` | `complexity / lines_of_code` (rounded to 3 dp) |
| `recommendation` | `str` | Guidance based on level |
| `needs_refactoring` | `bool` | `True` when level is `"high"` |

**Classification thresholds:**

| Level | Condition |
|-------|-----------|
| `low` | ≤ 5 |
| `moderate` | 6–10 |
| `high` | > 10 |

**Example:**

```python
check_complexity(cyclomatic_complexity=12, lines_of_code=80)
# → {"complexity_level": "high", "density": 0.15, "needs_refactoring": True, ...}
```

---

## Testing

```bash
# Run all tests
uv run pytest test_main.py -v

# Run with coverage report
uv run pytest test_main.py --cov=main --cov-report=term-missing

# Run a specific test class
uv run pytest test_main.py::TestScanSecurityRisks -v
```

**Test suite summary (37 tests, 100% coverage):**

| Class | Tests | Tool covered |
|-------|-------|-------------|
| `TestAnalyzeCoverage` | 6 | `analyze_coverage` |
| `TestGenerateTestReport` | 6 | `generate_test_report` |
| `TestDetectCodeSmells` | 6 | `detect_code_smells` |
| `TestScanSecurityRisks` | 6 | `scan_security_risks` |
| `TestEnforceStyleGuide` | 6 | `enforce_style_guide` |
| `TestCheckComplexity` | 6 | `check_complexity` |
| `TestMainEntrypoint` | 1 | Server startup |

---

## Troubleshooting & FAQ

### Installation

**Q: `No module named 'mcp'` or `No module named 'fastmcp'`**

Run `uv sync` from the project root to install all declared dependencies. If `uv` is not on your PATH, locate it at `~/.local/bin/uv` (macOS/Linux) or `%USERPROFILE%\.local\bin\uv.exe` (Windows).

---

**Q: `Python 3.14 not found` or `requires-python >=3.14`**

Check your version with `python --version`. If below 3.14, install via [python.org](https://www.python.org/downloads/) or `pyenv`:

```bash
pyenv install 3.14.0
pyenv local 3.14.0
uv sync
```

---

**Q: Virtual environment activation fails on Windows**

```powershell
# PowerShell (may require execution policy change)
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\.venv\Scripts\Activate.ps1
```

Or use `uv run` directly to avoid manual activation.

---

### Runtime

**Q: `OSError: [Errno 10048] / Address already in use` on port 8000**

Another process is using port 8000 (possibly a previous server instance).

```powershell
# Windows — find and kill the process
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process
```

---

**Q: VS Code cannot discover the MCP tools**

1. Confirm the server is running: open a browser to `http://127.0.0.1:8000/sse` — you should see a streaming response.
2. Check your `mcp.json` uses `"type": "http"` and the exact URL `http://127.0.0.1:8000/sse`.
3. Reload VS Code: `Ctrl+Shift+P` → *Developer: Reload Window*.
4. Inspect MCP logs: `Ctrl+Shift+P` → *MCP: Show Logs*.

---

**Q: Tool call returns `422 Unprocessable Entity`**

All boolean parameters must be JSON booleans (`true`/`false`), not strings (`"true"`). All integer parameters must be JSON numbers, not strings.

```json
// Wrong
{"has_duplicates": "true", "has_long_functions": "false"}

// Correct
{"has_duplicates": true, "has_long_functions": false}
```

---

**Q: `analyze_coverage` returns `"status": "error"`**

`total_lines` was passed as `0`. Ensure the coverage tool ran against actual source files before calling this tool.

---

### Testing

**Q: `pytest` not found**

```bash
uv add pytest pytest-cov --dev
```

---

**Q: `test_main_runs_mcp_server` fails with `OSError`**

Port 8000 is occupied (a live server is already running). Stop it before running tests, as this test mocks `FastMCP.run` but earlier test runs may have left the event loop in a bad state. Kill the server process and re-run.

---

**Q: Coverage drops below 100% after adding a new tool**

Write at least one test for every new branch introduced. Run:

```bash
uv run pytest test_main.py --cov=main --cov-report=term-missing
```

The `Missing` column will show the exact lines not yet covered.

---

### Security & Production

**Q: Is it safe to expose this server on a public IP?**

No. The server has no authentication, no TLS, and no rate limiting. It is intended for local/loopback use only. For any networked deployment, place it behind a reverse proxy (e.g., nginx) with HTTPS and API key authentication.

---

**Q: How do I add authentication to the MCP server?**

`fastmcp` does not provide built-in auth middleware. Options:

1. **Reverse proxy** — put nginx or Caddy in front and require a bearer token header.
2. **Custom middleware** — wrap the ASGI app from `mcp` with a Starlette `BaseHTTPMiddleware` that validates a secret.
3. **Environment-based secret** — check `os.environ["API_KEY"]` inside each tool and raise `ValueError` on mismatch.

---

**Last Updated:** March 12, 2026  
**Version:** 0.1.0
