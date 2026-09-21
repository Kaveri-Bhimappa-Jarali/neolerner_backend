from typing import List
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import schemas, models, database, dependencies, gamification, srs

router = APIRouter(prefix="/api/reviews", tags=["reviews"])

@router.get("/srs", response_model=List[schemas.VocabularySRSResponse])
def get_due_srs_items(
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    gamification.recharge_hearts_by_time(current_learner, db)
    # Get all vocab items that are due (next_review_date <= now)
    now = datetime.utcnow()
    due_items = db.query(models.VocabularySRS).filter(
        models.VocabularySRS.learner_id == current_learner.id,
        models.VocabularySRS.next_review_date <= now
    ).all()
    
    # If no items are due, we can return some review items that were studied recently
    # or just return empty list so the frontend knows there's no urgent review.
    # To make the user experience better, if there are absolutely no items in SRS,
    # let's auto-populate the user's SRS list with some vocabulary from their target language!
    if not due_items and current_learner.target_language_id:
        # Check if they have ANY srs items
        total_srs_count = db.query(models.VocabularySRS).filter(
            models.VocabularySRS.learner_id == current_learner.id
        ).count()
        
        if total_srs_count == 0:
            # Seed 5 vocabulary words from their target language
            vocab_pool = db.query(models.Vocabulary).filter(
                models.Vocabulary.language_id == current_learner.target_language_id
            ).limit(5).all()
            
            for vocab in vocab_pool:
                new_srs = models.VocabularySRS(
                    learner_id=current_learner.id,
                    vocabulary_id=vocab.id,
                    interval=1,
                    ease_factor=2.5,
                    repetitions=0,
                    next_review_date=datetime.utcnow()
                )
                db.add(new_srs)
            db.commit()
            
            due_items = db.query(models.VocabularySRS).filter(
                models.VocabularySRS.learner_id == current_learner.id
            ).all()
            
    return due_items

@router.post("/srs/submit", response_model=schemas.VocabularySRSResponse)
def submit_srs_review(
    review_submit: schemas.SRSReviewSubmit,
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    item = db.query(models.VocabularySRS).filter(
        models.VocabularySRS.id == review_submit.vocabulary_srs_id,
        models.VocabularySRS.learner_id == current_learner.id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="SRS vocabulary item not found")
        
    # Calculate new values using SM-2
    new_interval, new_ease_factor, new_repetitions = srs.calculate_sm2(
        interval=item.interval,
        ease_factor=item.ease_factor,
        repetitions=item.repetitions,
        quality=review_submit.quality
    )
    
    item.interval = new_interval
    item.ease_factor = new_ease_factor
    item.repetitions = new_repetitions
    item.last_reviewed_at = datetime.utcnow()
    item.next_review_date = datetime.utcnow() + timedelta(days=new_interval)
    
    # Award gamification rewards: 2 XP per correct review (quality >= 3)
    xp_earned = 0
    if review_submit.quality >= 3:
        xp_earned = 2
        gamification.award_xp_and_gems(current_learner, xp=xp_earned, gems=0, db=db)
        gamification.update_streak(current_learner, db=db)
        
    db.commit()
    db.refresh(item)
    return item

@router.get("/mistakes", response_model=List[schemas.ReviewItemResponse])
def get_mistakes(
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    gamification.recharge_hearts_by_time(current_learner, db)
    return db.query(models.ReviewItem).filter(
        models.ReviewItem.learner_id == current_learner.id,
        models.ReviewItem.is_resolved == False
    ).all()

@router.post("/mistakes/submit", response_model=schemas.ReviewItemResponse)
def submit_mistake_practice(
    submit_data: schemas.ReviewItemSubmit,
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    # Find the mistake item for this learner and question
    mistake = db.query(models.ReviewItem).filter(
        models.ReviewItem.learner_id == current_learner.id,
        models.ReviewItem.question_id == submit_data.question_id,
        models.ReviewItem.is_resolved == False
    ).first()
    
    if not mistake:
        # User is practicing a question that wasn't in their mistakes, or was resolved
        # Let's create a temporary mistake object to return, or error.
        # Let's see: to be safe, if it's already resolved or doesn't exist, we can raise 404
        raise HTTPException(status_code=404, detail="Mistake review item not found or already resolved")
        
    if submit_data.is_correct:
        mistake.is_resolved = True
        mistake.resolved_at = datetime.utcnow()
        
        # Award 2 XP for correct practice and recharge 1 Heart (max 5)
        gamification.award_xp_and_gems(current_learner, xp=2, gems=0, db=db)
        if current_learner.hearts < 5:
            current_learner.hearts += 1
            
        gamification.update_streak(current_learner, db=db)
    else:
        # Increment review count and keep unresolved
        mistake.review_count += 1
        
    db.commit()
    db.refresh(mistake)
    db.refresh(current_learner)
    return mistake
