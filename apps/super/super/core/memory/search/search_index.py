from sentence_transformers import SentenceTransformer
import numpy as np
import faiss

class QueryEmbedder:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed(self, query: str) -> np.ndarray:
        return self.model.encode(query, normalize_embeddings=True)


class FAISSSearcher:
    """FAISS vector search (for both query cache and document embeddings)"""
    def __init__(self, dim: int):
        self.index = faiss.IndexFlatIP(dim)
        self.vectors = []
        self.documents = []

    def add_documents(self, embeddings, docs):
        self.index.add(np.array(embeddings).astype("float32"))
        self.vectors.extend(embeddings)
        self.documents.extend(docs)

    def search(self, query_vector, k=5):
        if len(self.vectors) == 0:
            return [], []
        D, I = self.index.search(np.array([query_vector]).astype("float32"), k)
        return [self.documents[i] for i in I[0]], D[0]