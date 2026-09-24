from pydantic import BaseModel, ConfigDict
try:
    import email_validator
    from pydantic import EmailStr
except ImportError:
    EmailStr = str
from typing import Optional, List, Any, Union
from uuid import UUID
from datetime import datetime
from models import (
    ProficiencyLevel, ProgressStatus, CourseLevel, AssessmentType, 
    QuestionType, LeagueTier, FriendshipStatus, UnitMasteryLevel
)

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
    age: Optional[int] = None
    preferred_language_id: Optional[Any] = None
    target_language_id: Optional[Any] = None
    preferred_language_code: Optional[str] = None
    target_language_code: Optional[str] = None
    proficiency_level: ProficiencyLevel = ProficiencyLevel.Beginner
    predicted_proficiency_score: float = 0.0
    benchmark_level: str = "Emergent Reader"
    has_completed_placement_test: bool = False
    placement_score: Optional[float] = None
    
    # Onboarding & CEFR Fields
    learning_goal: Optional[str] = "conversation"
    prior_knowledge: Optional[str] = "complete_beginner"
    cefr_level: Optional[str] = "A0"
    daily_minutes_goal: Optional[int] = 15
    
    # Gamification Fields
    xp: int = 0
    gems: int = 500
    hearts: int = 5
    streak: int = 0
    last_active_date: Optional[datetime] = None
    streak_freeze_count: int = 0
    double_or_nothing_active: bool = False
    double_or_nothing_streak: int = 0
    last_heart_recharge: Optional[datetime] = None
    daily_xp_goal: int = 20
    daily_xp_earned: int = 0
    last_goal_completed_date: Optional[datetime] = None
    league_tier: Optional[LeagueTier] = LeagueTier.Bronze
    is_admin: bool = False
    is_verified: bool = False
    google_id: Optional[str] = None
    avatar_url: Optional[str] = None

class LearnerCreate(LearnerBase):
    password: str

class LearnerUpdate(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    preferred_language_id: Optional[UUID] = None
    target_language_id: Optional[UUID] = None
    preferred_language_code: Optional[str] = None
    target_language_code: Optional[str] = None
    proficiency_level: Optional[ProficiencyLevel] = None
    has_completed_placement_test: Optional[bool] = None
    placement_score: Optional[float] = None
    learning_goal: Optional[str] = None
    prior_knowledge: Optional[str] = None
    cefr_level: Optional[str] = None
    daily_minutes_goal: Optional[int] = None
    xp: Optional[int] = None
    gems: Optional[int] = None
    hearts: Optional[int] = None
    streak: Optional[int] = None
    last_active_date: Optional[datetime] = None
    streak_freeze_count: Optional[int] = None
    double_or_nothing_active: Optional[bool] = None
    double_or_nothing_streak: Optional[int] = None
    daily_xp_goal: Optional[int] = None
    daily_xp_earned: Optional[int] = None
    last_goal_completed_date: Optional[datetime] = None
    league_tier: Optional[LeagueTier] = None

class LearnerResponse(LearnerBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    verification_code: Optional[str] = None
    preferred_language: Optional[LanguageResponse] = None
    target_language: Optional[LanguageResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ShopPurchase(BaseModel):
    item_name: str # "streak_freeze", "heart_refill", "double_or_nothing"


# --- Auth Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str
    needs_onboarding: bool = False
    is_verified: bool = True

class TokenData(BaseModel):
    email: Optional[str] = None

class GoogleAuthRequest(BaseModel):
    credential: Optional[str] = None
    email: EmailStr
    full_name: str
    google_id: str
    avatar_url: Optional[str] = None

class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str

class ResendCodeRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str



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
    competency_tag: Optional[str] = "reading"
    difficulty_level: Optional[int] = 1

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
    language_code: Optional[str] = None

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
    assessment_id: Optional[UUID] = None
    score: float
    max_score: float = 100.0
    passed: bool = False
    completed_at: Optional[datetime] = None
    assessment: Optional[AssessmentResponse] = None
    xp_earned: Optional[int] = 0
    gems_earned: Optional[int] = 0
    hearts_lost: Optional[int] = 0
    current_hearts: Optional[int] = 5

    model_config = ConfigDict(from_attributes=True)


# --- Lesson Schemas ---
class LessonBase(BaseModel):
    title: str
    content: Optional[str] = None
    duration_minutes: int = 10
    order: int = 1
    competency_tag: Optional[str] = "phonics"

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
    language_code: Optional[str] = None

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
    cefr_level: str = "A1"
    min_score: float = 0.0
    max_score: float = 100.0
    prerequisites_json: Optional[str] = "[]"
    skills_json: Optional[str] = "[]"
    difficulty: str = "beginner"
    goals_json: Optional[str] = "[]"

class CourseCreate(CourseBase):
    language_id: UUID

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    level: Optional[CourseLevel] = None
    thumbnail_url: Optional[str] = None
    is_published: Optional[bool] = None
    cefr_level: Optional[str] = None
    min_score: Optional[float] = None
    max_score: Optional[float] = None
    prerequisites_json: Optional[str] = None
    skills_json: Optional[str] = None
    difficulty: Optional[str] = None
    goals_json: Optional[str] = None

class CourseResponse(CourseBase):
    id: UUID
    language_id: UUID
    created_at: datetime
    language: Optional[LanguageResponse] = None

    model_config = ConfigDict(from_attributes=True)

class CourseDetailResponse(CourseResponse):
    topics: List[TopicDetailResponse] = []

    model_config = ConfigDict(from_attributes=True)


# --- Adaptive Course Recommendation Engine Schemas ---
class ProficiencyBandConfigItem(BaseModel):
    min: float
    max: float
    level: str
    title: str

class EngineWeightsConfig(BaseModel):
    level_weight: float = 0.40
    skill_weight: float = 0.25
    goal_weight: float = 0.20
    prerequisite_weight: float = 0.10
    difficulty_weight: float = 0.05

class RecommendationReasonItem(BaseModel):
    text: str
    reason_type: str  # "level_match", "goal_match", "weak_skill_target", "prerequisite_unlocked", "starting_unit"

class CourseRecommendationItem(BaseModel):
    course_id: UUID
    title: str
    description: Optional[str] = None
    cefr_level: str
    recommendation_type: str  # "primary", "skill_booster", "optional_challenge", "locked"
    match_score: float
    is_locked: bool = False
    lock_reason: Optional[str] = None
    reasons: List[RecommendationReasonItem] = []
    starting_topic_index: int = 1
    starting_topic_id: Optional[UUID] = None
    starting_topic_title: Optional[str] = None
    skipped_topics_count: int = 0
    skills_covered: List[str] = []
    target_goals: List[str] = []

class CourseRecommendationResponse(BaseModel):
    learner_overall_score: float
    learner_cefr_level: str
    learner_goal: str
    skill_breakdown: dict = {}
    strengths: List[str] = []
    weaknesses: List[str] = []
    primary_recommendation: Optional[CourseRecommendationItem] = None
    skill_boosters: List[CourseRecommendationItem] = []
    optional_challenges: List[CourseRecommendationItem] = []
    all_ranked_courses: List[CourseRecommendationItem] = []


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


# --- Vocabulary Schemas ---
class VocabularyBase(BaseModel):
    word: str
    translation: str
    explanation: Optional[str] = None
    difficulty_level: Optional[int] = 1

class VocabularyResponse(VocabularyBase):
    id: UUID
    language_id: UUID

    model_config = ConfigDict(from_attributes=True)

# --- VocabularySRS Schemas ---
class VocabularySRSResponse(BaseModel):
    id: UUID
    learner_id: UUID
    vocabulary_id: UUID
    interval: int
    ease_factor: float
    repetitions: int
    next_review_date: datetime
    last_reviewed_at: datetime
    vocabulary: VocabularyResponse

    model_config = ConfigDict(from_attributes=True)

class SRSReviewSubmit(BaseModel):
    vocabulary_srs_id: UUID
    quality: int  # Quality score 0-5 for SM-2

# --- ReviewItem (Mistake) Schemas ---
class ReviewItemResponse(BaseModel):
    id: UUID
    learner_id: UUID
    question_id: UUID
    incorrect_answer: Optional[str] = None
    review_count: int
    is_resolved: bool
    created_at: datetime
    resolved_at: Optional[datetime] = None
    question: Optional[QuestionResponse] = None

    model_config = ConfigDict(from_attributes=True)

class ReviewItemSubmit(BaseModel):
    question_id: UUID
    incorrect_answer: Optional[str] = None
    is_correct: bool


# --- AI Engine & Learning Path Schemas ---
class ProficiencyPredictionResponse(BaseModel):
    reading: float
    writing: float
    comprehension: float
    listening: float
    speaking: float
    composite_score: float
    benchmark_level: str
    total_assessments: int
    recommendation_focus: str

class LearningPathNode(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    type: str # "lesson", "quiz", "remedial_drill", "milestone_checkpoint"
    status: str # "completed", "in_progress", "locked"
    order: int
    score: Optional[float] = None
    duration_minutes: int = 10
    lesson_id: Optional[UUID] = None
    assessment_id: Optional[UUID] = None
    competency_tag: str = "phonics"

class LearningPathResponse(BaseModel):
    course_id: Optional[UUID] = None
    course_title: str
    target_language_name: str
    nodes: List[LearningPathNode]
    current_node_index: int
    total_nodes: int
    completion_rate: float
    predicted_proficiency_score: float
    benchmark_level: str

class AdaptiveQuestionAnswer(BaseModel):
    id: str
    text: str
    is_correct: bool
    explanation: Optional[str] = None

class AdaptiveQuestion(BaseModel):
    id: str
    text: str
    type: QuestionType
    competency_tag: str
    points: int = 1
    prompt_audio_text: Optional[str] = None
    prompt_translation: Optional[str] = None
    target_word: Optional[str] = None
    scaffold_level: Optional[str] = "beginner"
    word_tiles: List[str] = []
    answers: List[AdaptiveQuestionAnswer] = []

class AdaptiveLessonResponse(BaseModel):
    session_id: str
    title: str
    reason: str
    target_competency: str
    language_code: str
    questions: List[AdaptiveQuestion]
    total_points: int

class AdaptiveAnswerSubmission(BaseModel):
    question_id: str
    is_correct: bool
    user_answer: Optional[str] = None

class AdaptiveLessonSubmit(BaseModel):
    session_id: str
    submissions: List[AdaptiveAnswerSubmission]

class AIRecommendationItem(BaseModel):
    id: str
    title: str
    reason: str
    type: str # "remedial_phonics", "spaced_review", "next_milestone", "challenge"
    action_url: str
    priority: int
    confidence: float
    competency_tag: str


# --- Placement & Initial Exam Diagnostic Testing Schemas ---
class PlacementTestQuestion(BaseModel):
    id: str
    text: str
    type: QuestionType
    competency_tag: str
    difficulty_level: int
    points: int = 1
    prompt_audio_text: Optional[str] = None
    prompt_translation: Optional[str] = None
    target_word: Optional[str] = None
    interface_translation: Optional[str] = None
    answers: List[AdaptiveQuestionAnswer] = []

class PlacementTestSessionResponse(BaseModel):
    session_id: str
    target_language_name: str
    target_language_code: str
    preferred_language_name: Optional[str] = None
    preferred_language_code: Optional[str] = None
    total_questions: int
    questions: List[PlacementTestQuestion]

class PlacementQuestionSubmission(BaseModel):
    question_id: str
    is_correct: bool
    difficulty_level: int
    user_answer: Optional[str] = None

class PlacementTestSubmit(BaseModel):
    session_id: str
    submissions: List[PlacementQuestionSubmission]

class PlacementTestResultResponse(BaseModel):
    placement_score: float
    calibrated_level: ProficiencyLevel
    benchmark_level: str
    cefr_level: str = "A0"
    skill_breakdown: Optional[dict] = None
    strengths: List[str] = []
    weak_areas: List[str] = []
    recommended_focus: Optional[str] = None
    tested_out_nodes_count: int
    xp_earned: int
    gems_earned: int
    message: str
    recommended_path_title: Optional[str] = None
    recommended_path_description: Optional[str] = None
    course_recommendations: Optional[CourseRecommendationResponse] = None
    recommended_course_title: Optional[str] = None
    recommended_course_id: Optional[UUID] = None
    recommendations: List[AIRecommendationItem] = []


# ==========================================
# --- AI Conversation Lab Schemas ---
# ==========================================
class ConversationScenarioItem(BaseModel):
    id: str
    name: str
    icon: str
    description: str
    cefr_target: str
    context_prompt: str

class ConversationStartRequest(BaseModel):
    scenario: str
    target_language_id: Optional[UUID] = None

class ConversationStartResponse(BaseModel):
    session_id: UUID
    scenario: str
    scenario_name: str
    target_language_code: str
    interface_language_code: str
    ai_message: str
    ai_audio_text: str
    phonetic: Optional[str] = None
    translation: Optional[str] = None
    context_hints: List[str] = []
    expected_phrases: List[str] = []

class ConversationRespondRequest(BaseModel):
    session_id: Optional[Union[UUID, str]] = None
    user_transcript: str

class ConversationRespondResponse(BaseModel):
    session_id: UUID
    target_language_code: Optional[str] = "kn"
    ai_reply: str
    ai_audio_text: str
    phonetic: Optional[str] = None
    translation: Optional[str] = None
    grammar_correction: Optional[str] = None
    pronunciation_tips: List[str] = []
    vocabulary_suggestions: List[str] = []
    current_turn: int
    turn_score: float = 85.0

class ConversationEndRequest(BaseModel):
    session_id: UUID

class ConversationEndResponse(BaseModel):
    session_id: UUID
    composite_score: float
    grammar_score: float
    pronunciation_score: float
    vocabulary_score: float
    total_turns: int
    xp_earned: int
    gems_earned: int
    transcript: List[dict]


# ==========================================
# --- NeoStories Schemas ---
# ==========================================
class StorySceneResponse(BaseModel):
    id: UUID
    scene_number: int
    character_name: str
    character_avatar: Optional[str] = None
    dialogue_target: str
    dialogue_translation: str
    audio_cue_url: Optional[str] = None

class StoryExerciseResponse(BaseModel):
    id: UUID
    scene_number: int
    question_text: str
    options: List[dict]
    exercise_type: str

class StorySummaryResponse(BaseModel):
    id: UUID
    title: str
    target_cefr: str
    icon: str
    xp_reward: int
    gem_reward: int
    order: int
    is_completed: bool = False
    best_score: Optional[float] = None

class StoryDetailResponse(BaseModel):
    id: UUID
    title: str
    target_cefr: str
    icon: str
    xp_reward: int
    gem_reward: int
    scenes: List[StorySceneResponse]
    exercises: List[StoryExerciseResponse]
    is_completed: bool = False

class StoryCompleteSubmit(BaseModel):
    score: float

class StoryCompleteResponse(BaseModel):
    story_id: UUID
    xp_earned: int
    gems_earned: int
    is_completed: bool


# ==========================================
# --- NeoAdventures Schemas ---
# ==========================================
class AdventureStepResponse(BaseModel):
    id: UUID
    step_key: str
    narrative: str
    prompt_in_target: str
    expected_concept: str
    choices: List[dict] = []

class AdventureSummaryResponse(BaseModel):
    id: UUID
    title: str
    scenario_type: str
    intro_text: str
    difficulty_level: int
    xp_reward: int
    is_completed: bool = False

class AdventureDetailResponse(BaseModel):
    id: UUID
    title: str
    scenario_type: str
    intro_text: str
    steps: List[AdventureStepResponse]
    current_step_key: str = "start"
    is_completed: bool = False

class AdventureStepSubmit(BaseModel):
    step_key: str
    chosen_index: Optional[int] = None
    user_spoken_text: Optional[str] = None

class AdventureStepResult(BaseModel):
    next_step_key: str
    narrative_feedback: str
    is_final: bool = False
    xp_earned: int = 0
    is_completed: bool = False


# ==========================================
# --- Practice Hub Schemas ---
# ==========================================
class PracticeModeInfo(BaseModel):
    id: str
    title: str
    desc: str
    icon: str
    badge: Optional[str] = None
    count: Optional[int] = None
    route: str

class PracticeHubOverviewResponse(BaseModel):
    hearts_restore_available: bool
    current_hearts: int
    due_srs_count: int
    mistakes_count: int
    flashcards_deck_size: int
    weak_competencies: List[dict] = []
    active_boost: Optional[dict] = None
    modes: List[PracticeModeInfo]


# ==========================================
# --- Social & Friends & Leagues Schemas ---
# ==========================================
class FriendUserResponse(BaseModel):
    id: UUID
    full_name: str
    email: str
    xp: int
    streak: int
    avatar_initial: str
    friendship_status: str
    friend_streak: int = 0

class FriendRequestAction(BaseModel):
    friend_id: Optional[UUID] = None
    email: Optional[str] = None
    action: str = "send"  # send, accept, decline

class FriendQuestStatusResponse(BaseModel):
    id: Optional[UUID] = None
    has_active_quest: bool = False
    target_xp: int = 2000
    combined_xp: int = 0
    my_xp: int = 0
    friend_xp: int = 0
    friend_name: Optional[str] = None
    gem_reward: int = 100
    days_left: int = 5
    is_completed: bool = False
    claimed: bool = False

class LeagueStandingsResponse(BaseModel):
    tier: LeagueTier
    tier_name: str
    tier_index: int
    user_rank: int
    user_weekly_xp: int
    days_remaining: int
    promotion_zone: int = 5
    demotion_zone: int = 5
    members: List[dict]


# ==========================================
# --- Unit Guidebook & Mastery Schemas ---
# ==========================================
class UnitGuidebookResponse(BaseModel):
    id: UUID
    topic_id: UUID
    title: str
    grammar_notes_md: str
    key_phrases: List[dict]
    common_mistakes_md: Optional[str] = None
    cultural_tips_md: Optional[str] = None

class TopicMasteryResponse(BaseModel):
    topic_id: UUID
    level: UnitMasteryLevel
    legendary_passed: bool
    score: float

class TopicTestOutSubmit(BaseModel):
    answers: List[dict]

class TopicTestOutResponse(BaseModel):
    topic_id: UUID
    score: float
    passed: bool
    new_mastery_level: UnitMasteryLevel
    xp_earned: int
    message: str


# ==========================================
# --- Explain My Answer Schemas ---
# ==========================================
class ExplainMistakeRequest(BaseModel):
    question_id: Optional[UUID] = None
    question_text: Optional[str] = None
    selected_answer_id: Optional[UUID] = None
    user_answer_text: Optional[str] = None
    correct_answer_text: Optional[str] = None

class ExplainMistakeResponse(BaseModel):
    question_text: str
    user_selection_text: str
    correct_answer_text: str
    why_incorrect: str
    grammar_rule: str
    contrast_examples: List[str] = []
    memory_tip: str


# ==========================================
# --- Speech & Pronunciation Schemas ---
# ==========================================
class PronunciationAssessmentRequest(BaseModel):
    target_text: str
    spoken_text: str
    language_code: Optional[str] = "en"
    audio_url: Optional[str] = None

class PronunciationAssessmentResponse(BaseModel):
    id: UUID
    target_text: str
    spoken_text: str
    overall_score: float
    accuracy_score: float
    fluency_score: float
    problematic_words: List[str] = []
    feedback: str
    xp_earned: int = 15
    current_speaking_score: float = 0.0
    created_at: datetime


# ==========================================
# --- Achievement Schemas ---
# ==========================================
class AchievementResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: str
    icon: str
    category: str
    threshold: int
    xp_reward: int
    gem_reward: int
    progress: int = 0
    is_unlocked: bool = False
    unlocked_at: Optional[datetime] = None


# ==========================================
# --- Learning Report Schemas ---
# ==========================================
class LearningReportResponse(BaseModel):
    learner_id: UUID
    learner_name: str
    report_date: datetime
    cefr_level: str
    benchmark_level: str
    composite_score: float
    skill_breakdown: dict
    strengths: List[str]
    weak_areas: List[str]
    lessons_completed_count: int
    total_learning_time_minutes: int
    current_streak: int
    total_xp: int
    unlocked_achievements_count: int
    recommendations: List[str]
    recent_pronunciation_score: float


# ==========================================
# --- Admin Portal Schemas ---
# ==========================================
class AdminOverviewResponse(BaseModel):
    total_learners: int
    active_learners_7d: int
    new_learners_30d: int
    total_lessons: int
    total_completed_lessons: int
    total_assessments_taken: int
    avg_learner_progress_pct: float
    avg_proficiency_score: float
    total_achievements_earned: int

class AdminLearnerDetailResponse(BaseModel):
    id: UUID
    full_name: str
    email: str
    age: Optional[int]
    is_admin: bool
    preferred_language: Optional[str]
    target_language: Optional[str]
    proficiency_level: str
    cefr_level: str
    benchmark_level: str
    predicted_score: float
    xp: int
    gems: int
    hearts: int
    streak: int
    created_at: datetime
    completed_lessons_count: int
    quiz_results_count: int
    recent_scores: List[float]
    weak_areas: List[str]
    strengths: List[str]


# ==========================================
# --- Admin CRUD Payload Schemas ---
# ==========================================
class AdminLearnerCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    age: Optional[int] = 20
    is_admin: bool = False
    proficiency_level: Optional[ProficiencyLevel] = ProficiencyLevel.Beginner
    cefr_level: Optional[str] = "A1"
    xp: Optional[int] = 0
    gems: Optional[int] = 500
    hearts: Optional[int] = 5
    streak: Optional[int] = 0

class AdminLearnerUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    age: Optional[int] = None
    is_admin: Optional[bool] = None
    proficiency_level: Optional[ProficiencyLevel] = None
    cefr_level: Optional[str] = None
    xp: Optional[int] = None
    gems: Optional[int] = None
    hearts: Optional[int] = None
    streak: Optional[int] = None

class AdminCourseCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    language_id: UUID
    level: CourseLevel = CourseLevel.Beginner
    cefr_level: Optional[str] = "A1"
    is_published: bool = True

class AdminCourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    language_id: Optional[UUID] = None
    level: Optional[CourseLevel] = None
    cefr_level: Optional[str] = None
    is_published: Optional[bool] = None

class AdminTopicCreate(BaseModel):
    course_id: UUID
    title: str
    description: Optional[str] = ""
    order: int = 1
    cefr_level: Optional[str] = "A1"

class AdminTopicUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None
    cefr_level: Optional[str] = None

class AdminLessonCreate(BaseModel):
    topic_id: UUID
    title: str
    content: Optional[str] = ""
    order: int = 1
    duration_minutes: int = 10

class AdminLessonUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    order: Optional[int] = None
    duration_minutes: Optional[int] = None

class AdminAchievementCreate(BaseModel):
    code: str
    name: str
    description: str
    icon: str = "🏆"
    category: str = "general"
    threshold: int = 1
    xp_reward: int = 50
    gem_reward: int = 20

class AdminAchievementUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    category: Optional[str] = None
    threshold: Optional[int] = None
    xp_reward: Optional[int] = None
    gem_reward: Optional[int] = None

class AdminStoryCreate(BaseModel):
    title: str
    language_code: str = "kn"
    cefr_level: str = "A1"
    difficulty: str = "Beginner"
    xp_reward: int = 30
    story_json: Optional[str] = "{}"

class AdminStoryUpdate(BaseModel):
    title: Optional[str] = None
    language_code: Optional[str] = None
    cefr_level: Optional[str] = None
    difficulty: Optional[str] = None
    xp_reward: Optional[int] = None
    story_json: Optional[str] = None

class AdminAdventureCreate(BaseModel):
    title: str
    scenario_code: str
    target_language: str = "Kannada"
    difficulty: str = "Beginner"
    system_prompt: str = ""
    starting_message: str = ""

class AdminAdventureUpdate(BaseModel):
    title: Optional[str] = None
    scenario_code: Optional[str] = None
    target_language: Optional[str] = None
    difficulty: Optional[str] = None
    system_prompt: Optional[str] = None
    starting_message: Optional[str] = None

class AdminVocabularyCreate(BaseModel):
    word: str
    translation: str
    language_code: str = "kn"
    pos: Optional[str] = "noun"
    cefr_level: Optional[str] = "A1"
    example_sentence: Optional[str] = ""

class AdminVocabularyUpdate(BaseModel):
    word: Optional[str] = None
    translation: Optional[str] = None
    language_code: Optional[str] = None
    pos: Optional[str] = None
    cefr_level: Optional[str] = None
    example_sentence: Optional[str] = None



