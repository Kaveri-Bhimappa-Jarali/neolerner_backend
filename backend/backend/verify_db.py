import uuid
import sys
import os

# Adjust sys.path for backend imports
sys.path.append(os.path.dirname(__file__))

from database import SessionLocal, engine
from models import (
    Base, Language, Learner, Course, Topic, Lesson,
    Assessment, Question, Answer, AssessmentResult, LearningProgress, Recommendation,
    ProficiencyLevel, CourseLevel, ProgressStatus, AssessmentType, QuestionType
)

def run_verification():
    print("=== Starting Database Entity Verification ===")
    
    # 1. Ensure tables can be created
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("[OK] 1. Tables created successfully.")

    db = SessionLocal()
    try:
        # 2. Test Language
        lang_en = Language(id=uuid.uuid4(), name="English", code="en", native_name="English")
        lang_es = Language(id=uuid.uuid4(), name="Spanish", code="es", native_name="Español")
        db.add_all([lang_en, lang_es])
        db.commit()
        assert db.query(Language).count() == 2
        print("[OK] 2. Language entity verified.")

        # 3. Test Learner
        learner = Learner(
            id=uuid.uuid4(),
            email="testuser@test.com",
            hashed_password="securepasswordhash",
            full_name="Test Student",
            preferred_language_id=lang_en.id,
            target_language_id=lang_es.id,
            proficiency_level=ProficiencyLevel.Beginner
        )
        db.add(learner)
        db.commit()
        assert db.query(Learner).count() == 1
        print("[OK] 3. Learner entity verified.")

        # 4. Test Course
        course = Course(
            id=uuid.uuid4(),
            title="Elementary Spanish Literacy",
            description="Introductory literacy course",
            language_id=lang_es.id,
            level=CourseLevel.Beginner,
            is_published=True
        )
        db.add(course)
        db.commit()
        assert db.query(Course).count() == 1
        print("[OK] 4. Course entity verified.")

        # 5. Test Topic
        topic = Topic(
            id=uuid.uuid4(),
            course_id=course.id,
            title="Alphabet & Phonics",
            description="Learn the sounds of letters",
            order=1
        )
        db.add(topic)
        db.commit()
        assert db.query(Topic).count() == 1
        print("[OK] 5. Topic entity verified.")

        # 6. Test Lesson
        lesson = Lesson(
            id=uuid.uuid4(),
            topic_id=topic.id,
            title="Letter Sounds A-M",
            content="Lesson reading text content...",
            duration_minutes=20,
            order=1
        )
        db.add(lesson)
        db.commit()
        assert db.query(Lesson).count() == 1
        print("[OK] 6. Lesson entity verified.")

        # 7. Test Assessment
        assessment = Assessment(
            id=uuid.uuid4(),
            lesson_id=lesson.id,
            title="Phonics Mastery Test",
            type=AssessmentType.quiz,
            pass_percentage=75.0
        )
        db.add(assessment)
        db.commit()
        assert db.query(Assessment).count() == 1
        print("[OK] 7. Assessment entity verified.")

        # 8. Test Question
        question = Question(
            id=uuid.uuid4(),
            assessment_id=assessment.id,
            text="What sound does 'A' make?",
            type=QuestionType.multiple_choice,
            points=2
        )
        db.add(question)
        db.commit()
        assert db.query(Question).count() == 1
        print("[OK] 8. Question entity verified.")

        # 9. Test Answer
        answer1 = Answer(id=uuid.uuid4(), question_id=question.id, text="/ah/", is_correct=True, explanation="Short A sound")
        answer2 = Answer(id=uuid.uuid4(), question_id=question.id, text="/buh/", is_correct=False)
        db.add_all([answer1, answer2])
        db.commit()
        assert db.query(Answer).count() == 2
        print("[OK] 9. Answer entity verified.")

        # 10. Test AssessmentResult
        result = AssessmentResult(
            id=uuid.uuid4(),
            learner_id=learner.id,
            assessment_id=assessment.id,
            score=100.0,
            max_score=100.0,
            passed=True
        )
        db.add(result)
        db.commit()
        assert db.query(AssessmentResult).count() == 1
        print("[OK] 10. AssessmentResult entity verified.")

        # 11. Test LearningProgress
        progress = LearningProgress(
            id=uuid.uuid4(),
            learner_id=learner.id,
            lesson_id=lesson.id,
            status=ProgressStatus.completed,
            percentage_completed=100.0
        )
        db.add(progress)
        db.commit()
        assert db.query(LearningProgress).count() == 1
        print("[OK] 11. LearningProgress entity verified.")

        # 12. Test Recommendation
        recommendation = Recommendation(
            id=uuid.uuid4(),
            learner_id=learner.id,
            recommended_course_id=course.id,
            reason="Based on beginner status in Spanish",
            priority=1
        )
        db.add(recommendation)
        db.commit()
        assert db.query(Recommendation).count() == 1
        print("[OK] 12. Recommendation entity verified.")

        # 13. Test Relationships and Cascades
        fetched_course = db.query(Course).filter(Course.id == course.id).first()
        assert len(fetched_course.topics) == 1
        assert len(fetched_course.topics[0].lessons) == 1
        assert len(fetched_course.topics[0].lessons[0].assessments) == 1
        assert len(fetched_course.topics[0].lessons[0].assessments[0].questions) == 1
        assert len(fetched_course.topics[0].lessons[0].assessments[0].questions[0].answers) == 2
        print("[OK] 13. Hierarchical relationship tree navigation verified.")

        print("=== ALL 11 ENTITIES VERIFIED SUCCESSFULLY ===")

    except Exception as e:
        print(f"[FAIL] Verification failed: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    run_verification()
