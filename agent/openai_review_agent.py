import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from agent.severity import annotate_findings, summarize_findings
from app.config import load_env_file
from agent.response_utils import extract_json_payload, normalize_findings, normalize_summary


class OpenAIReviewAgent:
	def __init__(self, api_key=None, model=None, base_url=None):
		project_root = Path(__file__).resolve().parents[1]
		try:
			load_dotenv(project_root / ".env", override=False)
		except Exception:
			pass
		load_env_file(project_root)
		self.api_key = (api_key or os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY", "")).strip()
		self.model = (model or os.getenv("GROQ_MODEL") or os.getenv("OPENAI_MODEL") or "llama-3.3-70b-versatile").strip()
		self.base_url = (
			base_url
			or os.getenv("GROQ_BASE_URL")
			or os.getenv("OPENAI_BASE_URL")
			or "https://api.groq.com/openai/v1"
		).rstrip("/")

	def _refresh_environment(self):
		project_root = Path(__file__).resolve().parents[1]
		load_env_file(project_root)
		if not self.api_key:
			self.api_key = (os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY", "")).strip()
		if not self.model:
			self.model = (os.getenv("GROQ_MODEL") or os.getenv("OPENAI_MODEL") or "llama-3.3-70b-versatile").strip()
		if not self.base_url:
			self.base_url = (
				os.getenv("GROQ_BASE_URL")
				or os.getenv("OPENAI_BASE_URL")
				or "https://api.groq.com/openai/v1"
			).rstrip("/")

	def is_enabled(self):
		self._refresh_environment()
		return bool(self.api_key)

	def _build_payload(self, code, language):
		return {
			"model": self.model,
			"temperature": 0.2,
			"response_format": {"type": "json_object"},
			"messages": [
				{
					"role": "system",
					"content": (
						"You are a senior code review assistant. Review the submission for correctness, security, "
						"maintainability, and code quality. Return valid JSON with keys findings and summary. "
						"Each finding must include type, severity, line, message, and recommendation. "
						"Use severity values Low, Medium, High, or Critical."
					),
				},
				{
					"role": "user",
					"content": f"Language: {language or 'unknown'}\n\nReview this code:\n\n{code}",
				},
			],
		}

	def _parse_response(self, response_text):
		try:
			payload = extract_json_payload(response_text)
		except ValueError:
			raw_content = (response_text or "").strip()
			payload = {
				"findings": [
					{
						"type": "Groq Output",
						"severity": "Low",
						"line": None,
						"message": raw_content or "Groq returned an empty or malformed response.",
						"recommendation": "Adjust the prompt or model output so it returns structured JSON.",
					}
				],
				"summary": {
					"total_findings": 1,
					"severity_breakdown": {"Low": 1, "Medium": 0, "High": 0, "Critical": 0},
					"risk_score": 1,
				},
			}
		findings = normalize_findings(payload.get("findings", []))
		summary = normalize_summary(payload.get("summary"), findings)
		return {
			"findings": annotate_findings(findings),
			"summary": summary,
			"review_mode": "openai",
			"model": self.model,
		}

	def analyze(self, code, language="python"):
		if not self.is_enabled():
			return None

		try:
			response = requests.post(
				f"{self.base_url}/chat/completions",
				headers={
					"Authorization": f"Bearer {self.api_key}",
					"Content-Type": "application/json",
				},
				json=self._build_payload(code, language),
				timeout=60,
			)
			response.raise_for_status()
		except requests.exceptions.HTTPError as error:
			status_code = getattr(getattr(error, "response", None), "status_code", None)
			if status_code == 429:
				return {
					"findings": [],
					"summary": summarize_findings([]),
					"review_mode": "groq_rate_limited",
					"model": self.model,
					"rate_limited": True,
					"error": "Groq rate limit reached. Please wait and try again.",
				}
			raise
		except (requests.exceptions.RequestException, OSError, TimeoutError) as error:
			return {
				"findings": [],
				"summary": summarize_findings([]),
				"review_mode": "groq_connection_error",
				"model": self.model,
				"error": f"Groq review request failed: {error}",
			}
		choices = response.json().get("choices", [])
		if not choices:
			raise ValueError("OpenAI response did not include any choices.")

		message = choices[0].get("message", {})
		content = message.get("content", "").strip()
		if not content:
			raise ValueError("OpenAI response did not include review content.")

		return self._parse_response(content)