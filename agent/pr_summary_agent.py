import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from app.config import load_env_file
from agent.response_utils import extract_json_payload


class PRSummaryAgent:
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

	def _build_payload(self, review_result):
		return {
			"model": self.model,
			"temperature": 0.2,
			"response_format": {"type": "json_object"},
			"messages": [
				{
					"role": "system",
					"content": (
						"You are a senior engineering manager. Convert code review findings into a pull-request style summary. "
						"Return valid JSON with keys executive_overview, severity_breakdown, prioritized_fix_list, and merge_readiness. "
						"prioritized_fix_list should be ordered by severity and include finding_type, severity, impact, fix_priority, "
						"and suggested_action. Keep the response concise, specific, and actionable."
					),
				},
				{
					"role": "user",
					"content": json.dumps(review_result, indent=2),
				},
			],
		}

	def _parse_response(self, response_text):
		try:
			parsed = extract_json_payload(response_text)
		except ValueError:
			raw_content = (response_text or "").strip()
			parsed = {
				"executive_overview": raw_content or "Groq returned an empty or malformed response.",
				"severity_breakdown": {},
				"prioritized_fix_list": [],
				"merge_readiness": "unknown",
			}
		return {
			"executive_overview": parsed.get("executive_overview", ""),
			"severity_breakdown": parsed.get("severity_breakdown", {}),
			"prioritized_fix_list": parsed.get("prioritized_fix_list", []),
			"merge_readiness": parsed.get("merge_readiness", "unknown"),
			"model": self.model,
		}

	def summarize(self, review_result):
		if not self.is_enabled():
			return {
				"executive_overview": "Set GROQ_API_KEY to enable PR summary generation.",
				"severity_breakdown": review_result.get("summary", {}).get("severity_breakdown", {}),
				"prioritized_fix_list": [],
				"merge_readiness": "blocked",
				"model": self.model,
			}

		try:
			response = requests.post(
				f"{self.base_url}/chat/completions",
				headers={
					"Authorization": f"Bearer {self.api_key}",
					"Content-Type": "application/json",
				},
				json=self._build_payload(review_result),
				timeout=60,
			)
			response.raise_for_status()
		except requests.exceptions.HTTPError as error:
			status_code = getattr(getattr(error, "response", None), "status_code", None)
			if status_code == 429:
				return {
					"executive_overview": "PR summary generation was skipped because Groq rate limited the request.",
					"severity_breakdown": review_result.get("summary", {}).get("severity_breakdown", {}),
					"prioritized_fix_list": [],
					"merge_readiness": "unknown",
					"model": self.model,
				}
			raise
		except (requests.exceptions.RequestException, OSError, TimeoutError) as error:
			return {
				"executive_overview": "PR summary generation was skipped because the Groq API connection was interrupted.",
				"severity_breakdown": review_result.get("summary", {}).get("severity_breakdown", {}),
				"prioritized_fix_list": [],
				"merge_readiness": "unknown",
				"model": self.model,
				"error": str(error),
			}
		choices = response.json().get("choices", [])
		if not choices:
			raise ValueError("OpenAI PR summary response did not include any choices.")

		message = choices[0].get("message", {})
		content = message.get("content", "").strip()
		if not content:
			raise ValueError("OpenAI PR summary response did not include content.")

		return self._parse_response(content)