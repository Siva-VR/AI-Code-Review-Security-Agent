import os
from pathlib import Path


APP_NAME = "AI Code Review Agent"
MAX_FILE_SIZE_BYTES = 1_000_000
SUPPORTED_EXTENSIONS = {".py": "python", ".python": "python", ".java": "java"}
SUPPORTED_LANGUAGES = {"python", "java"}
KNOWLEDGE_BASE_DIRECTORIES = ["doc", "knowledge_base/raw_documents"]
GROQ_MODEL = os.getenv("GROQ_MODEL", os.getenv("OPENAI_MODEL", "llama-3.3-70b-versatile")).strip()
OPENAI_MODEL = GROQ_MODEL


def load_env_file(project_root=None):
	project_root = Path(project_root or Path(__file__).resolve().parents[1])
	env_path = project_root / ".env"
	if not env_path.exists():
		return

	try:
		raw_bytes = env_path.read_bytes()
	except OSError:
		return

	for encoding in ("utf-8-sig", "utf-8", "utf-16", "utf-16-le", "utf-16-be"):
		try:
			text = raw_bytes.decode(encoding)
			break
		except UnicodeDecodeError:
			continue
	else:
		return

	for line in text.splitlines():
		line = line.strip()
		if not line or line.startswith("#") or "=" not in line:
			continue
		key, value = line.split("=", 1)
		key = key.strip()
		value = value.strip().strip('"').strip("'")
		if key:
			os.environ[key] = value