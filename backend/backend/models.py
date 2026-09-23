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
    match_pairs = "match_pairs"
    word_order = "word_order"
    listening = "listening"
    speaking = "speaking"

class FriendshipStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"

class LeagueTier(str, enum.Enum):
    Bronze = "Bronze"
    Silver = "Silver"
    Gold = "Gold"
    Sapphire = "Sapphire"
    Ruby = "Ruby"
    Emerald = "Emerald"
    Amethyst = "Amethyst"
    Pearl = "Pearl"
    Obsidian = "Obsidian"
    Diamond = "Diamond"

class UnitMasteryLevel(str, enum.Enum):
    not_started = "not_started"
    learning = "learning"
    practiced = "practiced"
    mastered = "mastered"
    legendary = "legendary"


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
    age = Column(Integer, nullable=True)
    
    # Auth & Verification fields
    is_verified = Column(Boolean, default=False)
    verification_code = Column(String, nullable=True)
    google_id = Column(String, nullable=True, index=True)
    avatar_url = Column(String, nullable=True)
    
    preferred_language_id = Column(Uuid(as_uuid=True), ForeignKey('languages.id'), nullable=True)
    target_language_id = Column(Uuid(as_uuid=True), ForeignKey('languages.id'), nullable=True)
    
    proficiency_level = Column(Enum(ProficiencyLevel), default=ProficiencyLevel.Beginner)
    predicted_proficiency_score = Column(Float, default=0.0)
    benchmark_level = Column(String, default="Emergent Reader")
    has_completed_placement_test = Column(Boolean, default=False)
    placement_score = Column(Float, nullable=True)
    
    # Onboarding & CEFR Level Fields
    learning_goal = Column(String, nullable=True, default="conversation")
    prior_knowledge = Column(String, nullable=True, default="complete_beginner")
    cefr_level = Column(String, nullable=True, default="A0")
    daily_minutes_goal = Column(Integer, default=15)
    
    # Gamification Fields
    xp = Column(Integer, default=0)
    gems = Column(Integer, default=500)
    hearts = Column(Integer, default=5)
    streak = Column(Integer, default=0)
    last_active_date = Column(DateTime(timezone=True), nullable=True)
    streak_freeze_count = Column(Integer, default=0)
    double_or_nothing_active = Column(Boolean, default=False)
    double_or_nothing_streak = Column(Integer, default=0)
    last_heart_recharge = Column(DateTime(timezone=True), default=datetime.utcnow)
    daily_xp_goal = Column(Integer, default=20)
    daily_xp_earned = Column(Integer, default=0)
    last_goal_completed_date = Column(DateTime(timezone=True), nullable=True)
    league_tier = Column(Enum(LeagueTier), default=LeagueTier.Bronze)
    is_admin = Column(Boolean, default=False)
    
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
    
    # Recommendation Engine Metadata
    cefr_level = Column(String, default="A1")
    min_score = Column(Float, default=0.0)
    max_score = Column(Float, default=100.0)
    prerequisites_json = Column(Text, default="[]")
    skills_json = Column(Text, default="[]")
    difficulty = Column(String, default="beginner")
    goals_json = Column(Text, default="[]")
    
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
    competency_tag = Column(String, default="phonics")  # phonics, vocabulary, grammar, reading

    # Relationships
    topic = relationship("Topic", back_populates="lessons")
    assessments = relationship("Assessment", back_populates="lesson", cascade="all, delete-orphan")
    progress_records = relationship("LearningProgress", back_populates="lesson", cascade="all, delete-orphan")

    @property
    def language_code(self):
        if self.topic and self.topic.course and self.topic.course.language:
            return self.topic.course.language.code
        return "en"


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

    @property
    def language_code(self):
        if self.lesson:
            return self.lesson.language_code
        return "en"


class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(Uuid(as_uuid=True), ForeignKey('assessments.id'), nullable=False)
    text = Column(Text, nullable=False)
    type = Column(Enum(QuestionType), default=QuestionType.multiple_choice)
    points = Column(Integer, default=1)
    competency_tag = Column(String, default="reading")  # reading, writing, comprehension, listening, speaking, phonics
    difficulty_level = Column(Integer, default=1)  # 1 (Basic/Phonics) to 5 (Advanced Fluency)

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
    assessment_id = Column(Uuid(as_uuid=True), ForeignKey('assessments.id'), nullable=True)
    score = Column(Float, nullable=False)
    max_score = Column(Float, default=100.0)
    passed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # CEFR & Skill Diagnostics
    cefr_level = Column(String, nullable=True)
    skill_breakdown = Column(Text, nullable=True)
    strengths = Column(Text, nullable=True)
    weak_areas = Column(Text, nullable=True)

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


class Vocabulary(Base):
    __tablename__ = "vocabulary"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    language_id = Column(Uuid(as_uuid=True), ForeignKey('languages.id'), nullable=False)
    word = Column(String, nullable=False)
    translation = Column(String, nullable=False)
    explanation = Column(Text, nullable=True)
    difficulty_level = Column(Integer, default=1)  # 1 (Basic) to 5 (Advanced)
    
    # Relationships
    language = relationship("Language")


class VocabularySRS(Base):
    __tablename__ = "vocabulary_srs"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learner_id = Column(Uuid(as_uuid=True), ForeignKey('learners.id'), nullable=False)
    vocabulary_id = Column(Uuid(as_uuid=True), ForeignKey('vocabulary.id'), nullable=False)
    
    # SM-2 Spaced Repetition Parameters
    interval = Column(Integer, default=1)  # Interval in days
    ease_factor = Column(Float, default=2.5)  # Ease factor
    repetitions = Column(Integer, default=0)  # Number of consecutive successful repetitions
    
    next_review_date = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_reviewed_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    learner = relationship("Learner")
    vocabulary = relationship("Vocabulary")


class ReviewItem(Base):
    __tablename__ = "review_items"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learner_id = Column(Uuid(as_uuid=True), ForeignKey('learners.id'), nullable=False)
    question_id = Column(Uuid(as_uuid=True), ForeignKey('questions.id'), nullable=False)
    
    incorrect_answer = Column(Text, nullable=True)
    review_count = Column(Integer, default=1)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    learner = relationship("Learner")
    question = relationship("Question")


class Friendship(Base):
    __tablename__ = "friendships"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requester_id = Column(Uuid(as_uuid=True), ForeignKey('learners.id'), nullable=False)
    receiver_id = Column(Uuid(as_uuid=True), ForeignKey('learners.id'), nullable=False)
    status = Column(Enum(FriendshipStatus), default=FriendshipStatus.pending)
    streak_count = Column(Integer, default=0)
    last_interaction = Column(DateTime(timezone=True), default=datetime.utcnow)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    requester = relationship("Learner", foreign_keys=[requester_id])
    receiver = relationship("Learner", foreign_keys=[receiver_id])


class FriendQuest(Base):
    __tablename__ = "friends_quests"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learner_one_id = Column(Uuid(as_uuid=True), ForeignKey('learners.id'), nullable=False)
    learner_two_id = Column(Uuid(as_uuid=True), ForeignKey('learners.id'), nullable=False)
    target_xp = Column(Integer, default=2000)
    learner_one_xp = Column(Integer, default=0)
    learner_two_xp = Column(Integer, default=0)
    gem_reward = Column(Integer, default=100)
    starts_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    ends_at = Column(DateTime(timezone=True), nullable=False)
    is_completed = Column(Boolean, default=False)
    claimed_one = Column(Boolean, default=False)
    claimed_two = Column(Boolean, default=False)

    # Relationships
    learner_one = relationship("Learner", foreign_keys=[learner_one_id])
    learner_two = relationship("Learner", foreign_keys=[learner_two_id])


class LeagueGroup(Base):
    __tablename__ = "league_groups"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tier = Column(Enum(LeagueTier), default=LeagueTier.Bronze)
    week_start = Column(DateTime(timezone=True), nullable=False)
    week_end = Column(DateTime(timezone=True), nullable=False)
    is_settled = Column(Boolean, default=False)

    members = relationship("LeagueMember", back_populates="group", cascade="all, delete-orphan")


class LeagueMember(Base):
    __tablename__ = "league_members"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(Uuid(as_uuid=True), ForeignKey('league_groups.id'), nullable=False)
    learner_id = Column(Uuid(as_uuid=True), ForeignKey('learners.id'), nullable=True)
    display_name = Column(String, nullable=False)
    weekly_xp = Column(Integer, default=0)
    is_simulated = Column(Boolean, default=False)
    rank = Column(Integer, default=1)

    group = relationship("LeagueGroup", back_populates="members")
    learner = relationship("Learner")


class Story(Base):
    __tablename__ = "stories"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    language_id = Column(Uuid(as_uuid=True), ForeignKey('languages.id'), nullable=False)
    title = Column(String, nullable=False)
    target_cefr = Column(String, default="A1")
    icon = Column(String, default="📖")
    xp_reward = Column(Integer, default=30)
    gem_reward = Column(Integer, default=15)
    order = Column(Integer, default=1)

    language = relationship("Language")
    scenes = relationship("StoryScene", back_populates="story", cascade="all, delete-orphan", order_by="StoryScene.scene_number")
    exercises = relationship("StoryExercise", back_populates="story", cascade="all, delete-orphan", order_by="StoryExercise.scene_number")
    progress = relationship("StoryProgress", back_populates="story", cascade="all, delete-orphan")


class StoryScene(Base):
    __tablename__ = "story_scenes"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    story_id = Column(Uuid(as_uuid=True), ForeignKey('stories.id'), nullable=False)
    scene_number = Column(Integer, nullable=False)
    character_name = Column(String, nullable=False)
    character_avatar = Column(String, nullable=True)
    dialogue_target = Column(Text, nullable=False)
    dialogue_translation = Column(Text, nullable=False)
    audio_cue_url = Column(String, nullable=True)

    story = relationship("Story", back_populates="scenes")


class StoryExercise(Base):
    __tablename__ = "story_exercises"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    story_id = Column(Uuid(as_uuid=True), ForeignKey('stories.id'), nullable=False)
    scene_number = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    options_json = Column(Text, nullable=False)
    exercise_type = Column(String, default="comprehension")

    story = relationship("Story", back_populates="exercises")


class StoryProgress(Base):
    __tablename__ = "story_progress"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learner_id = Column(Uuid(as_uuid=True), ForeignKey('learners.id'), nullable=False)
    story_id = Column(Uuid(as_uuid=True), ForeignKey('stories.id'), nullable=False)
    is_completed = Column(Boolean, default=False)
    score = Column(Float, default=100.0)
    completed_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    learner = relationship("Learner")
    story = relationship("Story", back_populates="progress")


class Adventure(Base):
    __tablename__ = "adventures"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    language_id = Column(Uuid(as_uuid=True), ForeignKey('languages.id'), nullable=False)
    title = Column(String, nullable=False)
    scenario_type = Column(String, nullable=False)
    intro_text = Column(Text, nullable=False)
    difficulty_level = Column(Integer, default=1)
    xp_reward = Column(Integer, default=60)

    language = relationship("Language")
    steps = relationship("AdventureStep", back_populates="adventure", cascade="all, delete-orphan")
    progress = relationship("AdventureProgress", back_populates="adventure", cascade="all, delete-orphan")


class AdventureStep(Base):
    __tablename__ = "adventure_steps"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    adventure_id = Column(Uuid(as_uuid=True), ForeignKey('adventures.id'), nullable=False)
    step_key = Column(String, nullable=False)
    narrative = Column(Text, nullable=False)
    prompt_in_target = Column(Text, nullable=False)
    expected_concept = Column(String, nullable=False)
    choices_json = Column(Text, nullable=True)

    adventure = relationship("Adventure", back_populates="steps")


class AdventureProgress(Base):
    __tablename__ = "adventure_progress"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learner_id = Column(Uuid(as_uuid=True), ForeignKey('learners.id'), nullable=False)
    adventure_id = Column(Uuid(as_uuid=True), ForeignKey('adventures.id'), nullable=False)
    current_step_key = Column(String, default="start")
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    learner = relationship("Learner")
    adventure = relationship("Adventure", back_populates="progress")


class ConversationSession(Base):
    __tablename__ = "conversation_sessions"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learner_id = Column(Uuid(as_uuid=True), ForeignKey('learners.id'), nullable=False)
    scenario = Column(String, nullable=False)
    language_id = Column(Uuid(as_uuid=True), ForeignKey('languages.id'), nullable=False)
    cefr_target = Column(String, default="A1")
    grammar_score = Column(Float, default=0.0)
    pronunciation_score = Column(Float, default=0.0)
    vocabulary_score = Column(Float, default=0.0)
    total_turns = Column(Integer, default=0)
    transcript_json = Column(Text, default="[]")
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    learner = relationship("Learner")
    language = relationship("Language")


class TopicMastery(Base):
    __tablename__ = "topic_mastery"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learner_id = Column(Uuid(as_uuid=True), ForeignKey('learners.id'), nullable=False)
    topic_id = Column(Uuid(as_uuid=True), ForeignKey('topics.id'), nullable=False)
    level = Column(Enum(UnitMasteryLevel), default=UnitMasteryLevel.not_started)
    legendary_passed = Column(Boolean, default=False)
    score = Column(Float, default=0.0)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    learner = relationship("Learner")
    topic = relationship("Topic")


class UnitGuidebook(Base):
    __tablename__ = "unit_guidebooks"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id = Column(Uuid(as_uuid=True), ForeignKey('topics.id'), unique=True, nullable=False)
    title = Column(String, nullable=False)
    grammar_notes_md = Column(Text, nullable=False)
    key_phrases_json = Column(Text, nullable=False)
    common_mistakes_md = Column(Text, nullable=True)
    cultural_tips_md = Column(Text, nullable=True)

    topic = relationship("Topic")


class LearnerBoost(Base):
    __tablename__ = "learner_boosts"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learner_id = Column(Uuid(as_uuid=True), ForeignKey('learners.id'), nullable=False)
    boost_type = Column(String, default="2x_xp")
    multiplier = Column(Float, default=2.0)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)

    learner = relationship("Learner")


class MonthlyChallenge(Base):
    __tablename__ = "monthly_challenges"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    target_type = Column(String, default="speaking_sessions")
    target_count = Column(Integer, default=20)
    gem_reward = Column(Integer, default=500)
    badge_icon = Column(String, default="🏆")


class SmartNotification(Base):
    __tablename__ = "smart_notifications"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learner_id = Column(Uuid(as_uuid=True), ForeignKey('learners.id'), nullable=False)
    type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    action_url = Column(String, default="/dashboard")
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    learner = relationship("Learner")


class PronunciationAttempt(Base):
    __tablename__ = "pronunciation_attempts"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learner_id = Column(Uuid(as_uuid=True), ForeignKey('learners.id'), nullable=False)
    target_text = Column(Text, nullable=False)
    spoken_text = Column(Text, nullable=False)
    audio_url = Column(String, nullable=True)
    overall_score = Column(Float, default=0.0)
    accuracy_score = Column(Float, default=0.0)
    fluency_score = Column(Float, default=0.0)
    problematic_words_json = Column(Text, default="[]")
    feedback = Column(Text, nullable=True)
    language_code = Column(String, default="en")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    learner = relationship("Learner")


class AchievementDefinition(Base):
    __tablename__ = "achievement_definitions"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    icon = Column(String, default="🏆")
    category = Column(String, default="milestone")  # lessons, streak, speaking, xp, milestone
    threshold = Column(Integer, default=1)
    xp_reward = Column(Integer, default=50)
    gem_reward = Column(Integer, default=25)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class LearnerAchievement(Base):
    __tablename__ = "learner_achievements"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learner_id = Column(Uuid(as_uuid=True), ForeignKey('learners.id'), nullable=False)
    achievement_id = Column(Uuid(as_uuid=True), ForeignKey('achievement_definitions.id'), nullable=False)
    progress = Column(Integer, default=0)
    is_unlocked = Column(Boolean, default=False)
    unlocked_at = Column(DateTime(timezone=True), nullable=True)

    learner = relationship("Learner")
    achievement = relationship("AchievementDefinition")


class LearningReport(Base):
    __tablename__ = "learning_reports"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learner_id = Column(Uuid(as_uuid=True), ForeignKey('learners.id'), nullable=False)
    report_date = Column(DateTime(timezone=True), default=datetime.utcnow)
    report_data_json = Column(Text, nullable=False)

    learner = relationship("Learner")

