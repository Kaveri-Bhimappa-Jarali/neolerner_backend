from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import schemas, models, database, dependencies

router = APIRouter(prefix="/api/learners", tags=["learners"])

@router.get("/me", response_model=schemas.LearnerResponse)
def read_users_me(current_learner: models.Learner = Depends(dependencies.get_current_learner)):
    return current_learner

@router.put("/me", response_model=schemas.LearnerResponse)
def update_user_me(
    learner_update: schemas.LearnerUpdate, 
    current_learner: models.Learner = Depends(dependencies.get_current_learner), 
    db: Session = Depends(database.get_db)
):
    if learner_update.full_name is not None:
        current_learner.full_name = learner_update.full_name
    if learner_update.preferred_language_id is not None:
        current_learner.preferred_language_id = learner_update.preferred_language_id
    if learner_update.target_language_id is not None:
        current_learner.target_language_id = learner_update.target_language_id
    if learner_update.proficiency_level is not None:
        current_learner.proficiency_level = learner_update.proficiency_level

    db.commit()
    db.refresh(current_learner)
    return current_learner
