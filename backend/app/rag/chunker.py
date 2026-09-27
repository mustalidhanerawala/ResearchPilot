def create_chunks(
    pages: list[dict],
    document_name: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> list[dict]:
    """
    Split page text into overlapping chunks while preserving
    document name and original page number.
    Safeguards against infinite loops when chunk_overlap >= chunk_size.
    """
    chunks = []
    chunk_size = max(10, chunk_size)
    step = max(1, chunk_size - chunk_overlap)

    for page in pages:
        page_number = page.get("page_number", 1)
        text = page.get("text", "")

        if not text:
            continue

        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append({
                    "document_name": document_name,
                    "page_number": page_number,
                    "text": chunk_text
                })

            start += step

    return chunks