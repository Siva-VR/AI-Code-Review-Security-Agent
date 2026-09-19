from pathlib import Path

from app.validator import infer_language_from_code, validate_submission


def load_uploaded_file(uploaded_file):
	if uploaded_file is None:
		return None

	content = uploaded_file.read()
	if isinstance(content, bytes):
		content = content.decode("utf-8", errors="replace")

	return {
		"filename": uploaded_file.name,
		"language": infer_language_from_code(content, uploaded_file.name),
		"code": content,
		"validation": validate_submission(uploaded_file.name, content),
	}


def load_file_from_path(file_path):
	path = Path(file_path)
	content = path.read_text(encoding="utf-8")
	return {
		"filename": path.name,
		"language": infer_language_from_code(content, path.name),
		"code": content,
		"validation": validate_submission(path.name, content),
	}