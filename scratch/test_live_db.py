import os
import sys
import uuid

# Add backend directory to sys.path
backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import database
import models
from sqlalchemy import text

def test_database_connection_and_crud():
    print("=" * 60)
    print("DATABASE TEST SUITE RUNNER")
    print("=" * 60)

    # 1. Print Engine & DB URL Info
    db_url = database.SQLALCHEMY_DATABASE_URL
    print(f"[1] SQLALCHEMY_DATABASE_URL: {db_url}")
    print(f"[2] Resolved DB Path: {database.DB_PATH}")
    print(f"[3] Engine dialect: {database.engine.name}")
    assert database.engine is not None, "Database engine failed to instantiate"

    # 2. Test get_db session generator & table creation
    print("\n[STEP 1] Ensuring tables exist and getting Session...")
    database.ensure_tables_created()

    db_generator = database.get_db()
    db = next(db_generator)
    print("[OK] Session created successfully.")

    try:
        # 3. Verify Table Mappings & Record Counts
        print("\n[STEP 2] Verifying core database tables...")
        table_counts = {
            "languages": db.query(models.Language).count(),
            "learners": db.query(models.Learner).count(),
            "courses": db.query(models.Course).count(),
            "topics": db.query(models.Topic).count(),
            "lessons": db.query(models.Lesson).count(),
            "vocabulary": db.query(models.Vocabulary).count(),
            "assessments": db.query(models.Assessment).count(),
        }
        for table_name, count in table_counts.items():
            print(f"  • Table '{table_name}': {count} records")

        # 4. Perform CRUD Test on Learner Table
        print("\n[STEP 3] Testing Live CRUD Transaction (Create, Read, Update, Delete)...")
        test_email = f"dbtest_{uuid.uuid4().hex[:8]}@example.com"
        
        # Create
        new_learner = models.Learner(
            id=uuid.uuid4(),
            email=test_email,
            hashed_password="testpasswordhash123",
            full_name="DB Test User",
            is_verified=True,
            cefr_level="A1",
            xp=100,
            gems=500
        )
        db.add(new_learner)
        db.commit()
        db.refresh(new_learner)
        created_id = new_learner.id
        print(f"  [CREATE OK] Created test learner ID: {created_id} with email {test_email}")

        # Read
        fetched = db.query(models.Learner).filter(models.Learner.id == created_id).first()
        assert fetched is not None, "Failed to retrieve created record"
        assert fetched.email == test_email, "Email mismatch on read"
        print(f"  [READ OK] Successfully queried record from DB. Full name: {fetched.full_name}")

        # Update
        fetched.full_name = "DB Test User Updated"
        fetched.xp = 250
        db.commit()
        db.refresh(fetched)
        assert fetched.full_name == "DB Test User Updated"
        assert fetched.xp == 250
        print(f"  [UPDATE OK] Updated record attributes in DB. XP: {fetched.xp}")

        # Delete
        db.delete(fetched)
        db.commit()
        deleted_check = db.query(models.Learner).filter(models.Learner.id == created_id).first()
        assert deleted_check is None, "Record was not deleted from DB"
        print(f"  [DELETE OK] Successfully deleted test record from DB.")

        print("\n" + "=" * 60)
        print("ALL DATABASE TESTS PASSED CLEANLY! DB IS FULLY OPERATIONAL.")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Database test failed: {e}")
        raise e
    finally:
        try:
            next(db_generator)
        except StopIteration:
            pass

if __name__ == "__main__":
    test_database_connection_and_crud()
