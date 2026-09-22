from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.orm import Session
import schemas, models, auth, database

import uuid
from typing import Optional

router = APIRouter(prefix="/api/auth", tags=["auth"])

def resolve_language_id(db: Session, lang_val, code_val) -> Optional[uuid.UUID]:
    if isinstance(lang_val, uuid.UUID):
        return lang_val
    if isinstance(lang_val, str):
        try:
            return uuid.UUID(lang_val)
        except ValueError:
            lang_by_code = db.query(models.Language).filter(
                func.lower(models.Language.code) == lang_val.lower()
            ).first()
            if lang_by_code:
                return lang_by_code.id
    if isinstance(lang_val, int):
        languages = db.query(models.Language).all()
        if 0 < lang_val <= len(languages):
            return languages[lang_val - 1].id
        elif languages:
            return languages[0].id
    if code_val and isinstance(code_val, str):
        lang_by_code = db.query(models.Language).filter(
            func.lower(models.Language.code) == code_val.lower()
        ).first()
        if lang_by_code:
            return lang_by_code.id
    first_lang = db.query(models.Language).first()
    return first_lang.id if first_lang else None

@router.post("/register", response_model=schemas.LearnerResponse, status_code=status.HTTP_201_CREATED)
@router.post("/register/", response_model=schemas.LearnerResponse, status_code=status.HTTP_201_CREATED)
def register(learner: schemas.LearnerCreate, db: Session = Depends(database.get_db)):
    normalized_email = learner.email.strip().lower()
    db_learner = db.query(models.Learner).filter(
        func.lower(func.trim(models.Learner.email)) == normalized_email
    ).first()
    if db_learner:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(learner.password)
    
    pref_id = resolve_language_id(db, learner.preferred_language_id, learner.preferred_language_code)
    target_id = resolve_language_id(db, learner.target_language_id, learner.target_language_code)

    new_learner = models.Learner(
        email=normalized_email,
        hashed_password=hashed_password,
        full_name=learner.full_name,
        age=learner.age,
        preferred_language_id=pref_id,
        target_language_id=target_id,
        proficiency_level=learner.proficiency_level,
        learning_goal=learner.learning_goal or "conversation",
        prior_knowledge=learner.prior_knowledge or "complete_beginner",
        cefr_level=learner.cefr_level or "A0",
        daily_minutes_goal=learner.daily_minutes_goal or 15
    )
    db.add(new_learner)
    db.commit()
    db.refresh(new_learner)
    return new_learner

@router.post("/login", response_model=schemas.Token)
@router.post("/login/", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    normalized_email = form_data.username.strip().lower()
    learner = db.query(models.Learner).filter(
        func.lower(func.trim(models.Learner.email)) == normalized_email
    ).first()
    if not learner:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No account found for this email. Please register first.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not auth.verify_password(form_data.password, learner.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": learner.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
