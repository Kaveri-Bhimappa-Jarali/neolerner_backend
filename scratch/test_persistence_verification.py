import sys
import os
import uuid
from fastapi.testclient import TestClient

backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, os.path.abspath(backend_dir))

from main import app
from database import SessionLocal
import models

def test_user_persistence():
    client = TestClient(app)
    
    unique_id = str(uuid.uuid4())[:8]
    test_email = f"persist_user_{unique_id}@example.com"
    test_password = "SecurePassword123!"
    test_name = f"Test User {unique_id}"
    
    # 1. Register new test user
    reg_payload = {
        "email": test_email,
        "password": test_password,
        "full_name": test_name,
        "age": 25,
        "preferred_language_code": "en",
        "target_language_code": "es",
        "proficiency_level": "Beginner",
        "learning_goal": "conversation",
        "prior_knowledge": "complete_beginner"
    }
    
    reg_resp = client.post("/api/auth/register", json=reg_payload)
    print("1. Registration Response Status:", reg_resp.status_code)
    assert reg_resp.status_code in (200, 201), f"Registration failed: {reg_resp.text}"
    reg_data = reg_resp.json()
    assert reg_data["email"] == test_email
    print("   User successfully registered with ID:", reg_data.get("id"))
    
    # 2. Log in with new user credentials
    login_resp = client.post("/api/auth/login", data={"username": test_email, "password": test_password})
    print("2. Login Response Status:", login_resp.status_code)
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token_data = login_resp.json()
    assert "access_token" in token_data
    access_token = token_data["access_token"]
    print("   User successfully logged in, access token received.")
    
    # 3. Access authenticated learner profile
    headers = {"Authorization": f"Bearer {access_token}"}
    profile_resp = client.get("/api/learners/me", headers=headers)
    print("3. Authenticated Profile Response Status:", profile_resp.status_code)
    assert profile_resp.status_code == 200, f"Profile fetch failed: {profile_resp.text}"
    profile_data = profile_resp.json()
    assert profile_data["email"] == test_email
    print("   Authenticated profile data verified for:", profile_data["full_name"])
    
    # 4. Simulate application restart / DB reconnect
    # We query the DB directly via a fresh DB session
    db = SessionLocal()
    try:
        db_user = db.query(models.Learner).filter(models.Learner.email == test_email).first()
        assert db_user is not None, "User not found in persistent DB!"
        assert db_user.full_name == test_name
        print("4. Direct DB Persistence Check OK. User exists in DB with email:", db_user.email)
    finally:
        db.close()
        
    # 5. Re-login after simulated restart
    relogin_resp = client.post("/api/auth/login", data={"username": test_email, "password": test_password})
    print("5. Re-login Response Status:", relogin_resp.status_code)
    assert relogin_resp.status_code == 200
    print("   Re-login after DB restart verified OK.")
    print("\n--- ALL PERSISTENCE TESTS PASSED 100% ---")

if __name__ == "__main__":
    test_user_persistence()
