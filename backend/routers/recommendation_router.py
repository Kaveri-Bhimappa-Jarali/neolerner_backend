from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import schemas, models, database, dependencies
from recommendation_engine import default_recommendation_engine, DEFAULT_PROFICIENCY_BANDS, DEFAULT_ENGINE_WEIGHTS

router = APIRouter(tags=["recommendations"])

# Admin/Runtime mutable config storage
CONFIG_BANDS = list(DEFAULT_PROFICIENCY_BANDS)
CONFIG_WEIGHTS = dict(DEFAULT_ENGINE_WEIGHTS)

@router.get("/api/learning/recommendations", response_model=schemas.CourseRecommendationResponse)
@router.get("/api/learning/recommendations/", response_model=schemas.CourseRecommendationResponse)
@router.get("/api/recommendations/courses", response_model=schemas.CourseRecommendationResponse)
def get_adaptive_course_recommendations(
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    """
    Dedicated Adaptive Course Recommendation Engine:
    Ranks available courses based on overall score, CEFR band, weak-skill inverse priority,
    learning goal match, prerequisite status, and calculates starting topic/unit placement.
    """
    engine = default_recommendation_engine
    engine.bands = CONFIG_BANDS
    engine.weights = CONFIG_WEIGHTS
    return engine.rank_courses_for_learner(current_learner, db)

@router.get("/api/recommendations/me", response_model=List[schemas.RecommendationResponse])
def get_my_legacy_recommendations(
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    return db.query(models.Recommendation).filter(
        models.Recommendation.learner_id == current_learner.id
    ).order_by(models.Recommendation.priority.asc()).all()

@router.get("/api/recommendations/bands")
def get_proficiency_bands_config():
    """
    Returns configurable score-to-level mapping bands and engine weights.
    """
    return {
        "bands": CONFIG_BANDS,
        "weights": CONFIG_WEIGHTS
    }

@router.put("/api/recommendations/bands")
def update_proficiency_bands_config(
    payload: Dict[str, Any],
    current_learner: models.Learner = Depends(dependencies.get_current_learner)
):
    """
    Update configurable proficiency bands and engine weighting factors (Admin/Config capability).
    """
    global CONFIG_BANDS, CONFIG_WEIGHTS
    if "bands" in payload and isinstance(payload["bands"], list):
        CONFIG_BANDS = payload["bands"]
    if "weights" in payload and isinstance(payload["weights"], dict):
        CONFIG_WEIGHTS.update(payload["weights"])
    return {
        "message": "Proficiency bands and recommendation weights updated successfully.",
        "bands": CONFIG_BANDS,
        "weights": CONFIG_WEIGHTS
    }

@router.post("/api/recommendations/reevaluate", response_model=schemas.CourseRecommendationResponse)
def reevaluate_recommendations(
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    """
    Forces dynamic re-evaluation and re-ranking of recommended courses for the learner.
    """
    engine = default_recommendation_engine
    engine.bands = CONFIG_BANDS
    engine.weights = CONFIG_WEIGHTS
    return engine.rank_courses_for_learner(current_learner, db)

@router.post("/api/recommendations/", response_model=schemas.RecommendationResponse, status_code=status.HTTP_201_CREATED)
def create_recommendation(
    rec: schemas.RecommendationCreate,
    db: Session = Depends(database.get_db)
):
    learner = db.query(models.Learner).filter(models.Learner.id == rec.learner_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    course = db.query(models.Course).filter(models.Course.id == rec.recommended_course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Recommended course not found")

    db_rec = models.Recommendation(**rec.model_dump())
    db.add(db_rec)
    db.commit()
    db.refresh(db_rec)
    return db_rec
