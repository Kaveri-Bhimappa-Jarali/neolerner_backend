import uuid
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from datetime import datetime
import models, database

router = APIRouter(prefix="/api/database", tags=["database"])

ENTITY_CONFIGS = {
    "learners": {
        "model": models.Learner,
        "name": "Learner",
        "description": "User profiles, credentials, proficiency levels, and language preferences.",
        "icon": "Users",
        "columns": ["id", "full_name", "email", "proficiency_level", "preferred_language_id", "target_language_id", "created_at"]
    },
    "languages": {
        "model": models.Language,
        "name": "Language",
        "description": "Supported languages in the literacy learning system.",
        "icon": "Globe",
        "columns": ["id", "name", "code", "native_name"]
    },
    "courses": {
        "model": models.Course,
        "name": "Course",
        "description": "Language learning courses organized by language and difficulty level.",
        "icon": "BookOpen",
        "columns": ["id", "title", "description", "level", "language_id", "is_published", "created_at"]
    },
    "topics": {
        "model": models.Topic,
        "name": "Topic",
        "description": "Modular sections within courses grouping related lessons.",
        "icon": "Layers",
        "columns": ["id", "title", "description", "order", "course_id"]
    },
    "lessons": {
        "model": models.Lesson,
        "name": "Lesson",
        "description": "Educational units with markdown content and estimated duration.",
        "icon": "FileText",
        "columns": ["id", "title", "duration_minutes", "order", "topic_id"]
    },
    "assessments": {
        "model": models.Assessment,
        "name": "Assessment",
        "description": "Quizzes and tests linked to lessons to test learner mastery.",
        "icon": "HelpCircle",
        "columns": ["id", "title", "type", "pass_percentage", "lesson_id"]
    },
    "questions": {
        "model": models.Question,
        "name": "Question",
        "description": "Individual questions inside assessments (multiple choice, fill-in-blank, true/false).",
        "icon": "HelpCircle",
        "columns": ["id", "text", "type", "points", "assessment_id"]
    },
    "answers": {
        "model": models.Answer,
        "name": "Answer",
        "description": "Options for questions with correctness flag and explanations.",
        "icon": "CheckSquare",
        "columns": ["id", "text", "is_correct", "explanation", "question_id"]
    },
    "assessment_results": {
        "model": models.AssessmentResult,
        "name": "Assessment Result",
        "description": "Recorded test scores, pass/fail status, and attempt timestamps.",
        "icon": "Award",
        "columns": ["id", "learner_id", "assessment_id", "score", "max_score", "passed", "completed_at"]
    },
    "learning_progress": {
        "model": models.LearningProgress,
        "name": "Learning Progress",
        "description": "Status and completion percentage tracking per learner and lesson.",
        "icon": "TrendingUp",
        "columns": ["id", "learner_id", "lesson_id", "status", "percentage_completed", "last_accessed"]
    },
    "recommendations": {
        "model": models.Recommendation,
        "name": "Recommendation",
        "description": "Personalized course suggestions generated for learners.",
        "icon": "Sparkles",
        "columns": ["id", "learner_id", "recommended_course_id", "reason", "priority", "created_at"]
    }
}

@router.get("/overview")
def get_database_overview(db: Session = Depends(database.get_db)):
    overview = []
    for key, cfg in ENTITY_CONFIGS.items():
        count = db.query(cfg["model"]).count()
        overview.append({
            "key": key,
            "name": cfg["name"],
            "description": cfg["description"],
            "icon": cfg["icon"],
            "count": count,
            "columns": cfg["columns"]
        })
    return {"entities": overview, "total_tables": len(overview)}

@router.get("/entities/{entity_key}")
def get_entity_data(entity_key: str, db: Session = Depends(database.get_db)):
    if entity_key not in ENTITY_CONFIGS:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_key}' not found in registry")

    cfg = ENTITY_CONFIGS[entity_key]
    model = cfg["model"]
    records = db.query(model).all()

    serialized = []
    for r in records:
        row = {}
        for col in cfg["columns"]:
            val = getattr(r, col, None)
            if hasattr(val, "isoformat"):
                val = val.isoformat()
            elif val is not None:
                val = str(val)
            row[col] = val
        serialized.append(row)

    return {
        "key": entity_key,
        "name": cfg["name"],
        "description": cfg["description"],
        "columns": cfg["columns"],
        "total_records": len(serialized),
        "data": serialized
    }

@router.post("/entities/{entity_key}", status_code=status.HTTP_201_CREATED)
def create_entity_record(entity_key: str, payload: Dict[str, Any] = Body(...), db: Session = Depends(database.get_db)):
    if entity_key not in ENTITY_CONFIGS:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_key}' not found")

    cfg = ENTITY_CONFIGS[entity_key]
    model = cfg["model"]

    # Filter payload keys that exist on model
    clean_data = {}
    for col in cfg["columns"]:
        if col == "id":
            clean_data["id"] = uuid.uuid4() if "id" not in payload or not payload["id"] else uuid.UUID(str(payload["id"]))
        elif col in payload and payload[col] is not None and payload[col] != "":
            val = payload[col]
            # Convert UUID foreign keys if necessary
            if col.endswith("_id"):
                try:
                    val = uuid.UUID(str(val))
                except Exception:
                    pass
            elif col in ["is_correct", "is_published", "passed"]:
                val = str(val).lower() in ["true", "1", "yes"]
            elif col in ["order", "points", "priority", "duration_minutes"]:
                val = int(val)
            elif col in ["score", "max_score", "pass_percentage", "percentage_completed"]:
                val = float(val)
            clean_data[col] = val

    try:
        new_item = model(**clean_data)
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        return {"message": "Record created successfully", "id": str(new_item.id)}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating record: {str(e)}")

@router.delete("/entities/{entity_key}/{record_id}")
def delete_entity_record(entity_key: str, record_id: str, db: Session = Depends(database.get_db)):
    if entity_key not in ENTITY_CONFIGS:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_key}' not found")

    model = ENTITY_CONFIGS[entity_key]["model"]
    try:
        rec_uuid = uuid.UUID(record_id)
        item = db.query(model).filter(model.id == rec_uuid).first()
        if not item:
            raise HTTPException(status_code=404, detail="Record not found")
        db.delete(item)
        db.commit()
        return {"message": "Record deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error deleting record: {str(e)}")
