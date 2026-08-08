"""Interview planner — selects 4 curriculum days and distributes questions.

Pure Python, no LLM. Uses the CandidateProfile and curriculum data to build
a personalized InterviewPlan with scored day selection and question slots.
"""

from app import config
from app.models import CandidateProfile, CurriculumDay, InterviewPlan, PlannedQuestion


# ---------------------------------------------------------------------------
# Role-to-topic relevance mapping
# ---------------------------------------------------------------------------

# Maps keywords in job roles to curriculum day numbers that are especially
# relevant for that role. Used for scoring "not attempted" days.
_ROLE_RELEVANT_DAYS: dict[str, set[int]] = {
    "data": {4, 5, 6, 7, 8, 9, 10},                    # Data-heavy roles
    "backend": {3, 16, 18, 28},                          # Backend / API roles
    "frontend": {3, 17, 19},                             # Frontend roles
    "devops": {28, 29, 30},                              # DevOps / infra roles
    "ai": {7, 8, 10, 11, 12, 13, 14, 15, 21, 22, 23},  # AI / ML roles
    "engineer": {7, 8, 12, 16, 22, 28},                  # General engineering
    "security": {27},                                     # Security roles
    "architect": {11, 22, 23, 24, 28},                   # Architecture roles
    "analyst": {4, 5, 6, 12},                             # Analyst roles
    "mobile": {3, 16, 17, 18, 28},                       # Mobile dev
    "intern": {1, 2, 3, 7, 12},                           # Entry-level / intern
    "junior": {1, 2, 3, 7, 12},                           # Junior
}


def _get_relevant_days_for_role(role: str) -> set[int]:
    """Return curriculum days relevant to the candidate's job role."""
    role_lower = role.lower()
    relevant: set[int] = set()
    for keyword, days in _ROLE_RELEVANT_DAYS.items():
        if keyword in role_lower:
            relevant |= days
    return relevant


def _score_day(
    day_num: int,
    profile: CandidateProfile,
    role_relevant_days: set[int],
) -> int:
    """Score a single curriculum day based on the candidate's relationship to it.

    Higher score = higher priority for inclusion in the interview.
    """
    if day_num in profile.failed_days:
        return 100
    if day_num in profile.skipped_days:
        return 80
    if day_num in profile.struggled_days:
        return 70
    if day_num in profile.not_attempted_days:
        return 50 if day_num in role_relevant_days else 5

    # Passed days (strong or with moderate effort)
    if day_num in profile.strong_days:
        return 30 if day_num in config.CORE_AI_DAYS else 10

    # Passed with 2 attempts (not in strong or struggled)
    return 40


def _get_module_for_day(day_num: int, curriculum_days: dict[int, CurriculumDay]) -> int:
    """Return the module number for a given curriculum day."""
    cd = curriculum_days.get(day_num)
    return cd.module_number if cd else 0


def _select_days(
    profile: CandidateProfile,
    curriculum_days: dict[int, CurriculumDay],
) -> list[tuple[int, int]]:
    """Select 4 curriculum days, ensuring ≥3 different modules.

    Returns list of (day_number, priority_score) sorted by score descending.
    """
    role_relevant = _get_relevant_days_for_role(profile.role)

    # Score every curriculum day
    scored: list[tuple[int, int]] = []
    for day_num in sorted(curriculum_days.keys()):
        score = _score_day(day_num, profile, role_relevant)
        scored.append((day_num, score))

    # Sort by score descending, then day number ascending for stability
    scored.sort(key=lambda x: (-x[1], x[0]))

    # Greedy selection with module diversity constraint
    selected: list[tuple[int, int]] = []
    modules_covered: set[int] = set()

    for day_num, score in scored:
        if len(selected) >= config.NUM_INTERVIEW_DAYS:
            break
        module = _get_module_for_day(day_num, curriculum_days)
        selected.append((day_num, score))
        modules_covered.add(module)

    # Check module diversity — if we have < MIN_MODULES_COVERED, swap the
    # lowest-priority selected day for the highest-priority day from a new module
    if len(modules_covered) < config.MIN_MODULES_COVERED:
        selected_days_set = {d for d, _ in selected}
        for day_num, score in scored:
            if day_num in selected_days_set:
                continue
            module = _get_module_for_day(day_num, curriculum_days)
            if module not in modules_covered:
                # Replace the lowest-scored selected day
                selected[-1] = (day_num, score)
                modules_covered.add(module)
                if len(modules_covered) >= config.MIN_MODULES_COVERED:
                    break

    # Sort selected by day number for a natural interview flow
    selected.sort(key=lambda x: x[0])
    return selected


def _distribute_questions(
    selected_days: list[tuple[int, int]],
) -> list[PlannedQuestion]:
    """Distribute questions across selected days.

    Each day gets 2 guaranteed questions (Q1 conceptual, Q2 applied).
    The highest-priority day gets a 3rd diagnostic probe.
    """
    questions: list[PlannedQuestion] = []

    # Find the highest-priority day
    highest_priority_day = max(selected_days, key=lambda x: x[1])[0]

    for day_num, _score in selected_days:
        # Q1: Conceptual (always)
        questions.append(PlannedQuestion(
            day=day_num,
            question_type="conceptual",
            optional=False,
        ))
        # Q2: Applied / Scenario (always)
        questions.append(PlannedQuestion(
            day=day_num,
            question_type="applied",
            optional=False,
        ))
        # Q3: Diagnostic probe (only for highest-priority day)
        if day_num == highest_priority_day:
            questions.append(PlannedQuestion(
                day=day_num,
                question_type="diagnostic",
                optional=True,
            ))

    return questions


def build_interview_plan(
    profile: CandidateProfile,
    curriculum_days: dict[int, CurriculumDay],
) -> InterviewPlan:
    """Build a complete interview plan from the candidate profile and curriculum.

    Args:
        profile: Analyzed candidate profile.
        curriculum_days: Lookup table {day_number: CurriculumDay}.

    Returns:
        An InterviewPlan with selected days, priorities, and question slots.
    """
    selected = _select_days(profile, curriculum_days)

    day_priorities = {day: score for day, score in selected}
    questions = _distribute_questions(selected)

    return InterviewPlan(
        selected_days=[d for d, _ in selected],
        day_priorities=day_priorities,
        questions=questions,
        total_planned=len(questions),
    )
