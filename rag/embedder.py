import re
from collections import Counter


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_']+")


def tokenize(text):
	return TOKEN_PATTERN.findall(text.lower())


class SimpleEmbedder:
	def embed(self, text):
		return Counter(tokenize(text))

	def embed_many(self, texts):
		return [self.embed(text) for text in texts]
