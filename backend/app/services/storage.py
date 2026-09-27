import os
from pathlib import Path

from dotenv import load_dotenv
from vercel.blob import BlobClient


# Load environment variables from the project root and backend.
APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BACKEND_DIR / ".env")


BLOB_READ_WRITE_TOKEN = os.getenv(
    "BLOB_READ_WRITE_TOKEN",
    ""
).strip()


def get_blob_client() -> BlobClient:
    """
    Create a Vercel Blob client.
    """
    if not BLOB_READ_WRITE_TOKEN:
        raise RuntimeError(
            "BLOB_READ_WRITE_TOKEN is not configured."
        )

    return BlobClient(
        token=BLOB_READ_WRITE_TOKEN
    )


def upload_pdf(
    file_path: str,
    blob_path: str
) -> dict:
    """
    Upload a PDF to private Vercel Blob storage.
    """
    with get_blob_client() as client:
        result = client.upload_file(
            file_path,
            blob_path,
            access="private",
            content_type="application/pdf"
        )

    return {
        "url": result.url,
        "pathname": result.pathname
    }


def delete_pdf(
    blob_url: str | None
) -> None:
    """
    Delete a PDF from Vercel Blob.
    """
    if not blob_url:
        return

    with get_blob_client() as client:
        client.delete([
            blob_url
        ])