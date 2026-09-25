import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from database import SessionLocal
import models
import ai_engine

db = SessionLocal()
try:
    learner = db.query(models.Learner).first()
    if not learner:
        print("No learner found in DB!")
    else:
        print(f"Testing placement session for learner: {learner.id} ({learner.email})")
        session = ai_engine.generate_placement_test_session(learner.id, db)
        print(f"SUCCESS! Session ID: {session.session_id}, Total Questions: {session.total_questions}")
except Exception as e:
    import traceback
    print("ERROR generating placement session:")
    traceback.print_exc()
finally:
    db.close()
