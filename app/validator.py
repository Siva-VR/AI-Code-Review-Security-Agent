import ast
from pathlib import Path

from app.config import MAX_FILE_SIZE_BYTES, SUPPORTED_EXTENSIONS


def detect_language(filename):
	suffix = Path(filename).suffix.lower()
	return SUPPORTED_EXTENSIONS.get(suffix)


def infer_language_from_code(code, filename=None):
	if filename:
		language = detect_language(filename)
		if language:
			return language

	try:
		ast.parse(code)
		return "python"
	except SyntaxError:
		pass

	java_markers = ["public class", "System.out.println", "String[] args", "import java.", ";"]
	python_markers = ["def ", "import ", "from ", "print(", "class "]

	java_score = sum(1 for marker in java_markers if marker in code)
	python_score = sum(1 for marker in python_markers if marker in code)

	if java_score > python_score:
		return "java"
	if python_score > 0:
		return "python"
	return None


def validate_python(code):
	try:
		ast.parse(code)
	except SyntaxError as error:
		return {
			"valid": False,
			"language": "python",
			"message": str(error),
		}

	return {
		"valid": True,
		"language": "python",
		"message": "Python syntax is valid.",
	}


def validate_java(code):
	if "class " not in code:
		return {
			"valid": False,
			"language": "java",
			"message": "Java source must contain a class declaration.",
		}

	brace_balance = 0
	for character in code:
		if character == "{":
			brace_balance += 1
		elif character == "}":
			brace_balance -= 1
			if brace_balance < 0:
				break

	if brace_balance != 0:
		return {
			"valid": False,
			"language": "java",
			"message": "Java braces are unbalanced.",
		}

	return {
		"valid": True,
		"language": "java",
		"message": "Java source passed structural validation.",
	}


def validate_submission(filename, code):
	if not filename:
		return {
			"valid": False,
			"language": None,
			"message": "A file name is required to detect the language.",
		}

	file_language = detect_language(filename)
	if file_language is None and Path(filename).suffix:
		return {
			"valid": False,
			"language": None,
			"message": "Unsupported file type. Use Python or Java source files.",
		}

	if len(code.encode("utf-8")) > MAX_FILE_SIZE_BYTES:
		return {
			"valid": False,
			"language": detect_language(filename),
			"message": "File exceeds the configured size limit.",
		}

	language = file_language or infer_language_from_code(code)
	if language == "python":
		return validate_python(code)
	if language == "java":
		return validate_java(code)

	return {
		"valid": False,
		"language": None,
		"message": "Unsupported file type. Use Python or Java source files.",
	}