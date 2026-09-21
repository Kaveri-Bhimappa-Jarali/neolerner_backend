from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.orm import Session
import schemas, models, auth, database

router = APIRouter(prefix="/api/auth", tags=["auth"])

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
    
    pref_id = learner.preferred_language_id
    target_id = learner.target_language_id

    if not pref_id and learner.preferred_language_code:
        p_lang = db.query(models.Language).filter(models.Language.code == learner.preferred_language_code.lower()).first()
        if p_lang:
            pref_id = p_lang.id

    if not target_id and learner.target_language_code:
        t_lang = db.query(models.Language).filter(models.Language.code == learner.target_language_code.lower()).first()
        if t_lang:
            target_id = t_lang.id

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
