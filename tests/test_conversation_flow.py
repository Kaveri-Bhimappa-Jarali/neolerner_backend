import pytest
from fastapi.testclient import TestClient
import sys
import os

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from main import app
from database import get_db, SessionLocal
import models, auth

client = TestClient(app)

def test_conversation_endpoints():
    db = SessionLocal()
    # Create or get test learner
    test_email = "tutor_test_user@example.com"
    learner = db.query(models.Learner).filter(models.Learner.email == test_email).first()
    if not learner:
        lang = db.query(models.Language).first()
        learner = models.Learner(
            email=test_email,
            hashed_password=auth.get_password_hash("password123"),
            full_name="Tutor Test User",
            target_language_id=lang.id if lang else None
        )
        db.add(learner)
        db.commit()
        db.refresh(learner)

    token = auth.create_access_token(data={"sub": learner.email})
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Start conversation
    start_resp = client.post("/api/conversation/start", json={
        "scenario": "restaurant"
    }, headers=headers)
    assert start_resp.status_code == 200, f"Start failed: {start_resp.text}"
    start_data = start_resp.json()
    assert "session_id" in start_data
    session_id = start_data["session_id"]

    # 2. Respond to conversation
    respond_resp = client.post("/api/conversation/respond", json={
        "session_id": session_id,
        "user_transcript": "ನನಗೆ ಒಂದು ಮಸಾಲೆ ದೋಸೆ ಬೇಕು"
    }, headers=headers)
    assert respond_resp.status_code == 200, f"Respond failed: {respond_resp.text}"
    respond_data = respond_resp.json()
    assert "ai_reply" in respond_data
    assert respond_data["ai_reply"] != ""

    # 3. Respond second time
    respond_resp2 = client.post("/api/conversation/respond", json={
        "session_id": session_id,
        "user_transcript": "ಬಿಲ್ ಎಷ್ಟು?"
    }, headers=headers)
    assert respond_resp2.status_code == 200, f"Respond 2 failed: {respond_resp2.text}"

    # 4. End conversation
    end_resp = client.post("/api/conversation/end", json={
        "session_id": session_id
    }, headers=headers)
    assert end_resp.status_code == 200, f"End failed: {end_resp.text}"
    end_data = end_resp.json()
    assert end_data["total_turns"] >= 2
