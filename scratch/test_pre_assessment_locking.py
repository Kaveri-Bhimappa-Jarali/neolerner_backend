import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import uuid
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def run_pre_assessment_locking_tests():
    print("==================================================")
    print("   PRE-ASSESSMENT LOCKING & NODE BUG TEST SUITE   ")
    print("==================================================")

    # 1. Register a fresh new user
    email = f"freshuser_{uuid.uuid4().hex[:6]}@test.com"
    reg_res = client.post("/api/auth/register", json={
        "email": email,
        "password": "TestPassword123",
        "full_name": "Fresh Test Learner",
        "age": 22
    })
    assert reg_res.status_code in [200, 201], f"Register failed: {reg_res.text}"
    login_res = client.post("/api/auth/login", data={"username": email, "password": "TestPassword123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"[1/4] Registered fresh user '{email}'.")

    # 2. Complete Onboarding
    onboard_res = client.put("/api/learners/me", json={
        "learning_goal": "career",
        "prior_knowledge": "intermediate"
    }, headers=headers)
    assert onboard_res.status_code == 200

    # 3. Check Initial Diagnostic Status before test
    status_before = client.get("/api/diagnostic/status", headers=headers).json()
    print(f"[2/4] Initial state before diagnostic: completed={status_before['has_completed_placement_test']}")
    assert status_before["has_completed_placement_test"] is False

    # Check progress records before test (must be 0)
    prog_before = client.get("/api/progress/me", headers=headers).json()
    completed_before = len([p for p in prog_before if p.get("status") == "completed"])
    print(f"  -> Completed lessons count before test: {completed_before}")
    assert completed_before == 0, "New user must have 0 completed lessons!"

    # 4. Generate & Submit Diagnostic Placement Test
    session_res = client.post("/api/diagnostic/session", headers=headers)
    assert session_res.status_code == 200
    session_data = session_res.json()
    
    # Submit placement answers
    submissions = []
    for q in session_data["questions"]:
        submissions.append({
            "question_id": q["id"],
            "is_correct": True,
            "difficulty_level": q["difficulty_level"],
            "user_answer": "correct"
        })

    submit_res = client.post("/api/diagnostic/submit", json={
        "session_id": session_data["session_id"],
        "submissions": submissions
    }, headers=headers)
    assert submit_res.status_code == 200
    sub_data = submit_res.json()

    print(f"[3/4] Diagnostic test submitted successfully.")
    print(f"  -> Score: {sub_data['placement_score']}%, Level: {sub_data['cefr_level']} ({sub_data['benchmark_level']})")

    # 5. Verify NO lessons were marked completed automatically!
    prog_after = client.get("/api/progress/me", headers=headers).json()
    completed_after = len([p for p in prog_after if p.get("status") == "completed"])
    print(f"[4/4] Completed lessons count after diagnostic test: {completed_after}")
    assert completed_after == 0, f"Diagnostic test MUST NOT mark lessons as completed! Expected 0, found {completed_after}."

    # Verify status is now updated to completed=True
    status_after = client.get("/api/diagnostic/status", headers=headers).json()
    assert status_after["has_completed_placement_test"] is True
    print("  -> Diagnostic status correctly updated: has_completed_placement_test=True.")

    print("\n==================================================")
    print("   PRE-ASSESSMENT LOCKING & NODE FIX VERIFIED 100%! ")
    print("==================================================")

if __name__ == "__main__":
    run_pre_assessment_locking_tests()
