import ast


def calculate_complexity(tree):

    findings = []

    complexity = 1

    for node in ast.walk(tree):

        if isinstance(node,

            (

                ast.If,

                ast.For,

                ast.While,

                ast.Try,

                ast.With,

                ast.BoolOp

            )):

            complexity += 1

    if complexity >= 10:

        findings.append({

            "type": "High Cyclomatic Complexity",

            "severity": "High",

            "line": 1,

            "message": f"Complexity = {complexity}",

            "recommendation": "Reduce nested decision points."

        })

    return findings