from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

try:
    from app.services.research import answer_question
    from app.services.session import get_or_create_session_id
except ModuleNotFoundError:
    from backend.app.services.research import answer_question
    from backend.app.services.session import get_or_create_session_id


router = APIRouter(
    prefix="/research",
    tags=["Research"]
)


class ResearchRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        description="Question to ask ResearchPilot"
    )

    top_k: int = Field(
        5,
        ge=1,
        le=20,
        description="Number of document chunks to retrieve"
    )


@router.post("/ask")
def ask_question(
    request: Request,
    response: Response,
    research_request: ResearchRequest
):
    if not research_request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    # ---------------------------------------------------------
    # Get or create the browser session
    # ---------------------------------------------------------
    session_id = get_or_create_session_id(
        request,
        response
    )

    result = answer_question(
        session_id=session_id,
        question=research_request.question.strip(),
        top_k=research_request.top_k
    )

    return result