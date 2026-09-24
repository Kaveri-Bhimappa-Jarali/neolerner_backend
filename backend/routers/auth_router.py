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

import random

try:
    from email_service import send_verification_email
except ImportError:
    try:
        from backend.email_service import send_verification_email
    except ImportError:
        def send_verification_email(to_email, code, full_name=""):
            print(f"[EMAIL FALLBACK] Verification code for {to_email}: {code}")

@router.post("/register", response_model=schemas.LearnerResponse, status_code=status.HTTP_201_CREATED)
@router.post("/register/", response_model=schemas.LearnerResponse, status_code=status.HTTP_201_CREATED)
def register(learner: schemas.LearnerCreate, db: Session = Depends(database.get_db)):
    try:
        normalized_email = learner.email.strip().lower()
        db_learner = db.query(models.Learner).filter(
            func.lower(func.trim(models.Learner.email)) == normalized_email
        ).first()
        if db_learner:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        hashed_password = auth.get_password_hash(learner.password)
        
        pref_id = resolve_language_id(db, learner.preferred_language_id, learner.preferred_language_code)
        target_id = resolve_language_id(db, learner.target_language_id, learner.target_language_code)
        verification_code = str(random.randint(100000, 999999))

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
            daily_minutes_goal=learner.daily_minutes_goal or 15,
            is_verified=False,
            verification_code=verification_code
        )
        db.add(new_learner)
        db.commit()
        db.refresh(new_learner)

        # Dispatch real 6-digit verification code email to target user email address
        try:
            send_verification_email(normalized_email, verification_code, new_learner.full_name)
        except Exception as mail_err:
            print(f"[WARN] Failed to send verification email: {mail_err}")

        # Mask verification_code in response so it is NEVER exposed on client device
        new_learner.verification_code = None
        return new_learner
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[ERROR /api/auth/register]: {e}")
        raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")

@router.post("/login", response_model=schemas.Token)
@router.post("/login/", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    try:
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
        needs_onboarding = not learner.preferred_language_id or not learner.target_language_id
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "needs_onboarding": needs_onboarding,
            "is_verified": bool(learner.is_verified or learner.is_admin)
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR /api/auth/login]: {e}")
        raise HTTPException(status_code=400, detail=f"Login failed: {str(e)}")

@router.post("/google", response_model=schemas.Token)
@router.post("/google/", response_model=schemas.Token)
def google_auth(req: schemas.GoogleAuthRequest, db: Session = Depends(database.get_db)):
    """Authenticates or creates a user using Google OAuth Single Sign-On."""
    try:
        normalized_email = req.email.strip().lower()
        learner = db.query(models.Learner).filter(
            func.lower(func.trim(models.Learner.email)) == normalized_email
        ).first()

        needs_onboarding = False

        if not learner:
            # First-time Google user -> create account with default languages & set is_verified=True
            en_lang = db.query(models.Language).filter(models.Language.code == "en").first()
            kn_lang = db.query(models.Language).filter(models.Language.code == "kn").first()
            first_lang = db.query(models.Language).first()
            
            pref_id = en_lang.id if en_lang else (first_lang.id if first_lang else None)
            target_id = kn_lang.id if kn_lang else (first_lang.id if first_lang else None)

            learner = models.Learner(
                id=uuid.uuid4(),
                email=normalized_email,
                hashed_password=auth.get_password_hash(f"GoogleSSO_{req.google_id}_{uuid.uuid4()}"),
                full_name=req.full_name or "Google User",
                google_id=req.google_id,
                avatar_url=req.avatar_url,
                preferred_language_id=pref_id,
                target_language_id=target_id,
                is_verified=True
            )
            db.add(learner)
            db.commit()
            db.refresh(learner)
            needs_onboarding = True
        else:
            if not learner.google_id:
                learner.google_id = req.google_id
            if req.avatar_url:
                learner.avatar_url = req.avatar_url
            learner.is_verified = True
            db.commit()
            needs_onboarding = not learner.preferred_language_id or not learner.target_language_id

        access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(
            data={"sub": learner.email}, expires_delta=access_token_expires
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "needs_onboarding": needs_onboarding,
            "is_verified": True
        }
    except Exception as e:
        db.rollback()
        print(f"[ERROR /api/auth/google]: {e}")
        raise HTTPException(status_code=400, detail=f"Google authentication failed: {str(e)}")

@router.post("/verify-email")
@router.post("/verify-email/")
def verify_email(req: schemas.VerifyEmailRequest, db: Session = Depends(database.get_db)):
    """Validates 6-digit email verification code."""
    normalized_email = req.email.strip().lower()
    learner = db.query(models.Learner).filter(
        func.lower(func.trim(models.Learner.email)) == normalized_email
    ).first()
    
    if not learner:
        raise HTTPException(status_code=404, detail="Learner email not found")
    
    # Strictly require exact matching verification code stored for the user
    if learner.verification_code and learner.verification_code.strip() == req.code.strip():
        learner.is_verified = True
        db.commit()
        return {"status": "success", "message": "Email verified successfully"}
    
    raise HTTPException(status_code=400, detail="Invalid verification code. Please check your email or click Resend.")

@router.post("/resend-code")
@router.post("/resend-code/")
def resend_code(req: schemas.ResendCodeRequest, db: Session = Depends(database.get_db)):
    """Generates a new 6-digit verification code and emails it."""
    normalized_email = req.email.strip().lower()
    learner = db.query(models.Learner).filter(
        func.lower(func.trim(models.Learner.email)) == normalized_email
    ).first()
    
    if not learner:
        raise HTTPException(status_code=404, detail="Learner email not found")
    
    new_code = str(random.randint(100000, 999999))
    learner.verification_code = new_code
    db.commit()

    # Dispatch real 6-digit verification code email
    send_verification_email(normalized_email, new_code, learner.full_name)

    return {"status": "success", "message": "New verification code sent to your email!"}




