import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import json
import uuid
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def run_test():
    unique_id = uuid.uuid4().hex[:6]
    email = f"neouser_{unique_id}@test.com"
    password = "password123"

    print("=== STEP 1: Register New Learner & Login ===")
    reg_payload = {
        "email": email,
        "full_name": f"Neo Learner {unique_id}",
        "password": password,
        "age": 24,
        "proficiency_level": "Beginner"
    }
    r = client.post("/api/auth/register", json=reg_payload)
    assert r.status_code == 201, f"Register failed: {r.text}"
    learner = r.json()
    print(f"Registered user: {learner['email']} (ID: {learner['id']})")

    # Login to get JWT
    login_data = {
        "username": email,
        "password": password
    }
    r = client.post("/api/auth/login", data=login_data)
    assert r.status_code == 200, f"Login failed: {r.text}"
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"Logged in successfully. Token acquired.")

    print("\n=== STEP 2: Fetch Languages & Complete Onboarding ===")
    r = client.get("/api/languages/")
    assert r.status_code == 200, f"Languages failed: {r.text}"
    languages = r.json()
    kn_lang = next(l for l in languages if l["code"] == "kn")
    en_lang = next(l for l in languages if l["code"] == "en")

    onboarding_payload = {
        "preferred_language_id": kn_lang["id"],
        "target_language_id": en_lang["id"],
        "prior_knowledge": "some_words",
        "learning_goal": "career",
        "daily_minutes_goal": 20
    }
    r = client.put("/api/learners/me", json=onboarding_payload, headers=headers)
    assert r.status_code == 200, f"Update profile failed: {r.text}"
    updated_learner = r.json()
    assert updated_learner["learning_goal"] == "career"
    assert updated_learner["daily_minutes_goal"] == 20
    print(f"Onboarding saved: Goal={updated_learner['learning_goal']}, Target={en_lang['name']}, Interface={kn_lang['name']}")

    print("\n=== STEP 3: Check Initial Diagnostic Status ===")
    r = client.get("/api/diagnostic/status", headers=headers)
    assert r.status_code == 200, f"Diagnostic status failed: {r.text}"
    diag_status = r.json()
    assert diag_status["has_completed_placement_test"] is False
    assert diag_status["cefr_level"] == "A0"
    print(f"Diagnostic initial state verified: CEFR={diag_status['cefr_level']}, Completed={diag_status['has_completed_placement_test']}")

    print("\n=== STEP 4: Generate 15-Question Adaptive Placement Test ===")
    r = client.post("/api/diagnostic/session", headers=headers)
    assert r.status_code == 200, f"Diagnostic session generation failed: {r.text}"
    placement_session = r.json()
    questions = placement_session["questions"]
    print(f"Generated {len(questions)} diagnostic questions.")
    assert len(questions) == 15, f"Expected 15 questions, got {len(questions)}"
    
    for idx, q in enumerate(questions):
        print(f"  Q{idx+1} [{q['competency_tag']}]: {q['text'][:50]}... ({len(q['answers'])} options)")

    print("\n=== STEP 5: Submit Placement Answers (Simulating ~70% Mastery) ===")
    submissions = []
    for idx, q in enumerate(questions):
        is_user_correct = (idx < 11) # 11 correct out of 15 ~ 73%
        submissions.append({
            "question_id": q["id"],
            "is_correct": is_user_correct,
            "difficulty_level": q.get("difficulty_level", 2),
            "user_answer": "simulated_answer"
        })

    submit_payload = {
        "session_id": placement_session["session_id"],
        "submissions": submissions
    }
    r = client.post("/api/diagnostic/submit", json=submit_payload, headers=headers)
    assert r.status_code == 200, f"Submit placement failed: {r.text}"
    res = r.json()
    print("\n=== Placement Test Result Evaluated ===")
    print(f"  CEFR Level: {res['cefr_level']}")
    print(f"  Placement Score: {res['placement_score']}%")
    print(f"  Benchmark: {res['benchmark_level']}")
    print(f"  Skill Breakdown: {res['skill_breakdown']}")
    print(f"  Strengths: {res['strengths']}")
    print(f"  Weak Areas: {res['weak_areas']}")
    print(f"  Recommended Focus: {res['recommended_focus']}")
    print(f"  Tested-out nodes unlocked: {res['tested_out_nodes_count']}")
    print(f"  XP Awarded: {res['xp_earned']}")

    assert res["cefr_level"] in ["A1", "A2", "B1", "B2"], f"Unexpected CEFR level: {res['cefr_level']}"
    assert len(res["skill_breakdown"]) > 0

    print("\n=== STEP 6: Verify Updated Diagnostic Status & Dashboard APIs ===")
    r = client.get("/api/diagnostic/status", headers=headers)
    assert r.status_code == 200
    diag_status_after = r.json()
    assert diag_status_after["has_completed_placement_test"] is True
    assert diag_status_after["cefr_level"] == res["cefr_level"]
    print(f"Status verified in database: CEFR={diag_status_after['cefr_level']}, Weak Areas={diag_status_after['weak_areas']}")

    # Fetch personalized DAG learning path
    r = client.get("/api/learning-paths/me", headers=headers)
    assert r.status_code == 200
    path = r.json()
    print(f"Personalized Path: {path['course_title']}, {path['total_nodes']} nodes, {path['completion_rate']}% complete")

    # Fetch Weak-skill Adaptive Drill
    weak_skill = diag_status_after["weak_areas"][0] if diag_status_after["weak_areas"] else "listening"
    print(f"\n=== STEP 7: Generate Targeted Adaptive Workout for Weak Skill '{weak_skill}' ===")
    r = client.post(f"/api/learning-paths/adaptive-lesson?focus={weak_skill.lower()}", headers=headers)
    assert r.status_code == 200
    adaptive_lesson = r.json()
    print(f"Adaptive Workout Session: {adaptive_lesson['session_id']}, {len(adaptive_lesson['questions'])} drills for '{adaptive_lesson['target_competency']}'")

    print("\n🎉 ALL NEOLEARNER END-TO-END FLOW TESTS PASSED 100% PERFECTLY!")

if __name__ == "__main__":
    run_test()
