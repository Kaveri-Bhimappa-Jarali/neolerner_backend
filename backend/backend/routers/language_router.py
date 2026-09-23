from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import schemas, models, database

router = APIRouter(prefix="/api/languages", tags=["languages"])

@router.get("", response_model=List[schemas.LanguageResponse])
@router.get("/", response_model=List[schemas.LanguageResponse])
def get_languages(db: Session = Depends(database.get_db)):
    languages = db.query(models.Language).all()
    return languages
