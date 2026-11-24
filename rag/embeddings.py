"""Embedding functions support for Acme Tech RAG."""
import hashlib
import numpy as np
from typing import List, Union
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from rag.config import settings

class DeterministicMockEmbeddingFunction(EmbeddingFunction[Documents]):
    """Fast deterministic mock embedding generator for testing and offline development."""
    def __init__(self, dim: int = 384):
        self.dim = dim

    def __call__(self, input: Documents) -> Embeddings:
        results: Embeddings = []
        for text in input:
            vec = np.zeros(self.dim, dtype=np.float32)
            # Tokenize words and hash into vector bins
            words = text.lower().replace("\n", " ").split()
            if not words:
                words = ["empty"]
            for word in words:
                h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
                idx = h % self.dim
                sign = 1.0 if (h // self.dim) % 2 == 0 else -1.0
                vec[idx] += sign
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            results.append(vec.tolist())
        return results

def get_embedding_function() -> EmbeddingFunction[Documents]:
    """Factory returning the configured embedding function."""
    provider = settings.EMBEDDING_PROVIDER.lower()

    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when EMBEDDING_PROVIDER is 'openai'")
        import chromadb.utils.embedding_functions as ef
        return ef.OpenAIEmbeddingFunction(
            api_key=settings.OPENAI_API_KEY,
            model_name=settings.OPENAI_EMBEDDING_MODEL
        )
    elif provider == "mock":
        return DeterministicMockEmbeddingFunction()
    else:
        # Default chromadb ONNX MiniLM
        try:
            import chromadb.utils.embedding_functions as ef
            return ef.DefaultEmbeddingFunction()
        except Exception:
            # Fallback to mock if ONNX or download fails
            return DeterministicMockEmbeddingFunction()
