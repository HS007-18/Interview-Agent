import asyncio
import json
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

# Mock the LLM before importing main
async def mock_chat_json(*args, **kwargs):
    # Depending on the instruction type, return a different mock response
    prompt_str = str(args) + str(kwargs)
    if "FINAL interview question" in prompt_str:
        return {
            "evaluation": {"score": 4, "notes": "Good final answer"},
            "reply": "Thank you, that concludes the interview."
        }
    elif "Generate feedback" in prompt_str:
        return {
            "summary": "Candidate did well overall.",
            "strengths": ["Data analysis", "Architecture"],
            "gaps": ["DevOps", "Testing"],
            "next": ["Review CI/CD concepts"]
        }
    elif "Start the interview" in prompt_str:
        return {
            "reply": "Welcome to the interview! Let's start with a question about Day X."
        }
    else:
        # Advance or Follow-up
        return {
            "evaluation": {"score": 3, "notes": "Adequate answer."},
            "reply": "Good point. Let's move on to the next question."
        }

async def mock_chat(*args, **kwargs):
    return "{}" # Not really used in chat_json currently since it directly returns

def test_api():
    print("Patching LLM service...")
    with patch('app.llm_service.LLMService.chat_json', new_callable=lambda: mock_chat_json), \
         patch('app.llm_service.LLMService.chat', new_callable=lambda: mock_chat):
        
        from app.main import app, _curriculum_days, _load_curriculum
        
        # Load curriculum explicitly for the test (FastAPI startup event doesn't fire in standard TestClient without 'with TestClient' context manager doing it properly)
        if not _curriculum_days:
            _curriculum_days.update(_load_curriculum())

        client = TestClient(app)
        
        print("Testing /api/candidates...")
        resp = client.get("/api/candidates")
        assert resp.status_code == 200
        candidates = resp.json()["candidates"]
        print(f"  Got {len(candidates)} candidates.")
        
        candidate = candidates[0]
        session_id = "test-session-123"
        
        print("\nTesting POST /api/interview (Start)...")
        resp = client.post("/api/interview", json={"sessionId": session_id, "candidate": candidate})
        assert resp.status_code == 200
        data = resp.json()
        print(f"  Reply: {data['reply']}")
        print(f"  Done: {data['done']}")
        
        print("\nTesting POST /api/interview (Turn 1)...")
        resp = client.post("/api/interview", json={"sessionId": session_id, "message": "Here is my answer to the first question."})
        assert resp.status_code == 200
        data = resp.json()
        print(f"  Reply: {data['reply']}")
        print(f"  Done: {data['done']}")

        # Loop until done
        turn = 2
        while not data["done"] and turn < 15: # safety break
            print(f"\nTesting POST /api/interview (Turn {turn})...")
            resp = client.post("/api/interview", json={"sessionId": session_id, "message": "My answer..."})
            assert resp.status_code == 200
            data = resp.json()
            print(f"  Reply: {data['reply']}")
            print(f"  Done: {data['done']}")
            turn += 1
            
        if data["done"]:
            print("\nInterview completed!")
            print("Feedback:")
            print(json.dumps(data.get("feedback", {}), indent=2))
        else:
            print("\nInterview didn't finish properly.")

if __name__ == "__main__":
    test_api()
