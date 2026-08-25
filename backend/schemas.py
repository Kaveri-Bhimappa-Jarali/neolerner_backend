from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from models import ProficiencyLevel, ProgressStatus, CourseLevel, AssessmentType, QuestionType

# --- Language Schemas ---
class LanguageBase(BaseModel):
    name: str
    code: str
    native_name: Optional[str] = None

class LanguageCreate(LanguageBase):
    pass

class LanguageResponse(LanguageBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


# --- Learner Schemas ---
class LearnerBase(BaseModel):
    email: EmailStr
    full_name: str
    preferred_language_id: Optional[UUID] = None
    target_language_id: Optional[UUID] = None
    proficiency_level: ProficiencyLevel = ProficiencyLevel.Beginner

class LearnerCreate(LearnerBase):
    password: str

class LearnerUpdate(BaseModel):
    full_name: Optional[str] = None
    preferred_language_id: Optional[UUID] = None
    target_language_id: Optional[UUID] = None
    proficiency_level: Optional[ProficiencyLevel] = None

class LearnerResponse(LearnerBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    preferred_language: Optional[LanguageResponse] = None
    target_language: Optional[LanguageResponse] = None

    model_config = ConfigDict(from_attributes=True)


# --- Auth Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None


# --- Answer Schemas ---
class AnswerBase(BaseModel):
    text: str
    is_correct: bool = False
    explanation: Optional[str] = None

class AnswerCreate(AnswerBase):
    pass

class AnswerResponse(AnswerBase):
    id: UUID
    question_id: UUID

    model_config = ConfigDict(from_attributes=True)


# --- Question Schemas ---
class QuestionBase(BaseModel):
    text: str
    type: QuestionType = QuestionType.multiple_choice
    points: int = 1

class QuestionCreate(QuestionBase):
    answers: List[AnswerCreate] = []

class QuestionResponse(QuestionBase):
    id: UUID
    assessment_id: UUID
    answers: List[AnswerResponse] = []

    model_config = ConfigDict(from_attributes=True)


# --- Assessment Schemas ---
class AssessmentBase(BaseModel):
    title: str
    type: AssessmentType = AssessmentType.quiz
    pass_percentage: float = 70.0

class AssessmentCreate(AssessmentBase):
    lesson_id: UUID
    questions: List[QuestionCreate] = []

class AssessmentResponse(AssessmentBase):
    id: UUID
    lesson_id: UUID

    model_config = ConfigDict(from_attributes=True)

class AssessmentDetailResponse(AssessmentResponse):
    questions: List[QuestionResponse] = []

    model_config = ConfigDict(from_attributes=True)


# --- Assessment Submission & Result Schemas ---
class QuestionAnswerSubmission(BaseModel):
    question_id: UUID
    selected_answer_id: UUID

class AssessmentSubmission(BaseModel):
    assessment_id: UUID
    answers: List[QuestionAnswerSubmission]

class AssessmentResultResponse(BaseModel):
    id: UUID
    learner_id: UUID
    assessment_id: UUID
    score: float
    max_score: float
    passed: bool
    completed_at: datetime
    assessment: Optional[AssessmentResponse] = None

    model_config = ConfigDict(from_attributes=True)


# --- Lesson Schemas ---
class LessonBase(BaseModel):
    title: str
    content: Optional[str] = None
    duration_minutes: int = 10
    order: int = 1

class LessonCreate(LessonBase):
    topic_id: UUID

class LessonUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    duration_minutes: Optional[int] = None
    order: Optional[int] = None

class LessonResponse(LessonBase):
    id: UUID
    topic_id: UUID

    model_config = ConfigDict(from_attributes=True)

class LessonDetailResponse(LessonResponse):
    assessments: List[AssessmentResponse] = []

    model_config = ConfigDict(from_attributes=True)


# --- Topic Schemas ---
class TopicBase(BaseModel):
    title: str
    description: Optional[str] = None
    order: int = 1

class TopicCreate(TopicBase):
    course_id: UUID

class TopicUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None

class TopicResponse(TopicBase):
    id: UUID
    course_id: UUID

    model_config = ConfigDict(from_attributes=True)

class TopicDetailResponse(TopicResponse):
    lessons: List[LessonResponse] = []

    model_config = ConfigDict(from_attributes=True)


# --- Course Schemas ---
class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None
    level: CourseLevel = CourseLevel.Beginner
    thumbnail_url: Optional[str] = None
    is_published: bool = True

class CourseCreate(CourseBase):
    language_id: UUID

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    level: Optional[CourseLevel] = None
    thumbnail_url: Optional[str] = None
    is_published: Optional[bool] = None

class CourseResponse(CourseBase):
    id: UUID
    language_id: UUID
    created_at: datetime
    language: Optional[LanguageResponse] = None

    model_config = ConfigDict(from_attributes=True)

class CourseDetailResponse(CourseResponse):
    topics: List[TopicDetailResponse] = []

    model_config = ConfigDict(from_attributes=True)


# --- Learning Progress Schemas ---
class LearningProgressBase(BaseModel):
    status: ProgressStatus = ProgressStatus.not_started
    percentage_completed: float = 0.0

class LearningProgressCreate(LearningProgressBase):
    lesson_id: UUID

class LearningProgressUpdate(BaseModel):
    status: Optional[ProgressStatus] = None
    percentage_completed: Optional[float] = None

class LearningProgressResponse(LearningProgressBase):
    id: UUID
    learner_id: UUID
    lesson_id: UUID
    last_accessed: datetime
    lesson: Optional[LessonResponse] = None

    model_config = ConfigDict(from_attributes=True)


# --- Recommendation Schemas ---
class RecommendationBase(BaseModel):
    reason: Optional[str] = None
    priority: int = 1

class RecommendationCreate(RecommendationBase):
    learner_id: UUID
    recommended_course_id: UUID

class RecommendationResponse(RecommendationBase):
    id: UUID
    learner_id: UUID
    recommended_course_id: UUID
    created_at: datetime
    recommended_course: Optional[CourseResponse] = None

    model_config = ConfigDict(from_attributes=True)
