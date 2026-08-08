"""FastAPI application — single POST /api/interview endpoint.

Loads curriculum data at startup, routes requests to the interview logic.
"""

import json
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.analyzer import analyze_candidate
from app.interviewer import generate_first_question, handle_turn
from app.models import CurriculumDay, InterviewRequest, InterviewResponse, InterviewSession
from app.planner import build_interview_plan
from app.session import create_session, get_session

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI Interview Agent",
    description="Personalized technical interviewer for the ABTalks hackathon",
    version="1.0.0",
)

# CORS — allow the React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Curriculum data — loaded once at startup
# ---------------------------------------------------------------------------

_curriculum_days: dict[int, CurriculumDay] = {}


def _load_curriculum() -> dict[int, CurriculumDay]:
    """Load and parse curriculum.json into a lookup table."""
    data_dir = Path(__file__).parent.parent / "data"
    curriculum_path = data_dir / "curriculum.json"

    if not curriculum_path.exists():
        logger.error("curriculum.json not found at %s", curriculum_path)
        raise FileNotFoundError(f"curriculum.json not found at {curriculum_path}")

    with open(curriculum_path, "r") as f:
        data = json.load(f)

    # Build module lookup: day_number -> (module_number, module_title)
    module_lookup: dict[int, tuple[int, str]] = {}
    for mod in data.get("modules", []):
        mod_num = mod["n"]
        mod_title = mod["title"]
        start, end = mod["days"]
        for d in range(start, end + 1):
            module_lookup[d] = (mod_num, mod_title)

    # Parse days
    days: dict[int, CurriculumDay] = {}
    for day_data in data.get("days", []):
        day_num = day_data["day"]
        mod_num, mod_title = module_lookup.get(day_num, (0, "Unknown"))
        days[day_num] = CurriculumDay(
            day=day_num,
            title=day_data["title"],
            type=day_data.get("type", "BUILD"),
            tools=day_data.get("tools", []),
            objectives=day_data.get("objectives", []),
            module_number=mod_num,
            module_title=mod_title,
        )

    logger.info("Loaded %d curriculum days across %d modules", len(days), len(data.get("modules", [])))
    return days


@app.on_event("startup")
async def startup():
    """Load curriculum data on server startup."""
    global _curriculum_days
    _curriculum_days = _load_curriculum()


# ---------------------------------------------------------------------------
# Candidate data endpoint — serves candidates.json for the frontend
# ---------------------------------------------------------------------------

@app.get("/api/candidates")
async def get_candidates():
    """Return the candidates list for the frontend picker."""
    data_dir = Path(__file__).parent.parent / "data"
    candidates_path = data_dir / "candidates.json"

    if not candidates_path.exists():
        raise HTTPException(404, "candidates.json not found")

    with open(candidates_path, "r") as f:
        data = json.load(f)

    return data


# ---------------------------------------------------------------------------
# Main interview endpoint
# ---------------------------------------------------------------------------

@app.post("/api/interview", response_model=InterviewResponse)
async def interview(request: InterviewRequest):
    """Handle all interview interactions through a single endpoint.

    - First request (with candidate): Initialize session, return welcome + Q1
    - Subsequent requests (with message): Evaluate answer, return next Q
    - Final request: Return feedback when interview is complete
    """
    if request.candidate is not None:
        # === START: New interview session ===

        # Check for duplicate session
        existing = get_session(request.sessionId)
        if existing is not None:
            raise HTTPException(
                409, f"Session '{request.sessionId}' already exists"
            )

        # Analyze candidate and build plan
        profile = analyze_candidate(request.candidate, _curriculum_days)
        plan = build_interview_plan(profile, _curriculum_days)

        # Create session
        session = InterviewSession(
            session_id=request.sessionId,
            candidate=request.candidate,
            profile=profile,
            plan=plan,
            follow_up_budget=config.FOLLOW_UP_BUDGET,
        )
        create_session(session)

        # Generate welcome + first question
        response = await generate_first_question(session, _curriculum_days)
        return response

    elif request.message is not None:
        # === TURN: Continue existing interview ===

        session = get_session(request.sessionId)
        if session is None:
            raise HTTPException(
                404, f"Session '{request.sessionId}' not found"
            )
        if session.status == "completed":
            raise HTTPException(
                400, f"Session '{request.sessionId}' is already completed"
            )

        response = await handle_turn(session, request.message, _curriculum_days)
        return response

    else:
        raise HTTPException(
            400, "Request must contain either 'candidate' (to start) or 'message' (to continue)"
        )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "curriculum_loaded": len(_curriculum_days) > 0}
