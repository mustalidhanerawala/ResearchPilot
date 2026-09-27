from pathlib import Path
import uuid

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    Request,
    Response
)

try:
    from app.config import UPLOAD_DIR
    from app.rag.pdf_processor import extract_text_from_pdf
    from app.rag.chunker import create_chunks
    from app.rag.embeddings import generate_embeddings
    from app.rag.vector_store import (
        add_chunks,
        clear_collection,
        collection,
        get_session_blob_urls
    )
    from app.services.session import get_or_create_session_id
    from app.services.storage import (
        upload_pdf,
        delete_pdf
    )
except ModuleNotFoundError:
    from backend.app.config import UPLOAD_DIR
    from backend.app.rag.pdf_processor import extract_text_from_pdf
    from backend.app.rag.chunker import create_chunks
    from backend.app.rag.embeddings import generate_embeddings
    from backend.app.rag.vector_store import (
        add_chunks,
        clear_collection,
        collection,
        get_session_blob_urls
    )
    from backend.app.services.session import get_or_create_session_id
    from backend.app.services.storage import (
        upload_pdf,
        delete_pdf
    )


router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


@router.post("/upload")
async def upload_document(
    request: Request,
    response: Response,
    file: UploadFile = File(...)
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )

    session_id = get_or_create_session_id(
        request,
        response
    )

    safe_filename = Path(file.filename).name

    temp_filename = (
        f".uploading_{uuid.uuid4().hex}_{safe_filename}"
    )

    temp_file_path = (
        UPLOAD_DIR / temp_filename
    )

    blob_path = (
        f"documents/{session_id}/"
        f"{uuid.uuid4().hex}_{safe_filename}"
    )

    new_blob_url = None

    try:
        # ---------------------------------------------------------
        # 1. Read the new PDF into a temporary local file
        # ---------------------------------------------------------
        contents = await file.read()

        with open(
            temp_file_path,
            "wb"
        ) as buffer:
            buffer.write(contents)

        # ---------------------------------------------------------
        # 2. Process the NEW PDF before touching current document
        # ---------------------------------------------------------
        pages = extract_text_from_pdf(
            str(temp_file_path)
        )

        chunks = create_chunks(
            pages=pages,
            document_name=safe_filename
        )

        if not chunks:
            temp_file_path.unlink(
                missing_ok=True
            )

            raise HTTPException(
                status_code=400,
                detail=(
                    "The uploaded PDF contains no extractable text. "
                    "The current document was kept."
                )
            )

        texts = [
            chunk["text"]
            for chunk in chunks
        ]

        embeddings = generate_embeddings(
            texts
        )

        if not embeddings:
            temp_file_path.unlink(
                missing_ok=True
            )

            raise HTTPException(
                status_code=400,
                detail=(
                    "Embeddings could not be generated for the new PDF. "
                    "The current document was kept."
                )
            )

        # ---------------------------------------------------------
        # 3. Upload NEW PDF to Vercel Blob
        # ---------------------------------------------------------
        blob_result = upload_pdf(
            file_path=str(temp_file_path),
            blob_path=blob_path
        )

        new_blob_url = blob_result["url"]

        # ---------------------------------------------------------
        # 4. Find previous Blob PDFs for THIS SESSION
        # ---------------------------------------------------------
        previous_blob_urls = get_session_blob_urls(
            session_id
        )

        # ---------------------------------------------------------
        # 5. Delete previous Blob PDFs
        # ---------------------------------------------------------
        for previous_blob_url in previous_blob_urls:
            if previous_blob_url != new_blob_url:
                try:
                    delete_pdf(
                        previous_blob_url
                    )
                except Exception:
                    pass

        # ---------------------------------------------------------
        # 6. Replace ONLY this session's Chroma records
        # ---------------------------------------------------------
        clear_collection(
            session_id
        )

        # ---------------------------------------------------------
        # 7. Store NEW document in Chroma
        # ---------------------------------------------------------
        add_chunks(
            session_id=session_id,
            chunks=chunks,
            embeddings=embeddings,
            blob_url=new_blob_url
        )

        # ---------------------------------------------------------
        # 8. Remove local temporary PDF
        # ---------------------------------------------------------
        temp_file_path.unlink(
            missing_ok=True
        )

        return {
            "message": "PDF uploaded and indexed successfully",
            "filename": safe_filename,
            "total_pages": len(pages),
            "total_chunks": len(chunks)
        }

    except HTTPException:
        raise

    except Exception as e:
        if temp_file_path.exists():
            temp_file_path.unlink(
                missing_ok=True
            )

        if new_blob_url:
            try:
                delete_pdf(
                    new_blob_url
                )
            except Exception:
                pass

        raise HTTPException(
            status_code=400,
            detail=f"Failed to process PDF: {str(e)}"
        )


@router.get("/status")
def get_documents_status(
    request: Request,
    response: Response
):
    session_id = get_or_create_session_id(
        request,
        response
    )

    count = 0
    active_doc = None

    try:
        session_records = collection.get(
            where={
                "session_id": session_id
            }
        )

        count = len(
            session_records.get(
                "ids",
                []
            )
        )

        metadatas = session_records.get(
            "metadatas",
            []
        )

        if metadatas:
            active_doc = metadatas[0].get(
                "document_name"
            )

    except Exception:
        pass

    return {
        "status": "ready",
        "active_document": active_doc,
        "total_chunks": count,
        "files": []
    }


@router.post("/session/cleanup")
def cleanup_session(
    request: Request
):
    """
    Delete all temporary document data belonging
    to the current browser session.

    This removes:
    - Session-specific Chroma vectors
    - Session-specific Vercel Blob PDFs
    """
    session_id = request.cookies.get(
        "researchpilot_session"
    )

    if not session_id:
        return {
            "message": "No active session found.",
            "cleaned": False
        }

    try:
        # ---------------------------------------------------------
        # 1. Find this session's Blob files
        # ---------------------------------------------------------
        blob_urls = get_session_blob_urls(
            session_id
        )

        # ---------------------------------------------------------
        # 2. Delete this session's Blob files
        # ---------------------------------------------------------
        for blob_url in blob_urls:
            try:
                delete_pdf(
                    blob_url
                )
            except Exception:
                pass

        # ---------------------------------------------------------
        # 3. Delete this session's Chroma vectors
        # ---------------------------------------------------------
        clear_collection(
            session_id
        )

        return {
            "message": "Session data cleaned up successfully.",
            "cleaned": True
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Session cleanup failed: {str(e)}"
        )