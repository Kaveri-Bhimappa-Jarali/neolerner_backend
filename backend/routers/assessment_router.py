from typing import List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import schemas, models, database, dependencies, gamification

router = APIRouter(prefix="/api/assessments", tags=["assessments"])

@router.get("/lesson/{lesson_id}", response_model=List[schemas.AssessmentResponse])
def get_assessments_by_lesson(lesson_id: UUID, db: Session = Depends(database.get_db)):
    return db.query(models.Assessment).filter(models.Assessment.lesson_id == lesson_id).all()

@router.get("/{assessment_id}", response_model=schemas.AssessmentDetailResponse)
def get_assessment_detail(assessment_id: UUID, db: Session = Depends(database.get_db)):
    assessment = db.query(models.Assessment).filter(models.Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment

@router.post("/", response_model=schemas.AssessmentDetailResponse, status_code=status.HTTP_201_CREATED)
def create_assessment(assessment: schemas.AssessmentCreate, db: Session = Depends(database.get_db)):
    db_assessment = models.Assessment(
        lesson_id=assessment.lesson_id,
        title=assessment.title,
        type=assessment.type,
        pass_percentage=assessment.pass_percentage
    )
    db.add(db_assessment)
    db.commit()
    db.refresh(db_assessment)

    for q_data in assessment.questions:
        db_question = models.Question(
            assessment_id=db_assessment.id,
            text=q_data.text,
            type=q_data.type,
            points=q_data.points
        )
        db.add(db_question)
        db.commit()
        db.refresh(db_question)

        for a_data in q_data.answers:
            db_answer = models.Answer(
                question_id=db_question.id,
                text=a_data.text,
                is_correct=a_data.is_correct,
                explanation=a_data.explanation
            )
            db.add(db_answer)
        db.commit()

    db.refresh(db_assessment)
    return db_assessment

@router.post("/{assessment_id}/submit", response_model=schemas.AssessmentResultResponse)
def submit_assessment(
    assessment_id: UUID,
    submission: schemas.AssessmentSubmission,
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    assessment = db.query(models.Assessment).filter(models.Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # Double check if user has at least 1 heart to submit an assessment
    gamification.recharge_hearts_by_time(current_learner, db)
    if current_learner.hearts <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="No hearts remaining. Recharge or practice to gain hearts."
        )

    questions = db.query(models.Question).filter(models.Question.assessment_id == assessment_id).all()
    if not questions:
        raise HTTPException(status_code=400, detail="Assessment has no questions")

    total_points = sum(q.points for q in questions)
    earned_points = 0.0
    incorrect_count = 0

    submission_dict = {ans.question_id: ans.selected_answer_id for ans in submission.answers}

    for question in questions:
        selected_answer_id = submission_dict.get(question.id)
        is_correct = False
        if selected_answer_id:
            answer = db.query(models.Answer).filter(
                models.Answer.id == selected_answer_id,
                models.Answer.question_id == question.id
            ).first()
            if answer and answer.is_correct:
                earned_points += question.points
                is_correct = True
        if not is_correct:
            incorrect_count += 1
            # Add to mistakes tracking (ReviewItem)
            existing_review = db.query(models.ReviewItem).filter(
                models.ReviewItem.learner_id == current_learner.id,
                models.ReviewItem.question_id == question.id,
                models.ReviewItem.is_resolved == False
            ).first()
            if existing_review:
                existing_review.review_count += 1
                existing_review.created_at = datetime.utcnow()
            else:
                new_review = models.ReviewItem(
                    learner_id=current_learner.id,
                    question_id=question.id,
                    incorrect_answer=str(selected_answer_id) if selected_answer_id else None,
                    review_count=1,
                    is_resolved=False
                )
                db.add(new_review)

    score_percentage = (earned_points / total_points * 100.0) if total_points > 0 else 0.0
    passed = score_percentage >= assessment.pass_percentage

    # Deduct hearts if incorrect answers
    hearts_lost = incorrect_count
    if hearts_lost > 0:
        current_learner.hearts = max(0, current_learner.hearts - hearts_lost)
        db.commit()

    # Award XP and Gems on passing
    xp_earned = 0
    gems_earned = 0
    if passed:
        xp_earned += 20
        gems_earned += 10
        # Perfect score bonus!
        if hearts_lost == 0:
            xp_earned += 10
            gems_earned += 10
        
        gamification.award_xp_and_gems(current_learner, xp=xp_earned, gems=gems_earned, db=db)
        gamification.update_streak(current_learner, db=db)

    result = models.AssessmentResult(
        learner_id=current_learner.id,
        assessment_id=assessment.id,
        score=score_percentage,
        max_score=100.0,
        passed=passed
    )
    db.add(result)
    db.commit()
    db.refresh(result)

    # Attach dynamic gamification details to the result object for response serialization
    result.xp_earned = xp_earned
    result.gems_earned = gems_earned
    result.hearts_lost = hearts_lost
    result.current_hearts = current_learner.hearts

    return result

@router.get("/results/me", response_model=List[schemas.AssessmentResultResponse])
@router.get("/results/me/", response_model=List[schemas.AssessmentResultResponse])
def get_my_assessment_results(
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    return db.query(models.AssessmentResult).filter(models.AssessmentResult.learner_id == current_learner.id).all()
