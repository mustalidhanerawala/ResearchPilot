try:
    from app.rag.retriever import retrieve_relevant_chunks
    from app.services.llm import generate_answer
except ModuleNotFoundError:
    from backend.app.rag.retriever import retrieve_relevant_chunks
    from backend.app.services.llm import generate_answer


def answer_question(
    session_id: str,
    question: str,
    top_k: int = 5
) -> dict:
    """
    Retrieve evidence and generate a structured research response
    for the current browser session.
    """
    retrieved_chunks = retrieve_relevant_chunks(
        session_id=session_id,
        query=question,
        top_k=top_k
    )

    answer = generate_answer(
        question,
        retrieved_chunks
    )

    main_source = (
        retrieved_chunks[0]
        if retrieved_chunks
        else None
    )

    related_content = (
        retrieved_chunks[1:]
        if len(retrieved_chunks) > 1
        else []
    )

    return {
        "question": question,
        "answer": answer,
        "main_source": main_source,
        "related_content": related_content,
        "sources": retrieved_chunks
    }