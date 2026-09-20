import json
from pathlib import Path
from datetime import datetime, timezone

from agent.code_analysis_agent import CodeAnalysisAgent
from agent.conversational_assistant import ConversationalCodeAssistant
from agent.openai_review_agent import OpenAIReviewAgent
from agent.pr_summary_agent import PRSummaryAgent
from agent.remediation_agent import RemediationAgent
from agent.report_exporter import export_review_pdf
from agent.security_agent import SecurityAgent
from agent.severity import summarize_findings


class ReviewOrchestrator:
	def __init__(self, reports_dir=None):
		self.code_analysis_agent = CodeAnalysisAgent()
		self.security_agent = SecurityAgent()
		self.openai_review_agent = OpenAIReviewAgent()
		self.remediation_agent = RemediationAgent()
		self.pr_summary_agent = PRSummaryAgent()
		self.conversational_assistant = ConversationalCodeAssistant()
		self.reports_dir = Path(reports_dir) if reports_dir else Path(__file__).resolve().parents[1] / "reports"

	def _build_error_result(self, message):
		findings = [
			{
				"type": "Groq Review Error",
				"severity": "Critical",
				"line": None,
				"message": message,
				"recommendation": "Set a valid GROQ_API_KEY and verify Groq API connectivity.",
				"severity_score": 4,
				"severity_label": "Critical",
			}
		]
		return {
			"findings": findings,
			"summary": summarize_findings(findings),
			"review_mode": "groq_only",
			"model": self.openai_review_agent.model,
		}

	def _write_review_report(self, code, language, result):
		self.reports_dir.mkdir(parents=True, exist_ok=True)
		timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
		report_path = self.reports_dir / f"review_report_{timestamp}.json"
		report_payload = {
			"language": language,
			"review_mode": result.get("review_mode", "local"),
			"model": result.get("model"),
			"summary": result.get("summary", {}),
			"findings": result.get("findings", []),
			"severity_breakdown": result.get("summary", {}).get("severity_breakdown", {}),
			"risk_score": result.get("summary", {}).get("risk_score"),
			"total_findings": result.get("summary", {}).get("total_findings"),
			"code": code,
		}
		report_path.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")
		return str(report_path)

	def _write_review_pdf(self, code, language, result):
		self.reports_dir.mkdir(parents=True, exist_ok=True)
		timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
		pdf_path = self.reports_dir / f"review_report_{timestamp}.pdf"
		return export_review_pdf(code, language, result, pdf_path)

	def _attach_remediations(self, code, language, result):
		findings = result.get("findings", [])
		for finding in findings:
			try:
				finding["remediation_details"] = self.remediation_agent.suggest(code, language, finding)
			except Exception as error:
				finding["remediation_details"] = {
					"remediation": "Remediation generation was skipped due to a Groq API error.",
					"corrected_code_example": "",
					"best_practice_explanation": f"Groq API error: {error}",
					"model": self.remediation_agent.model,
				}
		return result

	def _attach_pr_summary(self, result):
		try:
			result["pr_summary"] = self.pr_summary_agent.summarize(result)
		except Exception as error:
			result["pr_summary"] = {
				"executive_overview": "PR summary generation was skipped due to a Groq API error.",
				"severity_breakdown": result.get("summary", {}).get("severity_breakdown", {}),
				"prioritized_fix_list": [],
				"merge_readiness": "unknown",
				"model": self.pr_summary_agent.model,
				"error": str(error),
			}
		return result

	def _merge_findings(self, *finding_groups):
		merged = []
		seen = set()
		for group in finding_groups:
			if not isinstance(group, list):
				continue
			for finding in group:
				if not isinstance(finding, dict):
					continue
				key = (
					str(finding.get("type", "")),
					str(finding.get("line", "")),
					str(finding.get("message", "")),
				)
				if key in seen:
					continue
				seen.add(key)
				merged.append(dict(finding))
		return merged

	def answer_follow_up(self, question, review_result):
		return self.conversational_assistant.answer(question, review_result)

	def analyze(self, code, language="python"):
		normalized_language = (language or "python").lower()
		if not self.openai_review_agent.is_enabled():
			result = self._build_error_result("GROQ_API_KEY is not configured. Groq-backed review cannot run.")
			result["report_path"] = self._write_review_report(code, normalized_language, result)
			return result

		local_code_findings = self.code_analysis_agent.analyze(code, normalized_language)
		local_security_findings = self.security_agent.analyze(code, normalized_language)
		if not isinstance(local_code_findings, list):
			local_code_findings = []
		if not isinstance(local_security_findings, list):
			local_security_findings = []

		try:
			result = self.openai_review_agent.analyze(code, normalized_language) or self._build_error_result(
				"Groq returned an empty review response."
			)
		except Exception as error:
			result = self._build_error_result(f"Groq review request failed: {error}")

		if result.get("rate_limited"):
			result = self._build_error_result(result.get("error", "Groq rate limit reached. Please wait and try again."))
			result["rate_limited"] = True
			result["report_path"] = self._write_review_report(code, normalized_language, result)
			return result

		merged_findings = self._merge_findings(local_code_findings, local_security_findings, result.get("findings", []))
		result["findings"] = merged_findings
		result["summary"] = summarize_findings(merged_findings)
		if local_code_findings or local_security_findings:
			result["review_mode"] = "hybrid"
		else:
			result["review_mode"] = result.get("review_mode", "openai")
		result["model"] = self.openai_review_agent.model

		result = self._attach_remediations(code, normalized_language, result)
		result = self._attach_pr_summary(result)
		result["report_path"] = self._write_review_report(code, normalized_language, result)
		result["pdf_report_path"] = self._write_review_pdf(code, normalized_language, result)
		return result
