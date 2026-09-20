import ast
import re


SQL_PATTERN = re.compile(r"\b(SELECT|INSERT|UPDATE|DELETE)\b.*[+{]", re.IGNORECASE)
PASSWORD_PATTERN = re.compile(r"(password|passwd|secret|token)\s*=\s*['\"].+['\"]", re.IGNORECASE)


def _build_finding(finding_type, severity, line, message, recommendation):
	return {
		"type": finding_type,
		"severity": severity,
		"line": line,
		"message": message,
		"recommendation": recommendation,
	}


def analyze_python(code):
	try:
		tree = ast.parse(code)
	except SyntaxError as error:
		return [
			_build_finding(
				"Syntax Error",
				"Critical",
				error.lineno or 1,
				str(error),
				"Fix the syntax error before running security or quality analysis.",
			)
		]

	findings = []

	for node in ast.walk(tree):
		if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
			if node.func.id == "eval":
				findings.append(_build_finding(
					"Dangerous eval()",
					"Critical",
					node.lineno,
					"eval() executes dynamically generated code.",
					"Replace eval() with explicit parsing or a safe dispatcher.",
				))
			if node.func.id == "exec":
				findings.append(_build_finding(
					"Dangerous exec()",
					"Critical",
					node.lineno,
					"exec() executes dynamically generated code.",
					"Remove exec() and use controlled program flow instead.",
				))

		if isinstance(node, ast.Assign):
			target_names = [target.id for target in node.targets if isinstance(target, ast.Name)]
			if target_names and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
				assignment = f"{target_names[0]} = {node.value.value!r}"
				if PASSWORD_PATTERN.search(assignment):
					findings.append(_build_finding(
						"Hardcoded Secret",
						"High",
						node.lineno,
						"Sensitive value appears to be hardcoded.",
						"Move secrets to environment variables or a secure secret store.",
					))

		if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
			method_name = node.func.attr.lower()
			if method_name in {"execute", "executemany", "query"}:
				for arg in node.args:
					if isinstance(arg, ast.JoinedStr) or isinstance(arg, ast.BinOp):
						findings.append(_build_finding(
							"SQL Injection",
							"Critical",
							node.lineno,
							"Database query is built from interpolated input.",
							"Use parameterized queries and bind user input separately.",
						))
						break

	for line_number, line in enumerate(code.splitlines(), start=1):
		if SQL_PATTERN.search(line):
			findings.append(_build_finding(
				"SQL Injection",
				"Critical",
				line_number,
				line.strip(),
				"Use parameterized queries instead of string concatenation.",
			))
		if PASSWORD_PATTERN.search(line):
			findings.append(_build_finding(
				"Hardcoded Secret",
				"High",
				line_number,
				line.strip(),
				"Move secrets to environment variables or a secret manager.",
			))

	return findings
