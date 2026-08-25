from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import schemas, models, database, dependencies

router = APIRouter(prefix="/api/courses", tags=["courses"])

# --- Courses ---
@router.get("/", response_model=List[schemas.CourseResponse])
def get_courses(
    language_id: Optional[UUID] = None,
    level: Optional[models.CourseLevel] = None,
    db: Session = Depends(database.get_db)
):
    query = db.query(models.Course).filter(models.Course.is_published == True)
    if language_id:
        query = query.filter(models.Course.language_id == language_id)
    if level:
        query = query.filter(models.Course.level == level)
    return query.all()

@router.get("/{course_id}", response_model=schemas.CourseDetailResponse)
def get_course_detail(course_id: UUID, db: Session = Depends(database.get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.post("/", response_model=schemas.CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(course: schemas.CourseCreate, db: Session = Depends(database.get_db)):
    db_course = models.Course(**course.model_dump())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

# --- Topics ---
@router.post("/{course_id}/topics", response_model=schemas.TopicResponse, status_code=status.HTTP_201_CREATED)
def create_topic(course_id: UUID, topic: schemas.TopicBase, db: Session = Depends(database.get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    db_topic = models.Topic(**topic.model_dump(), course_id=course_id)
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    return db_topic

# --- Lessons ---
@router.post("/topics/{topic_id}/lessons", response_model=schemas.LessonResponse, status_code=status.HTTP_201_CREATED)
def create_lesson(topic_id: UUID, lesson: schemas.LessonBase, db: Session = Depends(database.get_db)):
    topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    db_lesson = models.Lesson(**lesson.model_dump(), topic_id=topic_id)
    db.add(db_lesson)
    db.commit()
    db.refresh(db_lesson)
    return db_lesson

@router.get("/lessons/{lesson_id}", response_model=schemas.LessonDetailResponse)
def get_lesson_detail(lesson_id: UUID, db: Session = Depends(database.get_db)):
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson
