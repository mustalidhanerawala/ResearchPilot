from pathlib import Path
import pymupdf


def extract_text_from_pdf(file_path: str) -> list[dict]:
    """
    Extract text from a PDF page by page.

    Returns:
        A list containing page number and extracted text.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found at: {file_path}")

    pages = []
    document = None

    try:
        document = pymupdf.open(str(path))

        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text").strip()
            pages.append({
                "page_number": page_number,
                "text": text
            })
    finally:
        if document is not None:
            document.close()

    return pages