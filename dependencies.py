from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import func
from sqlalchemy.orm import Session
import database, models, auth

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_learner(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    from sqlalchemy.orm import joinedload
    normalized_email = email.strip().lower()
    learner = db.query(models.Learner).options(
        joinedload(models.Learner.preferred_language),
        joinedload(models.Learner.target_language)
    ).filter(
        func.lower(func.trim(models.Learner.email)) == normalized_email
    ).first()
    if learner is None:
        raise credentials_exception
    return learner

def get_current_admin(current_learner: models.Learner = Depends(get_current_learner)):
    if not current_learner.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to access this resource"
        )
    return current_learner

