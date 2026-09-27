try:
    from app.rag.embeddings import generate_embeddings
    from app.rag.vector_store import search_chunks
except ModuleNotFoundError:
    from backend.app.rag.embeddings import generate_embeddings
    from backend.app.rag.vector_store import search_chunks


def retrieve_relevant_chunks(
    session_id: str,
    query: str,
    top_k: int = 5
) -> list[dict]:
    """
    Retrieve the most relevant document chunks
    belonging only to the current browser session.
    """
    if not session_id:
        return []

    if not query or not query.strip():
        return []

    embeddings = generate_embeddings(
        [query]
    )

    if not embeddings:
        return []

    query_embedding = embeddings[0]

    results = search_chunks(
        session_id=session_id,
        query_embedding=query_embedding,
        top_k=top_k
    )

    retrieved_chunks = []

    documents_list = results.get(
        "documents",
        [[]]
    )

    metadatas_list = results.get(
        "metadatas",
        [[]]
    )

    documents = (
        documents_list[0]
        if documents_list
        else []
    )

    metadatas = (
        metadatas_list[0]
        if metadatas_list
        else []
    )

    for document, metadata in zip(
        documents,
        metadatas
    ):
        metadata_dict = metadata or {}

        retrieved_chunks.append({
            "text": document,
            "document_name": metadata_dict.get(
                "document_name",
                "Unknown"
            ),
            "page_number": metadata_dict.get(
                "page_number",
                1
            )
        })

    return retrieved_chunks