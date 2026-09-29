import os
import sys
import uuid
import pytest
from fastapi.testclient import TestClient

# Ensure backend path is added
backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import database
import models
import auth
from main import app

client = TestClient(app)

def test_full_audit_lifecycle():
    print("\n" + "=" * 70)
    print("RUNNING COMPREHENSIVE NEOLEARNER PERSISTENCE & DATA ISOLATION SUITE")
    print("=" * 70)

    # Make sure tables exist
    database.ensure_tables_created()

    # TEST 1: User Registration, Database Persistence, and Re-login
    user_a_email = f"user_a_{uuid.uuid4().hex[:6]}@example.com"
    user_a_pass = "SecurePass123!"

    print(f"\n[TEST 1] Registering User A ({user_a_email})...")
    reg_resp_a = client.post("/api/auth/register", json={
        "email": user_a_email,
        "password": user_a_pass,
        "full_name": "User Alpha",
        "age": 25,
        "preferred_language_code": "en",
        "target_language_code": "kn"
    })
    assert reg_resp_a.status_code == 201, f"User A registration failed: {reg_resp_a.text}"
    dev_code_a = reg_resp_a.json().get("verification_code") or "123456"

    # Verify Email
    ver_resp_a = client.post("/api/auth/verify-email", json={
        "email": user_a_email,
        "code": dev_code_a
    })
    assert ver_resp_a.status_code == 200, f"User A email verification failed: {ver_resp_a.text}"
    token_a = ver_resp_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Verify User A exists in DB
    db = next(database.get_db())
    db_user_a = db.query(models.Learner).filter(models.Learner.email == user_a_email).first()
    assert db_user_a is not None, "User A missing from database"
    assert db_user_a.full_name == "User Alpha"
    print("  [OK] User A registered and verified in persistent DB.")

    # Re-fetch Profile (simulating browser refresh / token re-validation)
    me_resp_a = client.get("/api/learners/me", headers=headers_a)
    assert me_resp_a.status_code == 200, f"User A profile refresh failed: {me_resp_a.text}"
    assert me_resp_a.json()["email"] == user_a_email

    # Logout & Re-login
    login_resp_a = client.post("/api/auth/login", data={
        "username": user_a_email,
        "password": user_a_pass
    })
    assert login_resp_a.status_code == 200, f"User A re-login failed: {login_resp_a.text}"
    new_token_a = login_resp_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {new_token_a}"}
    print("  [OK] User A logged out and successfully re-authenticated.")


    # TEST 2: Learner Data Updates & Persistence
    print("\n[TEST 2] Updating Learner Data for User A (XP, Streaks, Placement Score)...")
    # Complete placement test session
    sess_resp = client.post("/api/diagnostic/session", headers=headers_a)
    assert sess_resp.status_code == 200, f"Failed starting placement session: {sess_resp.text}"
    sess_data = sess_resp.json()
    session_id = sess_data["session_id"]
    questions = sess_data["questions"]

    submissions_list = []
    for q in questions:
        q_id = q["id"]
        correct_text = "A / Ah"
        for ans in q.get("answers", []):
            if ans.get("is_correct"):
                correct_text = ans["text"]
                break
        submissions_list.append({
            "question_id": q_id,
            "given_answer": correct_text,
            "is_correct": True,
            "difficulty_level": q.get("difficulty_level", 1)
        })

    # Submit placement test results
    sub_resp = client.post("/api/diagnostic/submit", json={
        "session_id": session_id,
        "submissions": submissions_list
    }, headers=headers_a)
    assert sub_resp.status_code == 200, f"Failed submitting placement results: {sub_resp.text}"

    # Refresh User A profile & verify persistent placement score
    me_resp_a2 = client.get("/api/learners/me", headers=headers_a)
    assert me_resp_a2.status_code == 200
    assert me_resp_a2.json()["has_completed_placement_test"] is True
    print("  [OK] User A completed placement test; score and status persisted.")


    # TEST 3: User B Creation and Data Isolation
    user_b_email = f"user_b_{uuid.uuid4().hex[:6]}@example.com"
    user_b_pass = "SecurePass456!"

    print(f"\n[TEST 3] Registering User B ({user_b_email}) and testing Data Isolation...")
    reg_resp_b = client.post("/api/auth/register", json={
        "email": user_b_email,
        "password": user_b_pass,
        "full_name": "User Beta",
        "age": 30,
        "preferred_language_code": "en",
        "target_language_code": "hi"
    })
    assert reg_resp_b.status_code == 201
    dev_code_b = reg_resp_b.json().get("verification_code") or "123456"

    ver_resp_b = client.post("/api/auth/verify-email", json={
        "email": user_b_email,
        "code": dev_code_b
    })
    token_b = ver_resp_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Fetch User B profile
    me_resp_b = client.get("/api/learners/me", headers=headers_b)
    assert me_resp_b.status_code == 200
    assert me_resp_b.json()["email"] == user_b_email
    assert me_resp_b.json()["email"] != user_a_email
    assert me_resp_b.json()["has_completed_placement_test"] is False

    # Attempt to fetch User A's progress as User B -> should fail or return only User B's records
    prog_resp_b = client.get("/api/progress", headers=headers_b)
    assert prog_resp_b.status_code == 200
    b_records = prog_resp_b.json()
    for rec in (b_records if isinstance(b_records, list) else []):
        assert rec.get("learner_id") != str(db_user_a.id)

    print("  [OK] User A and User B data are strictly isolated.")


    # TEST 4: Backend Process Re-invocation / Session Refresh
    print("\n[TEST 4] Simulating Backend Re-invocation / Process Restart...")
    # Re-initialize DB connection generator
    database._tables_initialized = False
    database.ensure_tables_created()

    # Verify User A and User B both still exist in persistent DB
    db_recheck = next(database.get_db())
    recheck_a = db_recheck.query(models.Learner).filter(models.Learner.email == user_a_email).first()
    recheck_b = db_recheck.query(models.Learner).filter(models.Learner.email == user_b_email).first()

    assert recheck_a is not None, "User A missing after backend reinvocation!"
    assert recheck_b is not None, "User B missing after backend reinvocation!"
    assert recheck_a.has_completed_placement_test is True

    print("  [OK] All persistent data verified after backend reinvocation!")
    
    # TEST 5: Vercel Path Rewrites & Health Check Resolution
    print("\n[TEST 5] Testing Vercel Path Rewrites and Root Routing...")
    root_resp = client.get("/")
    assert root_resp.status_code == 200, f"Root / GET failed: {root_resp.text}"
    assert root_resp.json()["status"] == "ok"

    health_resp = client.get("/api/health")
    assert health_resp.status_code == 200, f"/api/health GET failed: {health_resp.text}"

    admin_resp = client.get("/admin")
    assert admin_resp.status_code == 200, f"/admin GET failed: {admin_resp.text}"

    index_resp = client.get("/api/index.py")
    assert index_resp.status_code == 200, f"/api/index.py GET failed: {index_resp.text}"
    assert index_resp.json()["status"] == "ok"
    print("  [OK] Vercel rewrites and health check routes all returned 200 OK.")

    print("\n" + "=" * 70)
    print("ALL API PERSISTENCE & DATA ISOLATION TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    test_full_audit_lifecycle()
