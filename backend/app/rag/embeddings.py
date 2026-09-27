from typing import Optional
from sentence_transformers import SentenceTransformer

try:
    from app.config import EMBEDDING_MODEL_NAME
except ModuleNotFoundError:
    from backend.app.config import EMBEDDING_MODEL_NAME

_model: Optional[SentenceTransformer] = None


def get_embedding_model() -> SentenceTransformer:
    """Lazy load embedding model to optimize startup time."""
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Convert a list of text strings into embedding vectors.
    """
    if not texts:
        return []

    model = get_embedding_model()
    embeddings = model.encode(
        texts,
        convert_to_numpy=True
    )

    return embeddings.tolist()