from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import schemas, models, database, dependencies

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

    questions = db.query(models.Question).filter(models.Question.assessment_id == assessment_id).all()
    if not questions:
        raise HTTPException(status_code=400, detail="Assessment has no questions")

    total_points = sum(q.points for q in questions)
    earned_points = 0.0

    submission_dict = {ans.question_id: ans.selected_answer_id for ans in submission.answers}

    for question in questions:
        selected_answer_id = submission_dict.get(question.id)
        if selected_answer_id:
            answer = db.query(models.Answer).filter(
                models.Answer.id == selected_answer_id,
                models.Answer.question_id == question.id
            ).first()
            if answer and answer.is_correct:
                earned_points += question.points

    score_percentage = (earned_points / total_points * 100.0) if total_points > 0 else 0.0
    passed = score_percentage >= assessment.pass_percentage

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
    return result

@router.get("/results/me", response_model=List[schemas.AssessmentResultResponse])
def get_my_assessment_results(
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    return db.query(models.AssessmentResult).filter(models.AssessmentResult.learner_id == current_learner.id).all()
