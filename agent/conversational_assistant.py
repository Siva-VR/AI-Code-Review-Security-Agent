import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from app.config import KNOWLEDGE_BASE_DIRECTORIES, load_env_file
from agent.response_utils import extract_json_payload
from rag.loader import build_knowledge_base
from rag.query import query_knowledge_base


class ConversationalCodeAssistant:
	def __init__(self, api_key=None, model=None, base_url=None, knowledge_paths=None):
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
		self.knowledge_paths = knowledge_paths or KNOWLEDGE_BASE_DIRECTORIES
		self.knowledge_base = build_knowledge_base(self.knowledge_paths)

	def is_enabled(self):
		return bool(self.api_key)

	def _build_payload(self, question, review_result, retrieval_result):
		return {
			"model": self.model,
			"temperature": 0.2,
			"response_format": {"type": "json_object"},
			"messages": [
				{
					"role": "system",
					"content": (
						"You are a conversational code assistant. Answer only using the provided review context and knowledge "
						"base excerpts. If the context is insufficient, say so explicitly. Return valid JSON with keys answer, "
						"supporting_sources, and follow_up_guidance. Keep the response practical and grounded in secure coding best practices."
					),
				},
				{
					"role": "user",
					"content": json.dumps(
						{
							"question": question,
							"review_result": review_result,
							"retrieved_context": retrieval_result.get("context", ""),
							"sources": [match.get("source") for match in retrieval_result.get("matches", [])],
						},
						indent=2,
					),
				},
			],
		}

	def _parse_response(self, response_text, retrieval_result):
		try:
			parsed = extract_json_payload(response_text)
		except ValueError:
			raw_content = (response_text or "").strip()
			parsed = {
				"answer": raw_content or "Groq returned an empty or malformed response.",
				"supporting_sources": [],
				"follow_up_guidance": "Adjust the prompt or model output so it returns structured JSON.",
			}
		return {
			"answer": parsed.get("answer", ""),
			"supporting_sources": parsed.get("supporting_sources", []),
			"follow_up_guidance": parsed.get("follow_up_guidance", ""),
			"retrieved_sources": [match.get("source") for match in retrieval_result.get("matches", [])],
			"model": self.model,
		}

	def answer(self, question, review_result):
		retrieval_result = query_knowledge_base(self.knowledge_base["vector_store"], question, top_k=4)
		if not self.is_enabled():
			return {
				"answer": "Set GROQ_API_KEY to enable grounded follow-up answers.",
				"supporting_sources": [],
				"follow_up_guidance": "",
				"retrieved_sources": [match.get("source") for match in retrieval_result.get("matches", [])],
				"model": self.model,
			}

		try:
			response = requests.post(
				f"{self.base_url}/chat/completions",
				headers={
					"Authorization": f"Bearer {self.api_key}",
					"Content-Type": "application/json",
				},
				json=self._build_payload(question, review_result, retrieval_result),
				timeout=60,
			)
			response.raise_for_status()
		except requests.exceptions.HTTPError as error:
			status_code = getattr(getattr(error, "response", None), "status_code", None)
			if status_code == 429:
				return {
					"answer": "Groq rate limited the assistant request. Please try again in a moment.",
					"supporting_sources": [],
					"follow_up_guidance": "",
					"retrieved_sources": [match.get("source") for match in retrieval_result.get("matches", [])],
					"model": self.model,
				}
			raise
		except (requests.exceptions.RequestException, OSError, TimeoutError) as error:
			return {
				"answer": "The Groq assistant connection was interrupted before a response was returned.",
				"supporting_sources": [],
				"follow_up_guidance": "Please try again in a moment or verify the Groq endpoint connectivity.",
				"retrieved_sources": [match.get("source") for match in retrieval_result.get("matches", [])],
				"model": self.model,
				"error": str(error),
			}
		choices = response.json().get("choices", [])
		if not choices:
			raise ValueError("OpenAI assistant response did not include any choices.")

		message = choices[0].get("message", {})
		content = message.get("content", "").strip()
		if not content:
			raise ValueError("OpenAI assistant response did not include content.")

		return self._parse_response(content, retrieval_result)