from typing import List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import schemas, models, database, dependencies, gamification

router = APIRouter(prefix="/api/progress", tags=["progress"])

@router.get("/me", response_model=List[schemas.LearningProgressResponse])
def get_my_learning_progress(
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    # Ensure hearts recharge check runs when retrieving progress
    gamification.recharge_hearts_by_time(current_learner, db)
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

    # Double check if user has at least 1 heart to start/complete a lesson
    gamification.recharge_hearts_by_time(current_learner, db)
    if current_learner.hearts <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="No hearts remaining. Recharge or practice to gain hearts."
        )

    progress = db.query(models.LearningProgress).filter(
        models.LearningProgress.learner_id == current_learner.id,
        models.LearningProgress.lesson_id == lesson_id
    ).first()

    newly_completed = False
    if not progress:
        status_val = progress_update.status or models.ProgressStatus.in_progress
        if status_val == models.ProgressStatus.completed:
            newly_completed = True
        progress = models.LearningProgress(
            learner_id=current_learner.id,
            lesson_id=lesson_id,
            status=status_val,
            percentage_completed=progress_update.percentage_completed or 0.0,
            last_accessed=datetime.utcnow()
        )
        db.add(progress)
    else:
        old_status = progress.status
        if progress_update.status is not None:
            progress.status = progress_update.status
            if progress_update.status == models.ProgressStatus.completed and old_status != models.ProgressStatus.completed:
                newly_completed = True
        if progress_update.percentage_completed is not None:
            progress.percentage_completed = progress_update.percentage_completed
        progress.last_accessed = datetime.utcnow()

    if newly_completed:
        gamification.award_xp_and_gems(current_learner, xp=10, gems=5, db=db)
        gamification.update_streak(current_learner, db=db)

    db.commit()
    db.refresh(progress)
    db.refresh(current_learner)
    return progress
