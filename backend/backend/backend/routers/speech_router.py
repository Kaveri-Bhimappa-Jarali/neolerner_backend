from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import schemas, models, database, dependencies, speech_engine, json

router = APIRouter(prefix="/api/speech", tags=["speech_pronunciation"])

@router.post("/assess", response_model=schemas.PronunciationAssessmentResponse)
@router.post("/assess/", response_model=schemas.PronunciationAssessmentResponse)
def assess_pronunciation(
    req: schemas.PronunciationAssessmentRequest,
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    """
    Pronunciation Assessment API:
    Evaluates learner spoken audio/transcript against target text, calculates overall score,
    accuracy, fluency, identifies problematic words, awards XP, and stores attempt in database.
    """
    return speech_engine.process_and_save_pronunciation(current_learner.id, req, db)


@router.get("/history", response_model=List[schemas.PronunciationAssessmentResponse])
@router.get("/history/", response_model=List[schemas.PronunciationAssessmentResponse])
def get_pronunciation_history(
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    """
    Retrieves recent pronunciation attempts for the authenticated learner.
    """
    attempts = db.query(models.PronunciationAttempt).filter(
        models.PronunciationAttempt.learner_id == current_learner.id
    ).order_by(models.PronunciationAttempt.created_at.desc()).limit(20).all()

    res = []
    for a in attempts:
        prob = []
        if a.problematic_words_json:
            try:
                prob = json.loads(a.problematic_words_json)
            except Exception:
                pass

        res.append(schemas.PronunciationAssessmentResponse(
            id=a.id,
            target_text=a.target_text,
            spoken_text=a.spoken_text,
            overall_score=a.overall_score,
            accuracy_score=a.accuracy_score,
            fluency_score=a.fluency_score,
            problematic_words=prob,
            feedback=a.feedback or "",
            xp_earned=15 if a.overall_score >= 60 else 5,
            current_speaking_score=a.overall_score,
            created_at=a.created_at
        ))
    return res
