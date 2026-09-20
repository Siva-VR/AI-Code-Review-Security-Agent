import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from app.config import load_env_file
from agent.response_utils import extract_json_payload


class RemediationAgent:
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

	def is_enabled(self):
		return bool(self.api_key)

	def _build_payload(self, code, language, finding):
		return {
			"model": self.model,
			"temperature": 0.2,
			"response_format": {"type": "json_object"},
			"messages": [
				{
					"role": "system",
					"content": (
						"You are a senior remediation assistant. For a single code review finding, return valid JSON with "
						"keys remediation, corrected_code_example, and best_practice_explanation. remediation should be a "
						"short, specific fix instruction. corrected_code_example should show a concrete replacement or snippet. "
						"best_practice_explanation should explain why the change is safer or better. Keep the answer concise "
						"and directly tied to the finding."
					),
				},
				{
					"role": "user",
					"content": (
						f"Language: {language or 'unknown'}\n"
						f"Finding type: {finding.get('type', 'Unknown')}\n"
						f"Severity: {finding.get('severity', 'Unknown')}\n"
						f"Line: {finding.get('line', 'unknown')}\n"
						f"Message: {finding.get('message', '')}\n"
						f"Recommendation: {finding.get('recommendation', '')}\n\n"
						f"Source code:\n{code}"
					),
				},
			],
		}

	def _parse_response(self, response_text):
		try:
			payload = extract_json_payload(response_text)
		except ValueError:
			raw_content = (response_text or "").strip()
			payload = {
				"remediation": raw_content or "Groq returned an empty or malformed response.",
				"corrected_code_example": "",
				"best_practice_explanation": "Adjust the prompt or model output so it returns structured JSON.",
			}
		return {
			"remediation": payload.get("remediation", "Review the issue and apply the safest minimal fix."),
			"corrected_code_example": payload.get("corrected_code_example", ""),
			"best_practice_explanation": payload.get("best_practice_explanation", ""),
			"model": self.model,
		}

	def suggest(self, code, language, finding):
		if not self.is_enabled():
			return {
				"remediation": "Set GROQ_API_KEY to enable remediation generation.",
				"corrected_code_example": "",
				"best_practice_explanation": "",
				"model": self.model,
			}

		try:
			response = requests.post(
				f"{self.base_url}/chat/completions",
				headers={
					"Authorization": f"Bearer {self.api_key}",
					"Content-Type": "application/json",
				},
				json=self._build_payload(code, language, finding),
				timeout=60,
			)
			response.raise_for_status()
		except requests.exceptions.HTTPError as error:
			status_code = getattr(getattr(error, "response", None), "status_code", None)
			if status_code == 429:
				return {
					"remediation": "Remediation generation was skipped because Groq rate limited the request.",
					"corrected_code_example": "",
					"best_practice_explanation": "Try again after the rate limit window resets.",
					"model": self.model,
				}
			raise
		except (requests.exceptions.RequestException, OSError, TimeoutError) as error:
			return {
				"remediation": "Remediation generation was skipped because the Groq API connection was interrupted.",
				"corrected_code_example": "",
				"best_practice_explanation": f"The upstream API closed the connection unexpectedly: {error}",
				"model": self.model,
				"error": str(error),
			}
		choices = response.json().get("choices", [])
		if not choices:
			raise ValueError("OpenAI remediation response did not include any choices.")

		message = choices[0].get("message", {})
		content = message.get("content", "").strip()
		if not content:
			raise ValueError("OpenAI remediation response did not include content.")

		return self._parse_response(content)