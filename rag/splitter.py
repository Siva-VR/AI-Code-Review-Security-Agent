def split_text(text, chunk_size=1000, overlap=150):
	if not text:
		return []

	chunks = []
	start = 0
	text_length = len(text)

	while start < text_length:
		end = min(start + chunk_size, text_length)
		chunk = text[start:end].strip()
		if chunk:
			chunks.append(chunk)
		if end >= text_length:
			break
		start = max(end - overlap, start + 1)

	return chunks


def split_documents(documents, chunk_size=1000, overlap=150):
	chunks = []
	for document in documents:
		for index, chunk in enumerate(split_text(document["text"], chunk_size=chunk_size, overlap=overlap)):
			chunks.append({
				"id": f"{document['source']}::{index}",
				"source": document["source"],
				"text": chunk,
			})
	return chunks
