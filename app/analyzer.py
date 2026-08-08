"""Candidate profile analysis — pure Python, no LLM.

Takes a raw candidate dict and the curriculum lookup, produces a CandidateProfile
with categorized missions, aggregate signals, and a calibration level.
"""

from app.models import CandidateProfile, MissionRecord, CurriculumDay


def _parse_missions(raw_missions: list[dict]) -> list[MissionRecord]:
    """Convert raw mission dicts into typed MissionRecord objects."""
    records: list[MissionRecord] = []
    for m in raw_missions:
        records.append(MissionRecord(
            day=m["day"],
            title=m["title"],
            passed=m.get("passed"),
            skipped=m.get("skipped", False),
            attempts=m.get("attempts", 0),
        ))
    return records


def _determine_calibration(role: str, experience: int, signals: dict) -> str:
    """Derive a calibration level from role, experience, and learning signals.

    Returns "junior", "mid", or "senior".
    """
    completed = signals.get("missionsCompleted", 0)
    first_try = signals.get("missionsFirstTry", 0)
    commit_days = signals.get("commitDays", 0)

    # Experience-based base level
    if experience <= 1:
        base = 0  # junior
    elif experience <= 6:
        base = 1  # mid
    else:
        base = 2  # senior

    # Performance adjustment
    first_try_rate = first_try / max(completed, 1)
    if first_try_rate >= 0.7 and commit_days >= 25:
        base = min(base + 1, 2)  # bump up for strong performers
    elif first_try_rate < 0.3 or commit_days < 15:
        base = max(base - 1, 0)  # bump down for struggling learners

    return ["junior", "mid", "senior"][base]


def analyze_candidate(
    candidate: dict,
    curriculum_days: dict[int, CurriculumDay],
) -> CandidateProfile:
    """Analyze a raw candidate object into a structured CandidateProfile.

    Args:
        candidate: Raw candidate dict from the API request body.
        curriculum_days: Lookup table {day_number: CurriculumDay} from curriculum.json.

    Returns:
        A fully populated CandidateProfile.
    """
    member = candidate["member"]
    missions = _parse_missions(candidate.get("missions", []))
    signals = candidate.get("signals", {})

    # All curriculum day numbers
    all_days = set(curriculum_days.keys())

    # Days the candidate has missions for
    mission_days = {m.day for m in missions}

    # Categorize each mission
    strong: list[int] = []
    struggled: list[int] = []
    failed: list[int] = []
    skipped: list[int] = []

    for m in missions:
        if m.skipped:
            skipped.append(m.day)
        elif m.passed is False:
            failed.append(m.day)
        elif m.passed is True and m.attempts == 1:
            strong.append(m.day)
        elif m.passed is True and m.attempts >= 3:
            struggled.append(m.day)
        # passed with 2 attempts — neither strong nor struggled, just "passed"

    not_attempted = sorted(all_days - mission_days)

    # Aggregate signals
    missions_completed = signals.get("missionsCompleted", 0)
    missions_first_try = signals.get("missionsFirstTry", 0)
    completion_rate = missions_completed / 31
    first_try_rate = missions_first_try / max(missions_completed, 1)

    calibration = _determine_calibration(
        member.get("jobRole", ""),
        member.get("yearsExperience", 0),
        signals,
    )

    return CandidateProfile(
        name=member.get("name", "Candidate"),
        role=member.get("jobRole", "Unknown"),
        experience=member.get("yearsExperience", 0),
        education=member.get("education", ""),
        strong_days=sorted(strong),
        struggled_days=sorted(struggled),
        failed_days=sorted(failed),
        skipped_days=sorted(skipped),
        not_attempted_days=not_attempted,
        completion_rate=round(completion_rate, 2),
        first_try_rate=round(first_try_rate, 2),
        calibration_level=calibration,
    )
