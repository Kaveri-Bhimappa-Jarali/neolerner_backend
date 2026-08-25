from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import schemas, models, auth, database

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=schemas.LearnerResponse, status_code=status.HTTP_201_CREATED)
def register(learner: schemas.LearnerCreate, db: Session = Depends(database.get_db)):
    db_learner = db.query(models.Learner).filter(models.Learner.email == learner.email).first()
    if db_learner:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(learner.password)
    new_learner = models.Learner(
        email=learner.email,
        hashed_password=hashed_password,
        full_name=learner.full_name,
        preferred_language_id=learner.preferred_language_id,
        target_language_id=learner.target_language_id,
        proficiency_level=learner.proficiency_level
    )
    db.add(new_learner)
    db.commit()
    db.refresh(new_learner)
    return new_learner

@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    learner = db.query(models.Learner).filter(models.Learner.email == form_data.username).first()
    if not learner or not auth.verify_password(form_data.password, learner.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": learner.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
