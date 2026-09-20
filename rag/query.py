from rag.vector_store import InMemoryVectorStore


def query_knowledge_base(vector_store, question, top_k=3):
	if vector_store is None:
		vector_store = InMemoryVectorStore()

	matches = vector_store.similarity_search(question, top_k=top_k)
	return {
		"question": question,
		"matches": matches,
		"context": "\n\n".join(match["text"] for match in matches),
	}
