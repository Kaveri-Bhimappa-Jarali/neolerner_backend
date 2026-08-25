import uuid
from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, Text, Enum, Uuid, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base

class ProficiencyLevel(str, enum.Enum):
    Beginner = "Beginner"
    Intermediate = "Intermediate"
    Advanced = "Advanced"

class ProgressStatus(str, enum.Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"

class CourseLevel(str, enum.Enum):
    Beginner = "Beginner"
    Intermediate = "Intermediate"
    Advanced = "Advanced"

class AssessmentType(str, enum.Enum):
    quiz = "quiz"
    final_test = "final_test"
    assignment = "assignment"

class QuestionType(str, enum.Enum):
    multiple_choice = "multiple_choice"
    fill_in_blank = "fill_in_blank"
    true_false = "true_false"


class Language(Base):
    __tablename__ = "languages"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False, unique=True)
    native_name = Column(String, nullable=True)

    # Relationships
    courses = relationship("Course", back_populates="language", cascade="all, delete-orphan")


class Learner(Base):
    __tablename__ = "learners"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    
    preferred_language_id = Column(Uuid(as_uuid=True), ForeignKey('languages.id'), nullable=True)
    target_language_id = Column(Uuid(as_uuid=True), ForeignKey('languages.id'), nullable=True)
    
    proficiency_level = Column(Enum(ProficiencyLevel), default=ProficiencyLevel.Beginner)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    preferred_language = relationship("Language", foreign_keys=[preferred_language_id])
    target_language = relationship("Language", foreign_keys=[target_language_id])
    progress = relationship("LearningProgress", back_populates="learner", cascade="all, delete-orphan")
    results = relationship("AssessmentResult", back_populates="learner", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="learner", cascade="all, delete-orphan")


class Course(Base):
    __tablename__ = "courses"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    language_id = Column(Uuid(as_uuid=True), ForeignKey('languages.id'), nullable=False)
    level = Column(Enum(CourseLevel), default=CourseLevel.Beginner)
    thumbnail_url = Column(String, nullable=True)
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    language = relationship("Language", back_populates="courses")
    topics = relationship("Topic", back_populates="course", cascade="all, delete-orphan", order_by="Topic.order")
    recommendations = relationship("Recommendation", back_populates="recommended_course", cascade="all, delete-orphan")


class Topic(Base):
    __tablename__ = "topics"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(Uuid(as_uuid=True), ForeignKey('courses.id'), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Integer, default=1)

    # Relationships
    course = relationship("Course", back_populates="topics")
    lessons = relationship("Lesson", back_populates="topic", cascade="all, delete-orphan", order_by="Lesson.order")


class Lesson(Base):
    __tablename__ = "lessons"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id = Column(Uuid(as_uuid=True), ForeignKey('topics.id'), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    duration_minutes = Column(Integer, default=10)
    order = Column(Integer, default=1)

    # Relationships
    topic = relationship("Topic", back_populates="lessons")
    assessments = relationship("Assessment", back_populates="lesson", cascade="all, delete-orphan")
    progress_records = relationship("LearningProgress", back_populates="lesson", cascade="all, delete-orphan")


class Assessment(Base):
    __tablename__ = "assessments"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_id = Column(Uuid(as_uuid=True), ForeignKey('lessons.id'), nullable=False)
    title = Column(String, nullable=False)
    type = Column(Enum(AssessmentType), default=AssessmentType.quiz)
    pass_percentage = Column(Float, default=70.0)

    # Relationships
    lesson = relationship("Lesson", back_populates="assessments")
    questions = relationship("Question", back_populates="assessment", cascade="all, delete-orphan")
    results = relationship("AssessmentResult", back_populates="assessment", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(Uuid(as_uuid=True), ForeignKey('assessments.id'), nullable=False)
    text = Column(Text, nullable=False)
    type = Column(Enum(QuestionType), default=QuestionType.multiple_choice)
    points = Column(Integer, default=1)

    # Relationships
    assessment = relationship("Assessment", back_populates="questions")
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")


class Answer(Base):
    __tablename__ = "answers"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(Uuid(as_uuid=True), ForeignKey('questions.id'), nullable=False)
    text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)
    explanation = Column(Text, nullable=True)

    # Relationships
    question = relationship("Question", back_populates="answers")


class AssessmentResult(Base):
    __tablename__ = "assessment_results"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learner_id = Column(Uuid(as_uuid=True), ForeignKey('learners.id'), nullable=False)
    assessment_id = Column(Uuid(as_uuid=True), ForeignKey('assessments.id'), nullable=False)
    score = Column(Float, nullable=False)
    max_score = Column(Float, default=100.0)
    passed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    learner = relationship("Learner", back_populates="results")
    assessment = relationship("Assessment", back_populates="results")


class LearningProgress(Base):
    __tablename__ = "learning_progress"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learner_id = Column(Uuid(as_uuid=True), ForeignKey('learners.id'), nullable=False)
    lesson_id = Column(Uuid(as_uuid=True), ForeignKey('lessons.id'), nullable=False)
    status = Column(Enum(ProgressStatus), default=ProgressStatus.not_started)
    percentage_completed = Column(Float, default=0.0)
    last_accessed = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    learner = relationship("Learner", back_populates="progress")
    lesson = relationship("Lesson", back_populates="progress_records")


class Recommendation(Base):
    __tablename__ = "recommendations"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learner_id = Column(Uuid(as_uuid=True), ForeignKey('learners.id'), nullable=False)
    recommended_course_id = Column(Uuid(as_uuid=True), ForeignKey('courses.id'), nullable=False)
    reason = Column(Text, nullable=True)
    priority = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    learner = relationship("Learner", back_populates="recommendations")
    recommended_course = relationship("Course", back_populates="recommendations")
