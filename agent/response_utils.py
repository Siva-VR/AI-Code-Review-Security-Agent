import json

from agent.severity import summarize_findings


def extract_json_payload(response_text):
	content = (response_text or "").strip()
	if not content:
		raise ValueError("Groq response did not include content.")

	try:
		return json.loads(content)
	except json.JSONDecodeError:
		pass

	if content.startswith("```"):
		parts = content.split("\n")
		if len(parts) >= 3:
			candidate = "\n".join(parts[1:-1]).strip()
			if candidate:
				try:
					return json.loads(candidate)
				except json.JSONDecodeError:
					pass

	start = content.find("{")
		
	end = content.rfind("}")
	if start != -1 and end != -1 and end > start:
		candidate = content[start : end + 1]
		try:
			return json.loads(candidate)
		except json.JSONDecodeError:
			pass

	raise ValueError(f"Groq response did not contain valid JSON: {content[:120]}")


def normalize_finding(finding):
	if isinstance(finding, dict):
		return finding
	if finding is None:
		finding = ""
	return {
		"type": "Review Finding",
		"severity": "Low",
		"line": None,
		"message": str(finding),
		"recommendation": "Review the code and apply the safest minimal fix.",
	}


def normalize_findings(findings):
	if not isinstance(findings, list):
		return []
	return [normalize_finding(finding) for finding in findings]


def normalize_summary(summary, findings):
	if isinstance(summary, dict):
		return summary
	return summarize_findings(normalize_findings(findings))