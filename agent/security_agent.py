import re

from rules.security_rules import (
    SQL_PATTERNS,
    PASSWORD_PATTERNS,
    API_KEY_PATTERNS,
    DANGEROUS_FUNCTIONS,
    SUBPROCESS_PATTERN,
    XSS_PATTERNS,
    JAVA_COMMAND_PATTERNS,
)

from agent.severity import annotate_findings


class SecurityAgent:

    def analyze(self, code, language="python"):

        findings = []

        lines = code.split("\n")
        normalized_language = (language or "python").lower()

        for line_number, line in enumerate(lines, start=1):

            # SQL Injection
            for pattern in SQL_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append({
                        "type": "SQL Injection",
                        "severity": "Critical",
                        "line": line_number,
                        "message": line.strip(),
                        "recommendation": "Use parameterized queries."
                    })

            # Hardcoded Password
            for pattern in PASSWORD_PATTERNS:
                if re.search(pattern, line):
                    findings.append({
                        "type": "Hardcoded Password",
                        "severity": "High",
                        "line": line_number,
                        "message": line.strip(),
                        "recommendation": "Store passwords in environment variables."
                    })

            # API Key
            for pattern in API_KEY_PATTERNS:
                if re.search(pattern, line):
                    findings.append({
                        "type": "Hardcoded API Key",
                        "severity": "High",
                        "line": line_number,
                        "message": line.strip(),
                        "recommendation": "Store secrets securely."
                    })

            # eval() / exec()
            if any(token in line for token in DANGEROUS_FUNCTIONS):
                findings.append({
                    "type": "Dangerous Dynamic Execution",
                    "severity": "Critical",
                    "line": line_number,
                    "message": line.strip(),
                    "recommendation": "Avoid dynamic code execution."
                })

            # subprocess(shell=True)
            if re.search(SUBPROCESS_PATTERN, line):
                findings.append({
                    "type": "Command Injection",
                    "severity": "Critical",
                    "line": line_number,
                    "message": line.strip(),
                    "recommendation": "Do not use shell=True with user input."
                })

            if normalized_language == "java":
                for pattern in JAVA_COMMAND_PATTERNS:
                    if re.search(pattern, line):
                        findings.append({
                            "type": "Command Injection",
                            "severity": "Critical",
                            "line": line_number,
                            "message": line.strip(),
                            "recommendation": "Avoid shell execution with user-controlled input."
                        })

            for pattern in XSS_PATTERNS:
                if re.search(pattern, line):
                    findings.append({
                        "type": "Cross Site Scripting",
                        "severity": "High",
                        "line": line_number,
                        "message": line.strip(),
                        "recommendation": "Encode untrusted output before rendering it."
                    })

        return annotate_findings(findings)