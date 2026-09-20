import math

from rag.embedder import SimpleEmbedder


def _cosine_similarity(left, right):
	if not left or not right:
		return 0.0

	shared_tokens = set(left) & set(right)
	numerator = sum(left[token] * right[token] for token in shared_tokens)
	left_norm = math.sqrt(sum(value * value for value in left.values()))
	right_norm = math.sqrt(sum(value * value for value in right.values()))
	if left_norm == 0 or right_norm == 0:
		return 0.0
	return numerator / (left_norm * right_norm)


class InMemoryVectorStore:
	def __init__(self, embedder=None):
		self.embedder = embedder or SimpleEmbedder()
		self.documents = []
		self.embeddings = []

	def add_documents(self, documents):
		for document in documents:
			self.documents.append(document)
			self.embeddings.append(self.embedder.embed(document["text"]))

	def similarity_search(self, query, top_k=4):
		query_embedding = self.embedder.embed(query)
		scored_documents = []
		for document, embedding in zip(self.documents, self.embeddings):
			score = _cosine_similarity(query_embedding, embedding)
			scored_documents.append((score, document))

		scored_documents.sort(key=lambda item: item[0], reverse=True)
		return [document for score, document in scored_documents[:top_k] if score > 0]
