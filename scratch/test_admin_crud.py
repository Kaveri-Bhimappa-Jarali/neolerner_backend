import sys
import os
sys.path.append(os.path.abspath("backend"))

from fastapi.testclient import TestClient
from main import app
import models, database, auth

client = TestClient(app)

def setup_admin_and_token():
    db = next(database.get_db())
    admin = db.query(models.Learner).filter(models.Learner.email == "admin_test_runner@lingua.com").first()
    if not admin:
        admin = models.Learner(
            email="admin_test_runner@lingua.com",
            hashed_password=auth.get_password_hash("admin123"),
            full_name="Admin Runner",
            is_admin=True,
            xp=1000
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
    token = auth.create_access_token({"sub": admin.email})
    return {"Authorization": f"Bearer {token}"}

def run_tests():
    headers = setup_admin_and_token()
    print("[TEST 1] Testing Learner CRUD...")
    # Create Learner
    res = client.post("/api/admin/learners", json={
        "email": "test_student_crud@example.com",
        "password": "secretpassword",
        "full_name": "Test Student CRUD",
        "age": 22,
        "is_admin": False,
        "proficiency_level": "Beginner",
        "cefr_level": "A1"
    }, headers=headers)
    assert res.status_code == 200, f"Create learner failed: {res.text}"
    learner_id = res.json()["id"]
    print(f" -> Created Learner ID: {learner_id}")

    # Update Learner
    res = client.put(f"/api/admin/learners/{learner_id}", json={
        "full_name": "Updated Student Name",
        "xp": 250,
        "gems": 999
    }, headers=headers)
    assert res.status_code == 200, f"Update learner failed: {res.text}"
    print(" -> Updated Learner successfully")

    # Delete Learner
    res = client.delete(f"/api/admin/learners/{learner_id}", headers=headers)
    assert res.status_code == 200, f"Delete learner failed: {res.text}"
    print(" -> Deleted Learner successfully")

    print("[TEST 2] Testing Universal Database Table Dynamic CRUD...")
    # Create Language via DB explorer endpoint
    res = client.post("/api/db/tables/languages", json={
        "name": "Sanskrit",
        "code": "sa_test",
        "native_name": "संस्कृतम्"
    })
    assert res.status_code == 200, f"Dynamic insert failed: {res.text}"
    lang_id = res.json()["id"]
    print(f" -> Dynamically Inserted Record ID: {lang_id}")

    # Update Language via DB explorer endpoint
    res = client.put(f"/api/db/tables/languages/{lang_id}", json={
        "native_name": "संस्कृतम् (Updated)"
    })
    assert res.status_code == 200, f"Dynamic update failed: {res.text}"
    print(" -> Dynamically Updated Record successfully")

    # Delete Language via DB explorer endpoint
    res = client.delete(f"/api/db/tables/languages/{lang_id}")
    assert res.status_code == 200, f"Dynamic delete failed: {res.text}"
    print(" -> Dynamically Deleted Record successfully")

    print("[TEST 3] Testing Achievement CRUD...")
    res = client.post("/api/admin/achievements", json={
        "code": "TEST_ACH_101",
        "name": "Test Master",
        "description": "Awarded for running test suite",
        "icon": "⚡",
        "category": "testing",
        "threshold": 1,
        "xp_reward": 100,
        "gem_reward": 50
    }, headers=headers)
    assert res.status_code == 200, f"Create achievement failed: {res.text}"
    ach_id = res.json()["id"]
    print(f" -> Created Achievement ID: {ach_id}")

    res = client.delete(f"/api/admin/achievements/{ach_id}", headers=headers)
    assert res.status_code == 200, f"Delete achievement failed: {res.text}"
    print(" -> Deleted Achievement successfully")

    print("=== ALL ADMIN CRUD ENDPOINTS VERIFIED SUCCESSFULLY ===")

if __name__ == "__main__":
    run_tests()
