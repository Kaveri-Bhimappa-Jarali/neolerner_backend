from typing import List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import schemas, models, database, dependencies

router = APIRouter(prefix="/api/progress", tags=["progress"])

@router.get("/me", response_model=List[schemas.LearningProgressResponse])
def get_my_learning_progress(
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    return db.query(models.LearningProgress).filter(models.LearningProgress.learner_id == current_learner.id).all()

@router.post("/lesson/{lesson_id}", response_model=schemas.LearningProgressResponse)
def update_lesson_progress(
    lesson_id: UUID,
    progress_update: schemas.LearningProgressUpdate,
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    progress = db.query(models.LearningProgress).filter(
        models.LearningProgress.learner_id == current_learner.id,
        models.LearningProgress.lesson_id == lesson_id
    ).first()

    if not progress:
        progress = models.LearningProgress(
            learner_id=current_learner.id,
            lesson_id=lesson_id,
            status=progress_update.status or models.ProgressStatus.in_progress,
            percentage_completed=progress_update.percentage_completed or 0.0,
            last_accessed=datetime.utcnow()
        )
        db.add(progress)
    else:
        if progress_update.status is not None:
            progress.status = progress_update.status
        if progress_update.percentage_completed is not None:
            progress.percentage_completed = progress_update.percentage_completed
        progress.last_accessed = datetime.utcnow()

    db.commit()
    db.refresh(progress)
    return progress
