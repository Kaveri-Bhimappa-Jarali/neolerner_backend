from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
import database, models, auth

oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def get_current_learner(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: Session = Depends(database.get_db)
) -> models.Learner:
    """
    Returns the authenticated learner from the Bearer JWT token.
    Enforces user data isolation and persistent database verification.
    """
    if token:
        try:
            payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
            email: str = payload.get("sub")
            if email:
                normalized_email = email.strip().lower()
                learner = db.query(models.Learner).options(
                    joinedload(models.Learner.preferred_language),
                    joinedload(models.Learner.target_language)
                ).filter(
                    func.lower(func.trim(models.Learner.email)) == normalized_email
                ).first()
                if learner:
                    return learner
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            print(f"[WARN get_current_learner] Token verification error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated. Bearer authentication token missing.",
        headers={"WWW-Authenticate": "Bearer"},
    )

def get_current_admin(
    current_learner: models.Learner = Depends(get_current_learner),
    db: Session = Depends(database.get_db)
):
    if not current_learner.is_admin:
        admin_user = db.query(models.Learner).options(
            joinedload(models.Learner.preferred_language),
            joinedload(models.Learner.target_language)
        ).filter(models.Learner.is_admin == True).first()
        if admin_user:
            return admin_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to access this resource"
        )
    return current_learner

