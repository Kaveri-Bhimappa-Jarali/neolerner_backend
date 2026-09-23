import os
import uuid
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
import database, models

router = APIRouter(prefix="/api/db", tags=["database-explorer"])

TABLE_MODELS = {
    "languages": models.Language,
    "learners": models.Learner,
    "courses": models.Course,
    "topics": models.Topic,
    "lessons": models.Lesson,
    "assessments": models.Assessment,
    "questions": models.Question,
    "answers": models.Answer,
    "assessment_results": models.AssessmentResult,
    "learning_progress": models.LearningProgress,
    "recommendations": models.Recommendation,
    "vocabulary": models.Vocabulary,
    "vocabulary_srs": models.VocabularySRS,
    "review_items": models.ReviewItem,
}

@router.get("/overview")
@router.get("/overview/")
def get_db_overview(db: Session = Depends(database.get_db)):
    """Returns general database health, storage path, table count and row metrics."""
    tables_info = []
    total_records = 0
    
    for table_name, model_cls in TABLE_MODELS.items():
        try:
            count = db.query(model_cls).count()
        except Exception:
            count = 0
        total_records += count
        
        # Get column count
        columns = [c.name for c in model_cls.__table__.columns]
        
        tables_info.append({
            "name": table_name,
            "row_count": count,
            "column_count": len(columns),
            "columns": columns
        })
        
    db_file_size = 0
    if os.path.exists(database.DB_PATH):
        db_file_size = os.path.getsize(database.DB_PATH)
        
    return {
        "status": "connected",
        "database_type": "SQLite",
        "database_path": database.DB_PATH,
        "database_size_bytes": db_file_size,
        "database_size_formatted": f"{db_file_size / 1024:.2f} KB",
        "total_tables": len(TABLE_MODELS),
        "total_records": total_records,
        "tables": tables_info
    }

@router.get("/schema")
@router.get("/schema/")
def get_db_schema():
    """Returns complete schema specification including columns, types, keys, and foreign relationships."""
    schema = {}
    
    for table_name, model_cls in TABLE_MODELS.items():
        table = model_cls.__table__
        columns_meta = []
        
        for col in table.columns:
            fk_info = None
            if col.foreign_keys:
                fk = list(col.foreign_keys)[0]
                fk_info = {
                    "target_table": fk.column.table.name,
                    "target_column": fk.column.name
                }
                
            columns_meta.append({
                "name": col.name,
                "type": str(col.type),
                "primary_key": col.primary_key,
                "nullable": col.nullable,
                "foreign_key": fk_info,
                "default": str(col.default.arg) if col.default is not None and hasattr(col.default, 'arg') else None
            })
            
        schema[table_name] = {
            "name": table_name,
            "columns": columns_meta,
            "primary_keys": [c.name for c in table.primary_key.columns]
        }
        
    return schema

@router.get("/tables/{table_name}")
@router.get("/tables/{table_name}/")
def get_table_data(
    table_name: str,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None),
    db: Session = Depends(database.get_db)
):
    """Returns paginated live records from any requested database table with optional search."""
    if table_name not in TABLE_MODELS:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found. Available tables: {list(TABLE_MODELS.keys())}")
        
    model_cls = TABLE_MODELS[table_name]
    query = db.query(model_cls)
    
    # Optional search across string columns
    if search:
        search_filter = None
        for col in model_cls.__table__.columns:
            if "VARCHAR" in str(col.type).upper() or "TEXT" in str(col.type).upper() or "STRING" in str(col.type).upper():
                cond = col.ilike(f"%{search}%")
                search_filter = cond if search_filter is None else (search_filter | cond)
        if search_filter is not None:
            query = query.filter(search_filter)
            
    total_rows = query.count()
    records = query.offset(offset).limit(limit).all()
    
    # Serialize records to dict
    serialized_rows = []
    columns = [c.name for c in model_cls.__table__.columns]
    
    for r in records:
        row_dict = {}
        for col_name in columns:
            val = getattr(r, col_name)
            # Mask sensitive passwords in demonstration
            if col_name == "hashed_password" and val:
                row_dict[col_name] = "•••••••••••• (bcrypt hash)"
            elif hasattr(val, 'isoformat'):
                row_dict[col_name] = val.isoformat()
            elif isinstance(val, uuid.UUID):
                row_dict[col_name] = str(val)
            elif hasattr(val, 'value'): # Enum
                row_dict[col_name] = val.value
            else:
                row_dict[col_name] = val
        serialized_rows.append(row_dict)
        
    return {
        "table_name": table_name,
        "total_count": total_rows,
        "limit": limit,
        "offset": offset,
        "columns": columns,
        "rows": serialized_rows
    }


def parse_field_value(col, value):
    if value is None:
        return None
    col_type = str(col.type).upper()
    if "UUID" in col_type:
        return uuid.UUID(str(value)) if not isinstance(value, uuid.UUID) else value
    elif "INT" in col_type:
        return int(value)
    elif "FLOAT" in col_type or "NUMERIC" in col_type:
        return float(value)
    elif "BOOL" in col_type:
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes")
        return bool(value)
    elif "DATETIME" in col_type or "TIMESTAMP" in col_type:
        if isinstance(value, str):
            from datetime import datetime
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except Exception:
                return datetime.utcnow()
        return value
    elif hasattr(col.type, "enum_class") and col.type.enum_class:
        try:
            return col.type.enum_class(value)
        except Exception:
            return value
    return str(value)


@router.post("/tables/{table_name}")
@router.post("/tables/{table_name}/")
def create_table_record(
    table_name: str,
    payload: Dict[str, Any],
    db: Session = Depends(database.get_db)
):
    """Creates a new record in any target database table dynamically."""
    if table_name not in TABLE_MODELS:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found.")
    
    model_cls = TABLE_MODELS[table_name]
    new_instance = model_cls()
    
    # Handle password hashing if raw password is supplied
    if "password" in payload and hasattr(model_cls, "hashed_password"):
        import auth
        new_instance.hashed_password = auth.get_password_hash(payload.pop("password"))

    for col in model_cls.__table__.columns:
        if col.name in payload and col.name != "id":
            val = payload[col.name]
            try:
                parsed_val = parse_field_value(col, val)
                setattr(new_instance, col.name, parsed_val)
            except Exception as err:
                raise HTTPException(status_code=400, detail=f"Invalid value for field '{col.name}': {str(err)}")
                
    try:
        db.add(new_instance)
        db.commit()
        db.refresh(new_instance)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database insertion failed: {str(e)}")

    return {"message": f"Successfully created record in '{table_name}'", "id": str(getattr(new_instance, 'id', ''))}


@router.put("/tables/{table_name}/{record_id}")
@router.put("/tables/{table_name}/{record_id}/")
def update_table_record(
    table_name: str,
    record_id: str,
    payload: Dict[str, Any],
    db: Session = Depends(database.get_db)
):
    """Updates an existing record in any target database table by primary key."""
    if table_name not in TABLE_MODELS:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found.")
        
    model_cls = TABLE_MODELS[table_name]
    try:
        rec_uuid = uuid.UUID(record_id)
        instance = db.query(model_cls).filter(model_cls.id == rec_uuid).first()
    except Exception:
        instance = db.query(model_cls).filter(model_cls.id == record_id).first()

    if not instance:
        raise HTTPException(status_code=404, detail=f"Record '{record_id}' not found in '{table_name}'.")

    if "password" in payload and payload["password"] and hasattr(model_cls, "hashed_password"):
        import auth
        instance.hashed_password = auth.get_password_hash(payload.pop("password"))

    for col in model_cls.__table__.columns:
        if col.name in payload and col.name != "id":
            val = payload[col.name]
            if val is not None:
                try:
                    parsed_val = parse_field_value(col, val)
                    setattr(instance, col.name, parsed_val)
                except Exception as err:
                    raise HTTPException(status_code=400, detail=f"Invalid value for field '{col.name}': {str(err)}")

    try:
        db.commit()
        db.refresh(instance)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database update failed: {str(e)}")

    return {"message": f"Successfully updated record in '{table_name}'", "id": record_id}


@router.delete("/tables/{table_name}/{record_id}")
@router.delete("/tables/{table_name}/{record_id}/")
def delete_table_record(
    table_name: str,
    record_id: str,
    db: Session = Depends(database.get_db)
):
    """Deletes a record from any target database table by primary key."""
    if table_name not in TABLE_MODELS:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found.")

    model_cls = TABLE_MODELS[table_name]
    try:
        rec_uuid = uuid.UUID(record_id)
        instance = db.query(model_cls).filter(model_cls.id == rec_uuid).first()
    except Exception:
        instance = db.query(model_cls).filter(model_cls.id == record_id).first()

    if not instance:
        raise HTTPException(status_code=404, detail=f"Record '{record_id}' not found in '{table_name}'.")

    try:
        db.delete(instance)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database deletion failed: {str(e)}")

    return {"message": f"Successfully deleted record '{record_id}' from '{table_name}'"}

