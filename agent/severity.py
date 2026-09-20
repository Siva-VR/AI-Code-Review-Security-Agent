SEVERITY_ORDER = ["Low", "Medium", "High", "Critical"]

SEVERITY_WEIGHTS = {
	"Low": 1,
	"Medium": 2,
	"High": 3,
	"Critical": 4,
}


def normalize_severity(severity):
	if not severity:
		return "Low"

	value = str(severity).strip().lower()
	if value == "critical":
		return "Critical"
	if value == "high":
		return "High"
	if value == "medium":
		return "Medium"
	return "Low"


def severity_score(findings):
	total = 0
	for finding in findings:
		total += SEVERITY_WEIGHTS.get(normalize_severity(finding.get("severity")), 1)
	return total


def score_finding(finding):
	return SEVERITY_WEIGHTS.get(normalize_severity(finding.get("severity")), 1)


def annotate_findings(findings):
	annotated = []
	for finding in findings:
		annotated_finding = dict(finding)
		annotated_finding["severity_score"] = score_finding(annotated_finding)
		annotated_finding["severity_label"] = normalize_severity(annotated_finding.get("severity"))
		annotated.append(annotated_finding)
	return annotated


def severity_breakdown(findings):
	breakdown = {level: 0 for level in SEVERITY_ORDER}
	for finding in findings:
		level = normalize_severity(finding.get("severity"))
		breakdown[level] += 1
	return breakdown


def summarize_findings(findings):
	breakdown = severity_breakdown(findings)
	return {
		"total_findings": len(findings),
		"severity_breakdown": breakdown,
		"risk_score": severity_score(findings),
	}
