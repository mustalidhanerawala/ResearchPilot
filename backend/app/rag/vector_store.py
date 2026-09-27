try:
    from app.config import (
        CHROMA_API_KEY,
        CHROMA_TENANT,
        CHROMA_DATABASE,
        CHROMA_COLLECTION_NAME
    )
except ModuleNotFoundError:
    from backend.app.config import (
        CHROMA_API_KEY,
        CHROMA_TENANT,
        CHROMA_DATABASE,
        CHROMA_COLLECTION_NAME
    )

import chromadb


if not CHROMA_API_KEY:
    raise RuntimeError(
        "CHROMA_API_KEY is not configured."
    )

if not CHROMA_TENANT:
    raise RuntimeError(
        "CHROMA_TENANT is not configured."
    )


client = chromadb.CloudClient(
    api_key=CHROMA_API_KEY,
    tenant=CHROMA_TENANT,
    database=CHROMA_DATABASE
)

collection = client.get_or_create_collection(
    name=CHROMA_COLLECTION_NAME
)


def get_session_records(
    session_id: str
) -> dict:
    """
    Get all Chroma records belonging to one session.
    """
    if not session_id:
        return {
            "ids": [],
            "documents": [],
            "metadatas": []
        }

    return collection.get(
        where={
            "session_id": session_id
        }
    )


def get_session_blob_urls(
    session_id: str
) -> list[str]:
    """
    Get unique Vercel Blob URLs belonging to one session.
    """
    records = get_session_records(
        session_id
    )

    blob_urls = set()

    for metadata in records.get(
        "metadatas",
        []
    ):
        if not metadata:
            continue

        blob_url = metadata.get(
            "blob_url"
        )

        if blob_url:
            blob_urls.add(
                blob_url
            )

    return list(blob_urls)


def clear_collection(
    session_id: str
) -> None:
    """
    Remove all chunks belonging to one browser session.
    """
    if not session_id:
        return

    records = get_session_records(
        session_id
    )

    ids = records.get(
        "ids",
        []
    )

    if ids:
        collection.delete(
            ids=ids
        )


def add_chunks(
    session_id: str,
    chunks: list[dict],
    embeddings: list[list[float]],
    blob_url: str | None = None
) -> None:
    """
    Store document chunks and embeddings for one session.
    """
    if not session_id:
        return

    if not chunks or not embeddings:
        return

    ids = []
    documents = []
    metadatas = []

    for index, chunk in enumerate(chunks):
        chunk_id = (
            f"{session_id}_"
            f"{chunk['document_name']}_"
            f"page_{chunk['page_number']}_"
            f"chunk_{index}"
        )

        ids.append(
            chunk_id
        )

        documents.append(
            chunk["text"]
        )

        metadata = {
            "session_id": session_id,
            "document_name": chunk["document_name"],
            "page_number": chunk["page_number"]
        }

        if blob_url:
            metadata["blob_url"] = blob_url

        metadatas.append(
            metadata
        )

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )


def search_chunks(
    session_id: str,
    query_embedding: list[float],
    top_k: int = 5
) -> dict:
    """
    Search only the document belonging to the current session.
    """
    if not session_id:
        return {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]]
        }

    if not query_embedding:
        return {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]]
        }

    # Get only records belonging to this session.
    session_records = collection.get(
        where={
            "session_id": session_id
        }
    )

    session_ids = session_records.get(
        "ids",
        []
    )

    total_docs = len(session_ids)

    if total_docs == 0:
        return {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]]
        }

    n_results = min(
        max(1, top_k),
        total_docs
    )

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where={
            "session_id": session_id
        }
    )

    return results