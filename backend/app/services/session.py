import secrets

from fastapi import Request, Response


SESSION_COOKIE_NAME = "researchpilot_session"


def get_or_create_session_id(
    request: Request,
    response: Response
) -> str:
    """
    Get the browser's ResearchPilot session ID.

    If the browser does not have one, create a new
    cryptographically secure session ID and store it
    in an HttpOnly session cookie.
    """
    session_id = request.cookies.get(
        SESSION_COOKIE_NAME
    )

    if session_id:
        return session_id

    session_id = secrets.token_urlsafe(32)

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/"
    )

    return session_id