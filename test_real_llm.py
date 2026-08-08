import asyncio
import json
from pathlib import Path
from fastapi.testclient import TestClient

def run_real_llm_test():
    print("Testing real LLM interaction...")
    
    # Do not mock the LLM this time! We want it to use OpenRouter.
    # Load the app
    from app.main import app, _curriculum_days, _load_curriculum
    from app.llm_service import get_llm_service
    
    # Initialize LLM early to check API key loads
    try:
        llm = get_llm_service()
        print(f"LLM Service ready. Model: {llm.model}")
    except Exception as e:
        print(f"Failed to initialize LLM: {e}")
        return

    # Load curriculum explicitly for TestClient
    if not _curriculum_days:
        _curriculum_days.update(_load_curriculum())

    client = TestClient(app)

    # 1. Get candidates
    print("\nFetching candidates...")
    resp = client.get("/api/candidates")
    candidates = resp.json()["candidates"]
    candidate = candidates[0]  # Sarah Johnson, Senior Data Engineer
    print(f"Selected candidate: {candidate['member']['name']} ({candidate['member']['jobRole']})")

    session_id = "real-test-session-001"

    # 2. Start the interview
    print("\nStarting the interview (this will call OpenRouter)...")
    resp = client.post("/api/interview", json={"sessionId": session_id, "candidate": candidate})
    
    if resp.status_code != 200:
        print(f"Error starting interview: {resp.text}")
        return
        
    data = resp.json()
    print(f"\n[INTERVIEWER]:\n{data['reply']}\n")
    
    if data["done"]:
        print("Interview finished unexpectedly early.")
        return

    # 3. Simulate a few conversation turns
    # Turn 1: Weak answer to trigger follow-up probe logic
    user_msgs = [
        "I don't really remember much about that topic. I think I used a tool once?",
        "Oh, I see. Well, I would probably just write a Python script with pandas.",
        "To optimize it, I guess I'd add an index to the database?"
    ]
    
    for i, msg in enumerate(user_msgs, 1):
        print(f"\n[CANDIDATE Turn {i}]:\n{msg}\n")
        print("Waiting for LLM response...")
        resp = client.post("/api/interview", json={"sessionId": session_id, "message": msg})
        
        if resp.status_code != 200:
            print(f"Error on turn {i}: {resp.text}")
            return
            
        data = resp.json()
        print(f"\n[INTERVIEWER Turn {i}]:\n{data['reply']}\n")
        
        # We also want to peek at the internal state
        from app.session import get_session
        sess = get_session(session_id)
        last_eval = sess.evaluations[-1] if sess.evaluations else None
        if last_eval:
            print(f"  [INTERNAL EVAL] Score: {last_eval.score}/5, Notes: {last_eval.notes}")
            print(f"  [STATE] pending_follow_up: {sess.pending_follow_up}, follow_up_budget: {sess.follow_up_budget}")
            print(f"  [STATE] index: {sess.current_question_index} / {sess.plan.total_planned}, asked: {sess.total_questions_asked}")

        if data["done"]:
            print("\nInterview completed!")
            if "feedback" in data and data["feedback"]:
                print("\nFeedback generated:")
                print(json.dumps(data["feedback"], indent=2))
            break
            
    print("\nReal LLM Test script finished.")

if __name__ == "__main__":
    run_real_llm_test()
