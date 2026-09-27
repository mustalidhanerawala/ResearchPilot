import os
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv


# Resolve project paths
# config.py is at <project_root>/backend/app/config.py
APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent


# Ensure backend directory and project root are in sys.path
for path in (BACKEND_DIR, PROJECT_ROOT):
    path_str = str(path)

    if path_str not in sys.path:
        sys.path.insert(0, path_str)


# Load environment variables
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BACKEND_DIR / ".env")


# Temporary local storage
#
# Locally:
#   Uses the operating system temporary directory.
#
# On Vercel:
#   Uses /tmp, which is the writable temporary filesystem.
#
TEMP_DIR = Path(
    tempfile.gettempdir()
) / "researchpilot"

UPLOAD_DIR = TEMP_DIR / "uploads"

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# Configuration values
GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
    ""
).strip()

GEMINI_MODEL_NAME = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.1-flash-lite"
)

EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL",
    "all-MiniLM-L6-v2"
)

CHROMA_COLLECTION_NAME = (
    "researchpilot_gemini_documents"
)


# Chroma Cloud
CHROMA_API_KEY = os.getenv(
    "CHROMA_API_KEY",
    ""
).strip()

CHROMA_TENANT = os.getenv(
    "CHROMA_TENANT",
    ""
).strip()

CHROMA_DATABASE = os.getenv(
    "CHROMA_DATABASE",
    "researchpilot"
).strip()