import pytest
from fastapi.testclient import TestClient
import sys
import os
import uuid

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from main import app
from database import SessionLocal
import models

client = TestClient(app)

def test_registration_verification_flow():
    db = SessionLocal()
    unique_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPassword123!"

    # 1. Register new user
    reg_payload = {
        "email": unique_email,
        "password": password,
        "full_name": "Test Verified Learner",
        "age": 22,
        "preferred_language_code": "en",
        "target_language_code": "kn"
    }
    reg_resp = client.post("/api/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201, f"Registration failed: {reg_resp.text}"
    reg_data = reg_resp.json()
    assert reg_data["email"] == unique_email
    assert reg_data["is_verified"] is False
    assert reg_data["verification_code"] is not None
    assert len(reg_data["verification_code"]) == 6
    code = reg_data["verification_code"]

    # Verify user persists in DB
    db_user = db.query(models.Learner).filter(models.Learner.email == unique_email).first()
    assert db_user is not None
    assert db_user.is_verified is False

    # 2. Verify Email with 6-digit code
    verify_resp = client.post("/api/auth/verify-email", json={
        "email": unique_email,
        "code": code
    })
    assert verify_resp.status_code == 200, f"Verification failed: {verify_resp.text}"
    verify_data = verify_resp.json()
    assert "access_token" in verify_data
    token = verify_data["access_token"]

    # Verify user state in DB is now verified
    db.refresh(db_user)
    assert db_user.is_verified is True

    # 3. Access Diagnostic Initial Exam with token
    headers = {"Authorization": f"Bearer {token}"}
    diag_resp = client.post("/api/diagnostic/session", headers=headers)
    assert diag_resp.status_code == 200, f"Diagnostic failed with status {diag_resp.status_code}: {diag_resp.text}"
    diag_data = diag_resp.json()
    assert "questions" in diag_data

    # 4. Login with registered credentials
    login_resp = client.post("/api/auth/login", data={
        "username": unique_email,
        "password": password
    })
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    login_data = login_resp.json()
    assert "access_token" in login_data
