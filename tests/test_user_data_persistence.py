import pytest
from fastapi.testclient import TestClient
import sys
import os
import uuid

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from main import app
import database
from database import SessionLocal
import models
import auth

client = TestClient(app)

def test_1_registration_persistence():
    """Test 1: Verify user registration persists in database across sessions."""
    db = SessionLocal()
    email = f"persist_user_{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePassword123!"

    # 1. Register
    reg_res = client.post("/api/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Persistence Tester 1",
        "preferred_language_code": "en",
        "target_language_code": "kn"
    })
    assert reg_res.status_code == 201, f"Registration failed: {reg_res.text}"

    # 2. Verify direct database record
    db_user = db.query(models.Learner).filter(models.Learner.email == email).first()
    assert db_user is not None
    assert db_user.email == email

    # 3. Simulate backend restart (closing DB session & creating new connection)
    db.close()
    new_db = SessionLocal()
    persisted_user = new_db.query(models.Learner).filter(models.Learner.email == email).first()
    assert persisted_user is not None
    assert persisted_user.full_name == "Persistence Tester 1"
    new_db.close()


def test_2_login_persistence():
    """Test 2: Verify registered user can authenticate after app restart."""
    email = f"login_persist_{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePassword123!"

    # Register
    reg_res = client.post("/api/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Login Persistence User",
        "preferred_language_code": "en",
        "target_language_code": "kn"
    })
    assert reg_res.status_code == 201

    # Simulate app close/reopen by making fresh login request
    login_res = client.post("/api/auth/login", data={
        "username": email,
        "password": password
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    login_data = login_res.json()
    assert "access_token" in login_data

    # Fetch user details via /api/learners/me
    token = login_data["access_token"]
    me_res = client.get("/api/learners/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == email


def test_3_refresh_and_activity_persistence():
    """Test 3: User activity (profile updates, goals, preferences) survives browser refresh / API reload."""
    email = f"activity_persist_{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePassword123!"

    # Register & Login
    client.post("/api/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Activity User"
    })
    login_res = client.post("/api/auth/login", data={"username": email, "password": password})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Perform profile update activity
    update_res = client.put("/api/learners/me", json={
        "full_name": "Updated Activity User Name",
        "daily_minutes_goal": 30,
        "learning_goal": "career"
    }, headers=headers)
    assert update_res.status_code == 200
    assert update_res.json()["full_name"] == "Updated Activity User Name"
    assert update_res.json()["daily_minutes_goal"] == 30

    # Simulate page refresh by fetching /api/learners/me directly from DB
    refresh_res = client.get("/api/learners/me", headers=headers)
    assert refresh_res.status_code == 200
    assert refresh_res.json()["full_name"] == "Updated Activity User Name"
    assert refresh_res.json()["daily_minutes_goal"] == 30
    assert refresh_res.json()["learning_goal"] == "career"


def test_4_logout_and_relogin_persistence():
    """Test 4: Logging out does NOT delete user data; logging back in restores all state."""
    email = f"logout_persist_{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePassword123!"

    # Register
    client.post("/api/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Logout Test User"
    })
    login_res = client.post("/api/auth/login", data={"username": email, "password": password})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Update profile & set goal
    client.put("/api/learners/me", json={"learning_goal": "travel", "daily_minutes_goal": 45}, headers=headers)

    # Logout (client removes token) -> simulate by clearing headers
    # Re-login to get fresh token
    login_again = client.post("/api/auth/login", data={"username": email, "password": password})
    new_token = login_again.json()["access_token"]
    new_headers = {"Authorization": f"Bearer {new_token}"}

    # Verify user state is completely intact
    me_res = client.get("/api/learners/me", headers=new_headers)
    assert me_res.status_code == 200
    assert me_res.json()["learning_goal"] == "travel"
    assert me_res.json()["daily_minutes_goal"] == 45


def test_5_multiple_users_data_isolation():
    """Test 5: User A and User B data are strictly isolated and cannot leak to each other."""
    email_a = f"usera_{uuid.uuid4().hex[:8]}@example.com"
    email_b = f"userb_{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePassword123!"

    # Register User A & User B
    client.post("/api/auth/register", json={"email": email_a, "password": password, "full_name": "User A"})
    client.post("/api/auth/register", json={"email": email_b, "password": password, "full_name": "User B"})

    token_a = client.post("/api/auth/login", data={"username": email_a, "password": password}).json()["access_token"]
    token_b = client.post("/api/auth/login", data={"username": email_b, "password": password}).json()["access_token"]

    # User A updates profile with custom goal
    headers_a = {"Authorization": f"Bearer {token_a}"}
    client.put("/api/learners/me", json={"learning_goal": "culture_mastery"}, headers=headers_a)

    headers_b = {"Authorization": f"Bearer {token_b}"}

    user_a_res = client.get("/api/learners/me", headers=headers_a).json()
    user_b_res = client.get("/api/learners/me", headers=headers_b).json()

    assert user_a_res["email"] == email_a
    assert user_b_res["email"] == email_b
    assert user_a_res["learning_goal"] == "culture_mastery"
    assert user_b_res["learning_goal"] == "conversation"

    # Requesting without token must return 401 Unauthorized
    unauth_res = client.get("/api/learners/me")
    assert unauth_res.status_code == 401


def test_6_explicit_account_deletion():
    """Test 6: User data persists until explicit account deletion is requested."""
    email = f"delete_me_{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePassword123!"

    # Register & Login
    client.post("/api/auth/register", json={"email": email, "password": password, "full_name": "Delete Me"})
    token = client.post("/api/auth/login", data={"username": email, "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify user exists
    assert client.get("/api/learners/me", headers=headers).status_code == 200

    # Explicitly call DELETE /api/learners/me
    del_res = client.delete("/api/learners/me", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"

    # Subsequent login must fail as account no longer exists
    login_again = client.post("/api/auth/login", data={"username": email, "password": password})
    assert login_again.status_code == 401
