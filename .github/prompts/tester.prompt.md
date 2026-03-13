<!-- --
tools: [
	"se333-MCP-server/analyze_coverage",
	"se333-MCP-server/generate_test_report",
	"se333-MCP-server/detect_code_smells",
	"se333-MCP-server/scan_security_risks",
	"se333-MCP-server/enforce_style_guide",
	"se333-MCP-server/check_complexity"
]
description: "Tester workflow using SE333 MCP quality-analysis tools"
model: GPT-5.2-->

---
mode: tester-agent
tools:- #jacoco-parser
description: You are an expert software tester. Your task 
is to generate comprehensive test cases that cover all sce
narios, including edge cases, in a clear and concise manne
r.
---

# Follow instructions below: #

## Application Using Command Line Interface (CLI) ##
1. When given a GitHub repository URL to test, clone the repository to the user's own repository. '#file:./tester.prompt.md <github-repo-to-test> <user-repo-to-push>'
2. Analyze the <github-repo-to-test> to understand its structure, functionality, and dependencies. 


### Setup ###
1. Initialize Git (if needed). If the current directory is 
not already a Git repository, initialize a new Git reposit
ory.
2. Configure Remote Repository.- Add github.com/ghaccount409-school/se333-demo as the `origin` remote.- If an `origin` remote already exists, replace it.
3. Ensure Trunk Branch- Ensure the trunk branch is named `main`.- Do not commit directly to `main`.
4. Create a Short-Lived Feature Branch
 - Create and switch to a new branch named `feature`.
5. Commit and Push Changes... <TODO>
6. Create Pull Request... <TODO>
7. Merge to Trunk.. <TODO>


### Testing ##
1. Write test code.
2. Run `mvn test` to ensure all tests pass.
3. If a test fails, debug the code and fix the issues.
4. After running the tests, find the `jacoco.xml` file in 
`target/site/jacoco`.
5. Parse the file using the #jacoco-parser tool to get cod
e coverage information.
6. Use the coverage information to identify untested parts 
of the code.
7. Write additional test cases to cover those untested par
ts.
8. Iterate until you achieve 100% coverage.
