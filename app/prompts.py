"""LLM prompt templates for all interview phases.

All prompt construction lives here. interviewer.py calls these functions
to get the system prompt + user messages for each LLM call.
"""

from app.models import CandidateProfile, CurriculumDay, InterviewPlan, InterviewSession, QuestionEval


# ---------------------------------------------------------------------------
# System prompt — sent with every LLM call
# ---------------------------------------------------------------------------

def build_system_prompt(
    profile: CandidateProfile,
    plan: InterviewPlan,
    curriculum_days: dict[int, CurriculumDay],
    current_day: int,
) -> str:
    """Build the system prompt with candidate context and interview plan."""

    # Summarize strong/weak topics
    strong_topics = ", ".join(
        curriculum_days[d].title for d in profile.strong_days
        if d in curriculum_days
    ) or "None identified"

    weak_topics_days = profile.failed_days + profile.skipped_days + profile.struggled_days
    weak_topics = ", ".join(
        curriculum_days[d].title for d in weak_topics_days
        if d in curriculum_days
    ) or "None identified"

    # Build the plan summary
    plan_lines = []
    for i, day_num in enumerate(plan.selected_days, 1):
        cd = curriculum_days.get(day_num)
        title = cd.title if cd else f"Day {day_num}"
        q_count = sum(1 for q in plan.questions if q.day == day_num)
        plan_lines.append(f"{i}. Day {day_num}: {title} — {q_count} questions")

    # Current day context
    current_cd = curriculum_days.get(current_day)
    if current_cd:
        current_context = (
            f"Day {current_day}: {current_cd.title}\n"
            f"Objectives: {'; '.join(current_cd.objectives)}\n"
            f"Tools: {', '.join(current_cd.tools)}"
        )
    else:
        current_context = f"Day {current_day}"

    return f"""You are a senior technical interviewer conducting a personalized interview \
for the ABTalks AI program. You are warm but rigorous, conversational but structured.

CANDIDATE PROFILE:
- Name: {profile.name}
- Role: {profile.role} ({profile.experience} years experience)
- Education: {profile.education}
- Calibration: {profile.calibration_level}
- Completion Rate: {round(profile.completion_rate * 100)}%
- Strengths: {strong_topics}
- Gaps: {weak_topics}

INTERVIEW PLAN:
You will cover these 4 curriculum topics in order:
{chr(10).join(plan_lines)}

CURRICULUM CONTEXT FOR CURRENT TOPIC:
{current_context}

RULES:
- Calibrate difficulty to the candidate's level ({profile.calibration_level})
- Ask questions that test understanding, not memorization
- Keep responses concise (2-4 sentences + 1 question)
- Never reveal your evaluation, scoring, or internal notes to the candidate
- Be conversational — this should feel like a real interview, not a quiz
- Reference specific curriculum objectives and tools where relevant"""


# ---------------------------------------------------------------------------
# Welcome + first question
# ---------------------------------------------------------------------------

def build_welcome_instruction(
    profile: CandidateProfile,
    plan: InterviewPlan,
    curriculum_days: dict[int, CurriculumDay],
) -> str:
    """Build the instruction for generating the welcome message + first question."""
    first_day = plan.selected_days[0]
    cd = curriculum_days.get(first_day)
    topic = cd.title if cd else f"Day {first_day}"
    objectives = "; ".join(cd.objectives) if cd else ""

    return f"""Start the interview. Do the following:

1. Greet the candidate by name ({profile.name})
2. Briefly mention their role ({profile.role}) and that this interview is tailored to their learning journey
3. Ask your FIRST question: a CONCEPTUAL question about "{topic}"
   Curriculum objectives for this topic: {objectives}

Respond in this exact JSON format:
{{
  "reply": "<your greeting + first question>"
}}"""


# ---------------------------------------------------------------------------
# Per-turn instructions
# ---------------------------------------------------------------------------

def build_advance_instruction(
    question_type: str,
    day_num: int,
    curriculum_days: dict[int, CurriculumDay],
    profile: CandidateProfile,
) -> str:
    """Build the instruction for evaluating an answer and advancing to the next question."""
    cd = curriculum_days.get(day_num)
    topic = cd.title if cd else f"Day {day_num}"
    objectives = "; ".join(cd.objectives) if cd else ""

    type_description = {
        "conceptual": "a CONCEPTUAL question (test their understanding of core concepts)",
        "applied": "an APPLIED / SCENARIO question (test practical ability — 'how would you...')",
        "diagnostic": "a DIAGNOSTIC PROBE question (directly address a gap or weakness in their learning journey)",
    }.get(question_type, f"a {question_type} question")

    return f"""The candidate just answered your previous question. Do the following:

1. Internally evaluate their answer (score 1-5, brief notes on what was good/missing)
2. Respond naturally — briefly acknowledge their answer (what was good, what was lacking)
3. Ask the NEXT question: {type_description} about "{topic}"
   Curriculum objectives: {objectives}

Score guide: 1=wrong/no answer, 2=vague/incomplete, 3=adequate, 4=good with depth, 5=excellent/comprehensive

Respond in this exact JSON format:
{{
  "evaluation": {{"score": <1-5>, "notes": "<brief assessment of their answer>"}},
  "reply": "<your conversational acknowledgment + next question>"
}}"""


def build_followup_instruction(
    day_num: int,
    curriculum_days: dict[int, CurriculumDay],
) -> str:
    """Build the instruction for a follow-up probe on the same topic (weak answer)."""
    cd = curriculum_days.get(day_num)
    topic = cd.title if cd else f"Day {day_num}"
    objectives = "; ".join(cd.objectives) if cd else ""

    return f"""The candidate just answered your previous question. Their answer was weak or \
incomplete. Do the following:

1. Internally evaluate their answer (score 1-5, brief notes)
2. Respond naturally — acknowledge what they got right, if anything
3. Ask a FOLLOW-UP PROBE on the SAME topic to help them demonstrate deeper \
understanding. Do NOT move to a new topic. Rephrase, simplify, or ask about a \
specific aspect they missed.

   Current topic: "{topic}"
   What they may have missed: {objectives}

Score guide: 1=wrong/no answer, 2=vague/incomplete, 3=adequate, 4=good with depth, 5=excellent/comprehensive

Respond in this exact JSON format:
{{
  "evaluation": {{"score": <1-5>, "notes": "<brief assessment of their answer>"}},
  "reply": "<your conversational acknowledgment + follow-up probe question>"
}}"""


def build_final_eval_instruction(day_num: int, curriculum_days: dict[int, CurriculumDay]) -> str:
    """Build the instruction for evaluating the final answer (no next question)."""
    cd = curriculum_days.get(day_num)
    topic = cd.title if cd else f"Day {day_num}"

    return f"""The candidate just answered your FINAL interview question about "{topic}". \
Do the following:

1. Internally evaluate their answer (score 1-5, brief notes)
2. Respond naturally — briefly acknowledge their answer and thank them for the interview

Score guide: 1=wrong/no answer, 2=vague/incomplete, 3=adequate, 4=good with depth, 5=excellent/comprehensive

Respond in this exact JSON format:
{{
  "evaluation": {{"score": <1-5>, "notes": "<brief assessment>"}},
  "reply": "<your acknowledgment + a brief closing remark thanking them>"
}}"""


# ---------------------------------------------------------------------------
# Feedback generation
# ---------------------------------------------------------------------------

def build_feedback_prompt(
    profile: CandidateProfile,
    evaluations: list[QuestionEval],
    curriculum_days: dict[int, CurriculumDay],
) -> str:
    """Build the prompt for generating structured interview feedback."""
    # Format evaluations
    eval_lines = []
    for i, ev in enumerate(evaluations, 1):
        cd = curriculum_days.get(ev.day)
        topic = cd.title if cd else f"Day {ev.day}"
        eval_lines.append(
            f"Q{i} [{ev.question_type}] — {topic}: "
            f"Score {ev.score}/5 — {ev.notes}"
        )

    avg_score = sum(e.score for e in evaluations) / max(len(evaluations), 1)

    return f"""Based on the full interview, generate structured feedback for the candidate.

CANDIDATE: {profile.name} — {profile.role} ({profile.experience} years experience)
CALIBRATION LEVEL: {profile.calibration_level}
AVERAGE SCORE: {avg_score:.1f}/5

PER-QUESTION EVALUATIONS:
{chr(10).join(eval_lines)}

Generate feedback that is specific, actionable, and references the actual topics discussed.

Respond in this exact JSON format:
{{
  "summary": "<2-3 sentence overall assessment of the candidate's performance>",
  "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "gaps": ["<gap 1>", "<gap 2>", "<gap 3>"],
  "next": ["<actionable recommendation 1>", "<actionable recommendation 2>", "<actionable recommendation 3>"]
}}

Each array should have 3-5 concise, actionable points. Reference specific topics from the interview."""
