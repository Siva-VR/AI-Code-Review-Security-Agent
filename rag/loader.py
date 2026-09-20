from pathlib import Path

from rag.splitter import split_documents
from rag.vector_store import InMemoryVectorStore


SUPPORTED_KB_EXTENSIONS = {".md", ".txt", ".rst"}


def load_documents(paths):
	documents = []
	for path in paths:
		base_path = Path(path)
		if base_path.is_dir():
			candidates = [candidate for candidate in base_path.rglob("*") if candidate.suffix.lower() in SUPPORTED_KB_EXTENSIONS]
		else:
			candidates = [base_path] if base_path.suffix.lower() in SUPPORTED_KB_EXTENSIONS else []

		for candidate in candidates:
			documents.append({
				"source": str(candidate),
				"text": candidate.read_text(encoding="utf-8", errors="ignore"),
			})
	return documents


def build_knowledge_base(paths, chunk_size=1000, overlap=150):
	documents = load_documents(paths)
	chunks = split_documents(documents, chunk_size=chunk_size, overlap=overlap)
	vector_store = InMemoryVectorStore()
	vector_store.add_documents(chunks)
	return {
		"documents": documents,
		"chunks": chunks,
		"vector_store": vector_store,
	}
