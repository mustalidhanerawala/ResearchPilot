from typing import Optional

from google import genai

try:
    from app.config import GEMINI_API_KEY
except ModuleNotFoundError:
    from backend.app.config import GEMINI_API_KEY


_client: Optional[genai.Client] = None

EMBEDDING_MODEL_NAME = "gemini-embedding-001"



def get_embedding_client() -> Optional[genai.Client]:
    """Create the Gemini client once and reuse it."""
    global _client

    if _client is not None:
        return _client

    if not GEMINI_API_KEY:
        return None

    _client = genai.Client(
        api_key=GEMINI_API_KEY
    )

    return _client


def generate_embeddings(
    texts: list[str]
) -> list[list[float]]:
    """
    Generate embeddings using Google's hosted
    Gemini Embedding model.
    """
    if not texts:
        return []

    client = get_embedding_client()

    if client is None:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    result = client.models.embed_content(
        model=EMBEDDING_MODEL_NAME,
        contents=texts
    )

    if not result.embeddings:
        return []

    return [
        embedding.values
        for embedding in result.embeddings
    ]