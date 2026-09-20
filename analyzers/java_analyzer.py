import re

from agent.severity import annotate_findings


METHOD_PATTERN = re.compile(r"\b(public|private|protected)\b[^\(]*\(([^\)]*)\)\s*\{")
SQL_PATTERN = re.compile(r"\b(SELECT|INSERT|UPDATE|DELETE)\b.*\+", re.IGNORECASE)
SECRET_PATTERN = re.compile(r"(password|passwd|secret|api_key|token)\s*=\s*\".*\"", re.IGNORECASE)
CONTROL_FLOW_PATTERN = re.compile(r"\b(if|for|while|switch|try|catch)\b")
MAX_ARGUMENTS_THRESHOLD = 5
LONG_METHOD_THRESHOLD = 20
LARGE_CLASS_THRESHOLD = 15
MAX_NESTING_THRESHOLD = 4


def _finding(finding_type, severity, line, message, recommendation):
	return {
		"type": finding_type,
		"severity": severity,
		"line": line,
		"message": message,
		"recommendation": recommendation,
	}


def _method_length_and_nesting(lines, start_index):
	brace_depth = 0
	length = 0
	control_flow_depth = 0

	for index in range(start_index, len(lines)):
		current_line = lines[index]
		length += 1
		brace_depth += current_line.count("{") - current_line.count("}")
		if CONTROL_FLOW_PATTERN.search(current_line):
			control_flow_depth += 1
		if index > start_index and brace_depth <= 0:
			break

	return length, control_flow_depth


def analyze_java(code):
	lines = code.splitlines()
	findings = []
	method_count = 0

	for line_number, line in enumerate(lines, start=1):
		stripped = line.strip()
		method_match = METHOD_PATTERN.search(line)
		if method_match:
			method_count += 1
			parameters = [parameter.strip() for parameter in method_match.group(2).split(",") if parameter.strip()]
			if len(parameters) > MAX_ARGUMENTS_THRESHOLD:
				findings.append(_finding(
					"Long Parameter List",
					"Medium",
					line_number,
					f"Method has {len(parameters)} parameters.",
					"Reduce parameter count by grouping related inputs into a value object.",
				))

			method_length, nesting_hits = _method_length_and_nesting(lines, line_number - 1)
			if method_length > LONG_METHOD_THRESHOLD:
				findings.append(_finding(
					"Long Method",
					"Medium",
					line_number,
					f"Method spans {method_length} lines.",
					"Split the method into smaller helpers with a single responsibility.",
				))
			if nesting_hits > MAX_NESTING_THRESHOLD:
				findings.append(_finding(
					"Deep Nesting",
					"Medium",
					line_number,
					f"Method contains {nesting_hits} nested control-flow statements.",
					"Flatten the control flow using guard clauses or extracted methods.",
				))

		if SQL_PATTERN.search(line):
			findings.append(_finding(
				"SQL Injection",
				"Critical",
				line_number,
				stripped,
				"Use prepared statements and parameter binding.",
			))

		if SECRET_PATTERN.search(line):
			findings.append(_finding(
				"Hardcoded Secret",
				"High",
				line_number,
				stripped,
				"Load secrets from environment variables or a secure vault.",
			))

		if "Runtime.getRuntime().exec" in line or "ProcessBuilder" in line:
			findings.append(_finding(
				"Command Injection",
				"Critical",
				line_number,
				stripped,
				"Avoid shell execution with user-controlled input.",
			))

	if method_count > LARGE_CLASS_THRESHOLD:
		findings.append(_finding(
			"Large Class",
			"Medium",
			1,
			f"Class declares {method_count} methods.",
			"Split the class into smaller cohesive components.",
		))

	return annotate_findings(findings)
