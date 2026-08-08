"""Pydantic schemas and dataclasses used across the application."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# API Request / Response schemas (Pydantic — used by FastAPI)
# ---------------------------------------------------------------------------

class InterviewRequest(BaseModel):
    """Incoming POST /api/interview body."""
    sessionId: str
    candidate: dict[str, Any] | None = None
    message: str | None = None


class Feedback(BaseModel):
    """Structured feedback returned when the interview ends."""
    summary: str
    strengths: list[str]
    gaps: list[str]
    next: list[str]


class InterviewResponse(BaseModel):
    """Outgoing response from POST /api/interview."""
    reply: str
    done: bool
    feedback: Feedback | None = None


# ---------------------------------------------------------------------------
# Internal data structures (dataclasses — not exposed via API)
# ---------------------------------------------------------------------------

@dataclass
class CurriculumDay:
    """A single day from curriculum.json, enriched with its module info."""
    day: int
    title: str
    type: str
    tools: list[str]
    objectives: list[str]
    module_number: int
    module_title: str


@dataclass
class MissionRecord:
    """A single mission entry from the candidate's missions array."""
    day: int
    title: str
    passed: bool | None = None       # None if skipped
    skipped: bool = False
    attempts: int = 0


@dataclass
class CandidateProfile:
    """Analyzed candidate profile — output of analyzer.py."""
    # Identity
    name: str
    role: str
    experience: int
    education: str

    # Mission categorization (lists of day numbers)
    strong_days: list[int] = field(default_factory=list)      # passed, attempts == 1
    struggled_days: list[int] = field(default_factory=list)    # passed, attempts >= 3
    failed_days: list[int] = field(default_factory=list)       # passed == False
    skipped_days: list[int] = field(default_factory=list)      # skipped == True
    not_attempted_days: list[int] = field(default_factory=list)  # no mission entry

    # Aggregate signals
    completion_rate: float = 0.0      # missionsCompleted / 31
    first_try_rate: float = 0.0       # missionsFirstTry / missionsCompleted
    calibration_level: str = "mid"    # "junior" | "mid" | "senior"


@dataclass
class PlannedQuestion:
    """A single planned question slot within the interview plan."""
    day: int                          # Curriculum day number
    question_type: str                # "conceptual" | "applied" | "diagnostic"
    optional: bool = False            # True for Q3 slots (can be skipped on strong answers)


@dataclass
class InterviewPlan:
    """The full interview plan — output of planner.py."""
    selected_days: list[int]          # The 4 chosen curriculum day numbers
    day_priorities: dict[int, int]    # {day_number: priority_score}
    questions: list[PlannedQuestion]  # Ordered list of planned question slots
    total_planned: int = 0            # len(questions)


@dataclass
class QuestionEval:
    """Evaluation of a single candidate answer."""
    day: int
    question_type: str                # "conceptual" | "applied" | "diagnostic" | "follow_up"
    score: int                        # 1-5
    notes: str = ""


@dataclass
class InterviewSession:
    """Full state for an active interview session."""
    session_id: str
    candidate: dict[str, Any]         # Raw candidate object from request
    profile: CandidateProfile
    plan: InterviewPlan

    # Conversation history
    conversation: list[dict[str, str]] = field(default_factory=list)
    # [{"role": "interviewer"/"candidate", "content": "..."}]

    # Per-question evaluations
    evaluations: list[QuestionEval] = field(default_factory=list)

    # Plan pointer
    current_question_index: int = 0   # Index into plan.questions
    total_questions_asked: int = 0    # Includes follow-ups

    # Adaptive state
    follow_up_budget: int = 4
    pending_follow_up: bool = False

    # Status
    status: str = "in_progress"       # "in_progress" | "completed"
