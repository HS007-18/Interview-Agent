import json
from pathlib import Path
from fastapi.testclient import TestClient

def run_full_interview():
    print("Running full end-to-end interview...")
    from app.main import app, _curriculum_days, _load_curriculum
    from app.session import get_session
    
    if not _curriculum_days:
        _curriculum_days.update(_load_curriculum())

    client = TestClient(app)

    # Fetch candidates and pick a junior one to test a different calibration
    resp = client.get("/api/candidates")
    candidates = resp.json()["candidates"]
    candidate = next(c for c in candidates if "Junior" in c["member"]["jobRole"])
    print(f"Selected candidate: {candidate['member']['name']} ({candidate['member']['jobRole']})")

    session_id = "e2e-test-session-002"

    # Start the interview
    resp = client.post("/api/interview", json={"sessionId": session_id, "candidate": candidate})
    if resp.status_code != 200:
        print(f"Error starting: {resp.text}")
        return
        
    data = resp.json()
    print(f"\n[Q1 (Welcome)]: {data['reply']}")

    # Provide a mix of weak, average, and strong answers
    # to trigger follow-ups and skipped optional questions.
    candidate_responses = [
        "I'm not exactly sure, could you give me a hint?", # Intentional weak answer -> triggers follow up (score 1-2)
        "Oh, I see. In that case I would use a dictionary to store the keys, which is O(1) time complexity.", # Strong follow-up answer (score 4-5)
        "I would probably write a loop and check each item.", # Average answer (score 3)
        "For that scenario, I would implement a REST API using FastAPI. I would define Pydantic models for request validation and use async endpoints to ensure it can handle concurrent requests efficiently.", # Very strong answer -> skips optional Q3 (score 4-5)
        "I think I'd just use a simple database.", # Weak answer -> triggers follow up (score 1-2)
        "I'd use PostgreSQL and create a relational schema with proper foreign keys to ensure data integrity.", # Strong follow-up answer (score 4-5)
        "I would use Docker to containerize it.", # Average answer (score 3)
        "I would use Docker Compose for local development and then deploy it to a Kubernetes cluster for production, ensuring I have health checks and horizontal pod autoscaling configured.", # Very strong answer (score 4-5)
        "I guess I'd write some tests.", # Weak answer
        "I'd write unit tests using pytest and mock the external dependencies.", # Strong follow up
        "I would use GitHub Actions for CI/CD.", # Average
        "I'd set up a pipeline that runs tests, builds the Docker image, and deploys it automatically on merge.", # Strong
        "I'm not sure.", # Weak
        "Okay, I'd use logging.", # Weak
        "Yes, structured logging with JSON.", # Average
    ]

    turn = 1
    total_questions = 1
    
    while not data.get("done") and turn <= 15:
        # Pick the response based on turn index (or a generic one if we run out)
        msg = candidate_responses[turn - 1] if turn <= len(candidate_responses) else "I would try my best to implement the solution according to best practices."
        
        print(f"\n[A{turn}]: {msg}")
        resp = client.post("/api/interview", json={"sessionId": session_id, "message": msg})
        
        if resp.status_code != 200:
            print(f"Error on turn {turn}: {resp.text}")
            return
            
        data = resp.json()
        print(f"\n[Q{turn+1}]: {data['reply']}")
        
        # Check internal state
        sess = get_session(session_id)
        if sess.evaluations:
            last_eval = sess.evaluations[-1]
            print(f"  -> Score: {last_eval.score}/5. Note: {last_eval.notes}")
            print(f"  -> Plan Index: {sess.current_question_index} / {sess.plan.total_planned}")
            print(f"  -> Total Asked: {sess.total_questions_asked}, Budget: {sess.follow_up_budget}, Pending Follow-up: {sess.pending_follow_up}")
            
        total_questions = sess.total_questions_asked
        turn += 1

    print("\n--- FINAL RESULTS ---")
    sess = get_session(session_id)
    print(f"Total questions asked: {sess.total_questions_asked}")
    
    # Verify days covered
    days_covered = set(e.day for e in sess.evaluations)
    print(f"Days covered: {len(days_covered)} (Target: 4)")
    
    print("\nFeedback generated:")
    print(json.dumps(data.get("feedback"), indent=2))

    # Verify final API response matches technical spec exactly:
    # { "reply": string, "done": boolean, "feedback": { summary, strengths, gaps, next } }
    print("\nFinal API Payload Validation:")
    print(f"Contains 'reply': {'reply' in data and isinstance(data['reply'], str)}")
    print(f"Contains 'done': {'done' in data and data['done'] is True}")
    
    fb = data.get("feedback", {})
    if fb:
        print(f"Feedback contains 'summary': {'summary' in fb}")
        print(f"Feedback contains 'strengths': {'strengths' in fb and isinstance(fb['strengths'], list)}")
        print(f"Feedback contains 'gaps': {'gaps' in fb and isinstance(fb['gaps'], list)}")
        print(f"Feedback contains 'next': {'next' in fb and isinstance(fb['next'], list)}")
    else:
        print("MISSING FEEDBACK OBJECT!")

if __name__ == "__main__":
    run_full_interview()
