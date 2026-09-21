import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import schemas, models, database, dependencies, ai_engine

router = APIRouter(prefix="/api/diagnostic", tags=["diagnostic_placement"])

@router.get("/status")
def get_diagnostic_status(
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    """
    Returns whether the learner has completed the initial adaptive placement diagnostic test,
    including CEFR level, skill breakdown, strengths, weak areas, and learning preferences.
    """
    latest_placement = db.query(models.AssessmentResult).filter(
        models.AssessmentResult.learner_id == current_learner.id,
        models.AssessmentResult.assessment_id.is_(None)
    ).order_by(models.AssessmentResult.completed_at.desc()).first()

    skill_breakdown = {}
    strengths = []
    weak_areas = []
    if latest_placement:
        try:
            if latest_placement.skill_breakdown:
                skill_breakdown = json.loads(latest_placement.skill_breakdown) if isinstance(latest_placement.skill_breakdown, str) else latest_placement.skill_breakdown
            if latest_placement.strengths:
                strengths = json.loads(latest_placement.strengths) if isinstance(latest_placement.strengths, str) else latest_placement.strengths
            if latest_placement.weak_areas:
                weak_areas = json.loads(latest_placement.weak_areas) if isinstance(latest_placement.weak_areas, str) else latest_placement.weak_areas
        except Exception:
            pass

    return {
        "has_completed_placement_test": current_learner.has_completed_placement_test or False,
        "placement_score": current_learner.placement_score,
        "cefr_level": current_learner.cefr_level or "A0",
        "proficiency_level": current_learner.proficiency_level.value if current_learner.proficiency_level else "Beginner",
        "benchmark_level": current_learner.benchmark_level or "Emergent Reader",
        "predicted_proficiency_score": current_learner.predicted_proficiency_score or 0.0,
        "learning_goal": current_learner.learning_goal or "conversation",
        "prior_knowledge": current_learner.prior_knowledge or "complete_beginner",
        "daily_minutes_goal": current_learner.daily_minutes_goal or 15,
        "skill_breakdown": skill_breakdown,
        "strengths": strengths,
        "weak_areas": weak_areas
    }


@router.post("/session", response_model=schemas.PlacementTestSessionResponse)
def create_placement_session(
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    """
    Computer Adaptive Placement Test: Generates a 6-tier diagnostic ladder
    spanning phonics, listening, spelling, pair matching, reading, and pronunciation.
    """
    try:
        return ai_engine.generate_placement_test_session(current_learner.id, db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate placement test session: {str(e)}"
        )


@router.post("/submit", response_model=schemas.PlacementTestResultResponse)
def submit_placement_test(
    submission: schemas.PlacementTestSubmit,
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    """
    Evaluates the Placement Test submissions, calculates difficulty-weighted accuracy,
    calibrates learner level (Beginner/Intermediate/Advanced), auto-unlocks tested-out nodes,
    and returns tailored recommendations.
    """
    try:
        return ai_engine.evaluate_placement_test(current_learner.id, submission, db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate placement test: {str(e)}"
        )
