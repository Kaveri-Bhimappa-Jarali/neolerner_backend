from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import schemas, models, database, dependencies, ai_engine

from uuid import UUID

router = APIRouter(prefix="/api/learning-paths", tags=["learning_paths"])

@router.get("/me", response_model=schemas.LearningPathResponse)
@router.get("/me/", response_model=schemas.LearningPathResponse)
def get_my_learning_path(
    course_id: Optional[UUID] = Query(None),
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    """
    Get the personalized DAG learning path for the authenticated learner's target course.
    """
    return ai_engine.generate_learning_path(current_learner.id, db, course_id=course_id)

@router.get("/prediction", response_model=schemas.ProficiencyPredictionResponse)
@router.get("/prediction/", response_model=schemas.ProficiencyPredictionResponse)
def get_my_proficiency_prediction(
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    """
    Learner Proficiency Prediction: Returns multi-skill competency scores and benchmark classification.
    """
    return ai_engine.calculate_predicted_proficiency(current_learner.id, db)

@router.get("/recommendations", response_model=List[schemas.AIRecommendationItem])
@router.get("/recommendations/", response_model=List[schemas.AIRecommendationItem])
def get_my_ai_recommendations(
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    """
    Adaptive Learning Recommendations: Returns prioritized, context-aware remedial & next-step actions.
    """
    return ai_engine.generate_ai_recommendations(current_learner.id, db)

@router.post("/adaptive-lesson", response_model=schemas.AdaptiveLessonResponse)
@router.post("/adaptive-lesson/", response_model=schemas.AdaptiveLessonResponse)
def generate_adaptive_lesson_session(
    focus: Optional[str] = Query(None, description="Focus competency: mistakes, reading, writing, comprehension, listening, speaking"),
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    """
    Personalized Lesson Generator: Synthesizes an on-the-fly remedial or booster workout tailored to weak skills.
    """
    return ai_engine.generate_adaptive_lesson(current_learner.id, focus, db)

@router.post("/adaptive-lesson/submit", response_model=schemas.AssessmentResultResponse)
@router.post("/adaptive-lesson/submit/", response_model=schemas.AssessmentResultResponse)
def submit_adaptive_lesson_session(
    submission: schemas.AdaptiveLessonSubmit,
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    """
    Processes completed adaptive lesson, resolves mistake tracking, awards XP/Gems, and recalculates proficiency.
    """
    return ai_engine.process_adaptive_lesson_submission(current_learner.id, submission, db)
