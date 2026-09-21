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
