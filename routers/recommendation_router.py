from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import schemas, models, database, dependencies

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])

@router.get("/me", response_model=List[schemas.RecommendationResponse])
def get_my_recommendations(
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    return db.query(models.Recommendation).filter(
        models.Recommendation.learner_id == current_learner.id
    ).order_by(models.Recommendation.priority.asc()).all()

@router.post("/", response_model=schemas.RecommendationResponse, status_code=status.HTTP_201_CREATED)
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
