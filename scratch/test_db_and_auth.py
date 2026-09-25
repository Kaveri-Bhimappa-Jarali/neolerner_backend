import sys
import os

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import SessionLocal, engine, Base
import models, auth, schemas
from routers.auth_router import register
from routers.admin_router import get_admin_learners_list
from uuid import uuid4

def run_tests():
    print("=== STARTING DATABASE AND REGISTRATION VERIFICATION TESTS ===")
    db = SessionLocal()
    try:
        # Test 1: Register standard learner
        test_learner_email = f"testlearner_{uuid4().hex[:6]}@example.com"
        learner_data = schemas.LearnerCreate(
            email=test_learner_email,
            password="TestPassword123!",
            full_name="Test Learner User",
            age=22,
            is_admin=False
        )
        reg_learner = register(learner=learner_data, db=db)
        print(f"[PASS] Standard Learner Registered:")
        print(f"       Email: {reg_learner.email}")
        print(f"       is_verified: {reg_learner.is_verified}")
        print(f"       verification_code: {reg_learner.verification_code}")
        
        assert reg_learner.is_verified == False, "Standard learner should be unverified upon registration"
        assert reg_learner.verification_code is not None and len(reg_learner.verification_code) == 6, "Standard learner should have a 6-digit verification code"

        # Test 2: Register Admin user
        test_admin_email = f"admin_{uuid4().hex[:6]}@neolearner.com"
        admin_data = schemas.LearnerCreate(
            email=test_admin_email,
            password="AdminPassword123!",
            full_name="Test Admin User",
            age=30,
            is_admin=True
        )
        reg_admin = register(learner=admin_data, db=db)
        print(f"[PASS] Admin User Registered:")
        print(f"       Email: {reg_admin.email}")
        print(f"       is_verified: {reg_admin.is_verified}")
        print(f"       verification_code: {reg_admin.verification_code}")

        assert reg_admin.is_verified == True, "Admin user should be automatically verified upon registration"
        assert reg_admin.verification_code is None, "Admin user should NOT have a verification code"

        # Test 3: Query Admin Learners List endpoint logic
        admin_obj = db.query(models.Learner).filter(models.Learner.is_admin == True).first()
        learners_list = get_admin_learners_list(q=None, level=None, current_admin=admin_obj, db=db)
        
        found_learner = next((l for l in learners_list if l.email == test_learner_email), None)
        found_admin = next((l for l in learners_list if l.email == test_admin_email), None)

        assert found_learner is not None, "Registered learner must appear in Admin Learners List"
        assert found_learner.is_verified == False, "Admin Learners List must reflect is_verified=False"
        assert found_learner.verification_code == reg_learner.verification_code, "Admin Learners List must expose verification_code"

        assert found_admin is not None, "Registered admin must appear in Admin Learners List"
        assert found_admin.is_verified == True, "Admin Learners List must reflect is_verified=True for admin"
        assert found_admin.verification_code is None, "Admin Learners List must show verification_code=None for admin"

        print(f"[PASS] Admin Panel API returns correct learner verification details!")
        print("=== ALL TESTS PASSED SUCCESSFULLY ===")

    except Exception as e:
        print(f"[FAIL] Test execution error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    run_tests()
