import ast

from agent.severity import annotate_findings
from analyzers.code_smells import detect_code_smells
from analyzers.complexity import calculate_complexity
from analyzers.java_analyzer import analyze_java



class CodeAnalysisAgent:
    
    def analyze(self, code, language="python"):

        normalized_language = (language or "python").lower()

        if normalized_language == "java":

            return analyze_java(code)

        findings = []

        try:

            tree = ast.parse(code)

        except SyntaxError as e:

            return annotate_findings([
                {
                    "type": "Syntax Error",
                    "severity": "Critical",
                    "line": e.lineno,
                    "message": str(e),
                    "recommendation": "Fix syntax before analysis."
                }
            ])

        findings.extend(detect_code_smells(tree))

        findings.extend(calculate_complexity(tree))

        return annotate_findings(findings)
    
