import json
from pathlib import Path
from app.main import _load_curriculum
from app.analyzer import analyze_candidate
from app.planner import build_interview_plan

def main():
    print("Loading curriculum...")
    try:
        curriculum_days = _load_curriculum()
        print(f"Loaded {len(curriculum_days)} curriculum days.")
    except Exception as e:
        print(f"Error loading curriculum: {e}")
        return

    print("Loading candidates...")
    candidates_path = Path("data/candidates.json")
    with open(candidates_path, "r") as f:
        candidates = json.load(f)["candidates"]
    
    print(f"Loaded {len(candidates)} candidates.")

    # Test analyzer and planner on the first candidate
    candidate = candidates[0]
    print(f"\nTesting Candidate: {candidate['member']['name']}")
    
    try:
        profile = analyze_candidate(candidate, curriculum_days)
        print("Profile generated successfully:")
        print(f"  Role: {profile.role}, Calibration: {profile.calibration_level}")
        print(f"  Strong days: {profile.strong_days}")
        print(f"  Struggled days: {profile.struggled_days}")
    except Exception as e:
        print(f"Error in analyzer: {e}")
        return

    try:
        plan = build_interview_plan(profile, curriculum_days)
        print("Plan generated successfully:")
        print(f"  Selected Days: {plan.selected_days}")
        print(f"  Total planned questions: {plan.total_planned}")
    except Exception as e:
        print(f"Error in planner: {e}")
        return
        
    print("\nAnalyzer and Planner OK.")

if __name__ == "__main__":
    main()
