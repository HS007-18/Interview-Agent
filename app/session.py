"""In-memory session store keyed by sessionId."""

from app.models import InterviewSession

# Global session store — simple dict, no persistence needed for hackathon
_sessions: dict[str, InterviewSession] = {}


def create_session(session: InterviewSession) -> None:
    """Store a new interview session."""
    _sessions[session.session_id] = session


def get_session(session_id: str) -> InterviewSession | None:
    """Retrieve an existing session by ID. Returns None if not found."""
    return _sessions.get(session_id)


def delete_session(session_id: str) -> None:
    """Remove a session (e.g., after completion)."""
    _sessions.pop(session_id, None)


def list_sessions() -> list[str]:
    """Return all active session IDs (useful for debugging)."""
    return list(_sessions.keys())
