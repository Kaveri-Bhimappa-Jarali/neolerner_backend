import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import uuid
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_language_pairs():
    r = client.get("/api/languages/")
    languages = r.json()
    lang_by_code = {l["code"]: l for l in languages}

    pairs_to_test = [
        ("kn", "en", "Kannada -> English"),
        ("te", "en", "Telugu -> English"),
        ("mr", "en", "Marathi -> English"),
        ("hi", "en", "Hindi -> English"),
        ("en", "kn", "English -> Kannada"),
        ("en", "te", "English -> Telugu"),
        ("en", "mr", "English -> Marathi"),
        ("en", "hi", "English -> Hindi"),
    ]

    for pref_code, targ_code, desc in pairs_to_test:
        uid = uuid.uuid4().hex[:5]
        email = f"pair_{pref_code}_{targ_code}_{uid}@test.com"
        
        # Register
        r = client.post("/api/auth/register", json={
            "email": email, "full_name": f"Tester {desc}", "password": "password123", "age": 25
        })
        assert r.status_code == 201

        # Login
        r = client.post("/api/auth/login", data={"username": email, "password": "password123"})
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Onboard
        r = client.put("/api/learners/me", json={
            "preferred_language_id": lang_by_code[pref_code]["id"],
            "target_language_id": lang_by_code[targ_code]["id"],
            "prior_knowledge": "beginner",
            "learning_goal": "conversation",
            "daily_minutes_goal": 15
        }, headers=headers)
        assert r.status_code == 200

        # Generate diagnostic session
        r = client.post("/api/diagnostic/session", headers=headers)
        assert r.status_code == 200, f"Failed for {desc}: {r.text}"
        session_data = r.json()
        assert len(session_data["questions"]) == 15
        print(f"✓ Verified Language Pair [{desc}]: 15 diagnostic questions successfully generated.")

    print("\n🎉 ALL 8 LANGUAGE PAIRS VERIFIED WITH ZERO ERRORS!")

if __name__ == "__main__":
    test_language_pairs()
