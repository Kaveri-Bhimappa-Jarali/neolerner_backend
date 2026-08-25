import uuid
import sys
import os
from datetime import datetime

# Adjust sys.path to allow importing backend modules
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from backend.database import SessionLocal, engine
from backend.models import (
    Base, Language, Learner, Course, Topic, Lesson,
    Assessment, Question, Answer, AssessmentResult, LearningProgress, Recommendation,
    ProficiencyLevel, CourseLevel, ProgressStatus, AssessmentType, QuestionType
)
from backend.auth import get_password_hash

def seed_database():
    print("Recreating database tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        print("Seeding Languages...")
        languages_data = [
            {"name": "English", "code": "en", "native_name": "English"},
            {"name": "Spanish", "code": "es", "native_name": "Español"},
            {"name": "French", "code": "fr", "native_name": "Français"},
            {"name": "German", "code": "de", "native_name": "Deutsch"},
            {"name": "Japanese", "code": "ja", "native_name": "日本語"}
        ]
        lang_map = {}
        for l in languages_data:
            lang = Language(id=uuid.uuid4(), name=l["name"], code=l["code"], native_name=l["native_name"])
            db.add(lang)
            lang_map[l["code"]] = lang
        db.commit()

        print("Seeding Learner...")
        learner = Learner(
            id=uuid.uuid4(),
            email="learner@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Maria Rodriguez",
            preferred_language_id=lang_map["en"].id,
            target_language_id=lang_map["es"].id,
            proficiency_level=ProficiencyLevel.Beginner
        )
        db.add(learner)
        db.commit()
        db.refresh(learner)

        print("Seeding Course, Topics & Lessons...")
        course = Course(
            id=uuid.uuid4(),
            title="Spanish Literacy Foundations",
            description="Master elementary Spanish reading, phonics, and conversational basics.",
            language_id=lang_map["es"].id,
            level=CourseLevel.Beginner,
            thumbnail_url="https://images.unsplash.com/photo-1543783207-ec64e4d95325",
            is_published=True
        )
        db.add(course)
        db.commit()

        topic1 = Topic(
            id=uuid.uuid4(),
            course_id=course.id,
            title="Vowels & Basic Sounds",
            description="Introduction to Spanish vowel pronunciation and sounds.",
            order=1
        )
        db.add(topic1)
        db.commit()

        lesson1 = Lesson(
            id=uuid.uuid4(),
            topic_id=topic1.id,
            title="Pronouncing Spanish Vowels (A, E, I, O, U)",
            content="# Spanish Vowels\nUnlike English, Spanish vowels always maintain consistent sounds:\n- A as in *father*\n- E as in *get*\n- I as in *machine*\n- O as in *go*\n- U as in *rule*",
            duration_minutes=15,
            order=1
        )
        db.add(lesson1)
        db.commit()

        print("Seeding Assessment, Questions & Answers...")
        assessment = Assessment(
            id=uuid.uuid4(),
            lesson_id=lesson1.id,
            title="Spanish Vowel Pronunciation Quiz",
            type=AssessmentType.quiz,
            pass_percentage=70.0
        )
        db.add(assessment)
        db.commit()

        q1 = Question(
            id=uuid.uuid4(),
            assessment_id=assessment.id,
            text="How is the Spanish vowel 'E' pronounced?",
            type=QuestionType.multiple_choice,
            points=1
        )
        db.add(q1)
        db.commit()

        a1_1 = Answer(id=uuid.uuid4(), question_id=q1.id, text="Like 'e' in 'get'", is_correct=True, explanation="Correct! E sounds like 'get' in English.")
        a1_2 = Answer(id=uuid.uuid4(), question_id=q1.id, text="Like 'ee' in 'see'", is_correct=False, explanation="Incorrect. That is the sound for Spanish 'I'.")
        a1_3 = Answer(id=uuid.uuid4(), question_id=q1.id, text="Like 'ay' in 'say'", is_correct=False)
        db.add_all([a1_1, a1_2, a1_3])
        db.commit()

        print("Seeding Assessment Result...")
        res = AssessmentResult(
            id=uuid.uuid4(),
            learner_id=learner.id,
            assessment_id=assessment.id,
            score=100.0,
            max_score=100.0,
            passed=True
        )
        db.add(res)

        print("Seeding Learning Progress...")
        prog = LearningProgress(
            id=uuid.uuid4(),
            learner_id=learner.id,
            lesson_id=lesson1.id,
            status=ProgressStatus.completed,
            percentage_completed=100.0
        )
        db.add(prog)

        print("Seeding Recommendation...")
        rec = Recommendation(
            id=uuid.uuid4(),
            learner_id=learner.id,
            recommended_course_id=course.id,
            reason="Recommended based on your target language preference (Spanish).",
            priority=1
        )
        db.add(rec)

        db.commit()
        print("Database seeded successfully with all 11 entities!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
