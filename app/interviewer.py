"""Core interview logic — the orchestrator.

Controls interview flow, manages state transitions, and calls the LLM
through llm_service. This module never imports openai or knows about providers.

The adaptive follow-up logic lives here:
- Weak answers (score 1-2) trigger follow-up probes on the same topic
- Strong answers (score 4-5) skip optional Q3 slots
- Hard constraints (≥8 questions, 4 days, max 12 total) are always enforced
"""

import logging

from app import config
from app.llm_service import get_llm_service
from app.models import (
    CurriculumDay,
    Feedback,
    InterviewPlan,
    InterviewResponse,
    InterviewSession,
    QuestionEval,
)
from app.prompts import (
    build_advance_instruction,
    build_feedback_prompt,
    build_final_eval_instruction,
    build_followup_instruction,
    build_system_prompt,
    build_welcome_instruction,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _current_day(session: InterviewSession) -> int:
    """Get the curriculum day number for the current question."""
    idx = session.current_question_index
    if idx < len(session.plan.questions):
        return session.plan.questions[idx].day
    # Fallback: last day in plan
    return session.plan.selected_days[-1]


def _current_question_type(session: InterviewSession) -> str:
    """Get the question type for the current planned question."""
    idx = session.current_question_index
    if idx < len(session.plan.questions):
        return session.plan.questions[idx].question_type
    return "applied"


def _can_follow_up(session: InterviewSession) -> bool:
    """Check if a follow-up probe is allowed.

    Follow-up is allowed only if:
    1. Budget remains
    2. Total questions won't exceed MAX_QUESTIONS
    3. There are still planned questions remaining to ask after this
    """
    remaining_planned = session.plan.total_planned - session.current_question_index
    return (
        session.follow_up_budget > 0
        and session.total_questions_asked + 1 < config.MAX_QUESTIONS
        and remaining_planned > 0
    )


def _has_optional_q3(session: InterviewSession) -> bool:
    """Check if the current day has an unasked optional Q3 coming up."""
    idx = session.current_question_index
    # Look ahead in the plan for an optional question on the current day
    current_day = _current_day(session)
    for i in range(idx, min(idx + 3, len(session.plan.questions))):
        q = session.plan.questions[i]
        if q.day == current_day and q.optional:
            return True
    return False


def _skip_optional_q3(session: InterviewSession) -> None:
    """Skip the optional Q3 for the current day by advancing past it."""
    current_day = _current_day(session)
    idx = session.current_question_index
    # Find and skip any optional questions for this day
    while idx < len(session.plan.questions):
        q = session.plan.questions[idx]
        if q.day == current_day and q.optional:
            # Remove it from the plan
            session.plan.questions.pop(idx)
            session.plan.total_planned -= 1
            logger.info(
                "Skipped optional Q3 for day %d (strong answer)", current_day
            )
            return
        if q.day != current_day:
            break  # Past this day's questions
        idx += 1


def _is_interview_complete(session: InterviewSession) -> bool:
    """Check if the interview should end."""
    return (
        session.current_question_index >= session.plan.total_planned
        or session.total_questions_asked >= config.MAX_QUESTIONS
    )


def _build_conversation_messages(session: InterviewSession, instruction: str) -> list[dict[str, str]]:
    """Convert session conversation + instruction into OpenAI-format messages."""
    messages: list[dict[str, str]] = []

    for entry in session.conversation:
        role = entry["role"]
        content = entry["content"]
        if role == "interviewer":
            messages.append({"role": "assistant", "content": content})
        else:
            messages.append({"role": "user", "content": content})

    # Add the instruction as the final user message
    messages.append({"role": "user", "content": instruction})
    return messages


# ---------------------------------------------------------------------------
# Main interview functions
# ---------------------------------------------------------------------------

async def generate_first_question(
    session: InterviewSession,
    curriculum_days: dict[int, CurriculumDay],
) -> InterviewResponse:
    """Generate the welcome message and first interview question.

    Called on the initial POST /api/interview request with a candidate object.
    """
    llm = get_llm_service()

    first_day = session.plan.selected_days[0]
    system_prompt = build_system_prompt(
        session.profile, session.plan, curriculum_days, first_day,
    )
    instruction = build_welcome_instruction(
        session.profile, session.plan, curriculum_days,
    )

    messages = [{"role": "user", "content": instruction}]
    response = await llm.chat_json(system_prompt, messages, temperature=0.7)

    reply = response.get("reply", "Welcome! Let's begin your interview.")

    # Record in conversation history
    session.conversation.append({"role": "interviewer", "content": reply})
    session.total_questions_asked = 1

    logger.info(
        "Interview started: session=%s, candidate=%s, days=%s, planned=%d",
        session.session_id, session.profile.name,
        session.plan.selected_days, session.plan.total_planned,
    )

    return InterviewResponse(reply=reply, done=False)


async def handle_turn(
    session: InterviewSession,
    candidate_message: str,
    curriculum_days: dict[int, CurriculumDay],
) -> InterviewResponse:
    """Handle a single conversation turn.

    This is the core adaptive logic:
    1. Record the candidate's answer
    2. Call LLM to evaluate answer + generate next question (or follow-up)
    3. Apply adaptive decision: follow-up, advance, or skip
    4. Check if interview is complete
    """
    llm = get_llm_service()

    # 1. Record the candidate's answer
    session.conversation.append({"role": "candidate", "content": candidate_message})

    current_day = _current_day(session)

    # 2. Determine what kind of turn this is and build the appropriate instruction
    is_last_question = (
        session.current_question_index >= session.plan.total_planned - 1
        and not session.pending_follow_up
        and session.total_questions_asked >= config.MIN_QUESTIONS - 1
    )

    if is_last_question:
        # This is the final answer — evaluate and close
        instruction = build_final_eval_instruction(current_day, curriculum_days)
    elif session.pending_follow_up:
        # Follow-up probe (triggered by previous weak answer)
        instruction = build_followup_instruction(current_day, curriculum_days)
    else:
        # Normal advance to next planned question
        next_idx = session.current_question_index + 1
        if next_idx < len(session.plan.questions):
            next_q = session.plan.questions[next_idx]
            next_day = next_q.day
            next_type = next_q.question_type
        else:
            next_day = current_day
            next_type = "applied"
        instruction = build_advance_instruction(
            next_type, next_day, curriculum_days, session.profile,
        )

    # 3. Call LLM
    system_prompt = build_system_prompt(
        session.profile, session.plan, curriculum_days, current_day,
    )
    messages = _build_conversation_messages(session, instruction)
    response = await llm.chat_json(system_prompt, messages, temperature=0.7)

    # 4. Parse evaluation and reply
    evaluation_data = response.get("evaluation", {"score": 3, "notes": "No evaluation"})
    reply = response.get("reply", "Let's continue.")

    score = int(evaluation_data.get("score", 3))
    notes = evaluation_data.get("notes", "")

    # Determine the question type for this evaluation
    if session.pending_follow_up:
        eval_type = "follow_up"
    else:
        eval_type = _current_question_type(session)

    # 5. Store evaluation
    session.evaluations.append(QuestionEval(
        day=current_day,
        question_type=eval_type,
        score=score,
        notes=notes,
    ))

    # 6. Clear pending follow-up flag
    was_follow_up = session.pending_follow_up
    session.pending_follow_up = False

    # 7. Adaptive decision: what happens next?
    if not was_follow_up:
        # We just evaluated a planned question — advance the plan pointer
        session.current_question_index += 1

    if is_last_question or _is_interview_complete(session):
        # Interview complete — generate feedback
        session.total_questions_asked += 1
        feedback = await _generate_feedback(session, curriculum_days)
        session.status = "completed"

        logger.info(
            "Interview completed: session=%s, total_questions=%d, avg_score=%.1f",
            session.session_id, session.total_questions_asked,
            sum(e.score for e in session.evaluations) / max(len(session.evaluations), 1),
        )

        return InterviewResponse(reply=reply, done=True, feedback=feedback)

    # Apply adaptive logic for the NEXT turn
    if score <= 2 and _can_follow_up(session):
        # WEAK answer — insert follow-up probe on the same topic
        session.pending_follow_up = True
        session.follow_up_budget -= 1
        logger.info(
            "Weak answer (score=%d) on day %d — scheduling follow-up probe "
            "(budget remaining: %d)",
            score, current_day, session.follow_up_budget,
        )
    elif score >= 4 and _has_optional_q3(session):
        # STRONG answer — skip optional Q3
        _skip_optional_q3(session)

    session.total_questions_asked += 1

    # 8. Record interviewer reply and continue
    session.conversation.append({"role": "interviewer", "content": reply})

    return InterviewResponse(reply=reply, done=False)


async def _generate_feedback(
    session: InterviewSession,
    curriculum_days: dict[int, CurriculumDay],
) -> Feedback:
    """Generate structured feedback from the full interview.

    Makes a separate LLM call with all evaluations to produce the
    summary, strengths, gaps, and next-steps arrays.
    """
    llm = get_llm_service()

    prompt = build_feedback_prompt(
        session.profile, session.evaluations, curriculum_days,
    )

    system = (
        "You are an expert technical interview evaluator. Generate specific, "
        "actionable feedback based on the interview performance data provided."
    )
    messages = [{"role": "user", "content": prompt}]

    response = await llm.chat_json(system, messages, temperature=0.5)

    return Feedback(
        summary=response.get("summary", "Interview completed."),
        strengths=response.get("strengths", []),
        gaps=response.get("gaps", []),
        next=response.get("next", []),
    )
