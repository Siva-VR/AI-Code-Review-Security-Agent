# Final Demonstration Script

## Demo Goal

Show the full AI Code Review & Security Analysis Agent workflow end to end:
code submission, validation, review analysis, remediation guidance, PR summary,
PDF export, and grounded conversational follow-up.

---

## 1. Opening

"This project is a multi-agent code review platform for Python and Java.
It detects code smells, security vulnerabilities, and design issues,
then generates remediation guidance, a PR summary, and a PDF report.
It also supports a conversational assistant grounded in a secure coding knowledge base."

---

## 2. Demo Flow

### Step 1: Show the UI

Open the Streamlit app and point out the main workflow:

- Paste code or upload a file.
- Automatic language detection.
- Validation before analysis.
- Review results with findings, severity, remediation, and PR summary.
- PDF report export.

### Step 2: Python code sample

Use the Python security sample or a similar short example.

Talk track:

"The platform first detects the language and validates the submission.
Then the orchestrator runs the analysis agents and produces severity-ranked findings."

What to highlight:

- Code smell findings.
- Security issues such as hardcoded secrets, SQL injection, eval, or exec usage.
- Severity scores and line numbers.
- Remediation details attached to each finding.

### Step 3: Java code sample

Switch to the Java sample with deeper nesting and a vulnerable query pattern.

Talk track:

"The same pipeline works for Java. The code analysis agent flags design and maintainability issues,
while the security agent highlights the vulnerable query and command execution paths."

What to highlight:

- Long parameter list.
- Deep nesting.
- Hardcoded secret handling.
- Command injection or SQL injection.

### Step 4: Pull request summary

Open the PR summary tab.

Talk track:

"The PR summary converts findings into a concise engineer-friendly review summary,
prioritizes fixes, and gives a merge readiness judgment."

What to highlight:

- Executive overview.
- Severity breakdown.
- Prioritized fix list.
- Merge readiness state.

### Step 5: PDF export

Show the exported PDF report path or open the generated PDF.

Talk track:

"The final report is exportable as a PDF and includes the findings summary,
severity breakdown, remediation roadmap, and overall code quality assessment."

What to highlight:

- Report title.
- Findings table.
- Remediation roadmap.
- Code snapshot.

### Step 6: Conversational assistant

Ask a follow-up question based on one finding.

Example questions:

- "Why is this SQL injection finding critical?"
- "Show a safer fix for this query."
- "How do I avoid hardcoded secrets in Java?"

Talk track:

"The assistant uses retrieval-augmented generation to ground the answer in the secure coding knowledge base,
so follow-up guidance stays specific and practical."

---

## 3. Recommended Three-Sample Set

Use these three submissions for the final walkthrough:

1. Python security sample: demonstrates hardcoded secrets, SQL injection, eval, and exec.
2. Java bad code sample: demonstrates code smells, nesting, and maintainability issues.
3. Java security sample: demonstrates SQL injection and command execution risk.

This set shows both breadth and depth across quality, security, remediation, and reporting.

---

## 4. Closing Statement

"This project completes a full review pipeline from code submission to analysis,
remediation, conversational follow-up, and exportable reporting.
It is ready for final demonstration and handoff."
