import ast

from rules.code_smell_rules import (
    CODE_SMELL_TYPES,
    LARGE_CLASS_THRESHOLD,
    LONG_METHOD_THRESHOLD,
    MAX_ARGUMENTS_THRESHOLD,
    MAX_NESTING_THRESHOLD,
)


def _nesting_depth(node, current_depth=0):
    if not isinstance(node, ast.AST):
        return current_depth

    child_depths = [current_depth]
    for child in ast.iter_child_nodes(node):
        next_depth = current_depth + 1 if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With)) else current_depth
        child_depths.append(_nesting_depth(child, next_depth))
    return max(child_depths)


def detect_code_smells(tree):
    findings = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            statement_count = len(node.body)
            if statement_count > LONG_METHOD_THRESHOLD:
                findings.append({
                    "type": CODE_SMELL_TYPES["long_method"],
                    "severity": "Medium",
                    "line": node.lineno,
                    "message": f"Function '{node.name}' contains {statement_count} statements.",
                    "recommendation": "Split the function into smaller units with single responsibilities.",
                })

            if len(node.args.args) > MAX_ARGUMENTS_THRESHOLD:
                findings.append({
                    "type": CODE_SMELL_TYPES["too_many_arguments"],
                    "severity": "Medium",
                    "line": node.lineno,
                    "message": f"Function '{node.name}' takes {len(node.args.args)} parameters.",
                    "recommendation": "Wrap related inputs into a data object or reduce parameter count.",
                })

            nesting_depth = _nesting_depth(node)
            if nesting_depth > MAX_NESTING_THRESHOLD:
                findings.append({
                    "type": CODE_SMELL_TYPES["deep_nesting"],
                    "severity": "Medium",
                    "line": node.lineno,
                    "message": f"Function '{node.name}' has nesting depth {nesting_depth}.",
                    "recommendation": "Flatten nested logic with guard clauses or helper functions.",
                })

        if isinstance(node, ast.ClassDef):
            if len(node.body) > LARGE_CLASS_THRESHOLD:
                findings.append({
                    "type": CODE_SMELL_TYPES["large_class"],
                    "severity": "Medium",
                    "line": node.lineno,
                    "message": f"Class '{node.name}' contains {len(node.body)} members.",
                    "recommendation": "Split the class into focused collaborators.",
                })

    return findings