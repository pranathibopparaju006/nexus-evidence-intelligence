from typing import List
from sentence_transformers import SentenceTransformer

_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model


async def get_embedding(text: str) -> List[float]:
    model = get_model()
    embedding = model.encode(text, convert_to_list=True)
    return embedding


async def get_embeddings(texts: List[str]) -> List[List[float]]:
    model = get_model()
    embeddings = model.encode(texts, convert_to_list=True)
    return embeddings


def cosine_similarity(embedding_a: List[float], embedding_b: List[float]) -> float:
    import numpy as np
    
    a = np.array(embedding_a)
    b = np.array(embedding_b)
    
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
