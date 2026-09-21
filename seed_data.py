import uuid
from typing import Dict
from sqlalchemy.orm import Session
import models

LANGUAGES_TO_SEED = [
    {"code": "en", "name": "English", "native_name": "English"},
    {"code": "kn", "name": "Kannada", "native_name": "ಕನ್ನಡ"},
    {"code": "te", "name": "Telugu", "native_name": "తెలుగు"},
    {"code": "mr", "name": "Marathi", "native_name": "मराठी"},
    {"code": "hi", "name": "Hindi", "native_name": "हिन्दी"},
    {"code": "es", "name": "Spanish", "native_name": "Español"}
]

COURSES_TO_SEED = [
    {
        "lang_code": "en",
        "title": "English Literacy Foundations",
        "description": "Master English alphabet, phonics, vocabulary, and basic sentence construction.",
        "level": models.CourseLevel.Beginner,
        "cefr_level": "A1"
    },
    {
        "lang_code": "kn",
        "title": "Kannada Literacy Foundations",
        "description": "ಕನ್ನಡ ಅಕ್ಷರಮಾಲೆ, ಕಾಗುಣಿತ, ಶಬ್ದಕೋಶ ಮತ್ತು ವಾಕ್ಯ ರಚನೆ ಕಲಿಕೆ.",
        "level": models.CourseLevel.Beginner,
        "cefr_level": "A1"
    },
    {
        "lang_code": "te",
        "title": "Telugu Literacy Foundations",
        "description": "తెలుగు అక్షరమాల, పదజాలం మరియు వాక్య నిర్మాణం అభ్యసించండి.",
        "level": models.CourseLevel.Beginner,
        "cefr_level": "A1"
    },
    {
        "lang_code": "mr",
        "title": "Marathi Literacy Foundations",
        "description": "मराठी मुळाक्षरे, शब्दसंग्रह आणि वाक्यरचना सराव.",
        "level": models.CourseLevel.Beginner,
        "cefr_level": "A1"
    },
    {
        "lang_code": "hi",
        "title": "Hindi Literacy Foundations",
        "description": "हिन्दी वर्णमाला, शब्दावली और वाक्य निर्माण का बुनियादी सराव।",
        "level": models.CourseLevel.Beginner,
        "cefr_level": "A1"
    },
    {
        "lang_code": "es",
        "title": "Elementary Spanish Literacy",
        "description": "Introductory literacy course for phonics, vocabulary, and basic conversation.",
        "level": models.CourseLevel.Beginner,
        "cefr_level": "A1"
    }
]

TOPICS_TEMPLATES = [
    {
        "order": 1,
        "title": "Alphabet & Phonics",
        "description": "Learn basic letter sounds, vowels, and character recognition.",
        "lessons": [
            {
                "order": 1,
                "title": "Letter Sounds A-M",
                "content": "Phonics practice for vowels and foundational letter sounds.",
                "duration_minutes": 15,
                "assessment": {
                    "title": "Alphabet & Phonics Quiz Checkpoint",
                    "questions": [
                        {
                            "text": "Identify the vowel sound in the vocabulary deck.",
                            "type": models.QuestionType.multiple_choice,
                            "competency_tag": "phonics",
                            "difficulty_level": 1,
                            "answers": [
                                {"text": "A / Ah", "is_correct": True, "explanation": "Short vowel sound A"},
                                {"text": "B / Buh", "is_correct": False},
                                {"text": "C / Cuh", "is_correct": False},
                                {"text": "D / Duh", "is_correct": False}
                            ]
                        },
                        {
                            "text": "Listen to the spoken audio and select the matching word.",
                            "type": models.QuestionType.listening,
                            "competency_tag": "listening",
                            "difficulty_level": 1,
                            "answers": [
                                {"text": "Hello", "is_correct": True, "explanation": "Greeting sound match"},
                                {"text": "Book", "is_correct": False},
                                {"text": "Water", "is_correct": False}
                            ]
                        }
                    ]
                }
            }
        ]
    },
    {
        "order": 2,
        "title": "Vocabulary & Words",
        "description": "Build essential daily vocabulary for nouns, food, and objects.",
        "lessons": [
            {
                "order": 2,
                "title": "Common Nouns & Objects",
                "content": "Learn common words for objects in daily environment.",
                "duration_minutes": 20,
                "assessment": {
                    "title": "Vocabulary & Words Quiz Checkpoint",
                    "questions": [
                        {
                            "text": "Match the word to its meaning:",
                            "type": models.QuestionType.multiple_choice,
                            "competency_tag": "vocabulary",
                            "difficulty_level": 2,
                            "answers": [
                                {"text": "Book / Reading item", "is_correct": True},
                                {"text": "Milk", "is_correct": False},
                                {"text": "Water", "is_correct": False}
                            ]
                        },
                        {
                            "text": "hello:Hello,milk:Milk,book:Book",
                            "type": models.QuestionType.match_pairs,
                            "competency_tag": "vocabulary",
                            "difficulty_level": 2,
                            "answers": [
                                {"text": "hello:Hello,milk:Milk,book:Book", "is_correct": True}
                            ]
                        }
                    ]
                }
            }
        ]
    },
    {
        "order": 3,
        "title": "Grammar & Sentences",
        "description": "Understand basic sentence structure and subject-verb agreement.",
        "lessons": [
            {
                "order": 3,
                "title": "Sentence Formation",
                "content": "Form simple sentences using subject, object, and verb rules.",
                "duration_minutes": 20,
                "assessment": {
                    "title": "Grammar & Sentences Quiz Checkpoint",
                    "questions": [
                        {
                            "text": "Fill in the blank with the correct spelling.",
                            "type": models.QuestionType.fill_in_blank,
                            "competency_tag": "writing",
                            "difficulty_level": 3,
                            "answers": [
                                {"text": "read", "is_correct": True, "explanation": "Correct spelling of read"}
                            ]
                        }
                    ]
                }
            }
        ]
    },
    {
        "order": 4,
        "title": "Reading Comprehension",
        "description": "Read simple paragraphs and answer comprehension questions.",
        "lessons": [
            {
                "order": 4,
                "title": "Paragraph Reading",
                "content": "Practice reading short stories and identifying main ideas.",
                "duration_minutes": 25,
                "assessment": {
                    "title": "Reading Comprehension Quiz Checkpoint",
                    "questions": [
                        {
                            "text": "Pronounce the target sentence out loud into the microphone.",
                            "type": models.QuestionType.speaking,
                            "competency_tag": "speaking",
                            "difficulty_level": 3,
                            "answers": [
                                {"text": "Hello friend", "is_correct": True}
                            ]
                        }
                    ]
                }
            }
        ]
    }
]

def seed_initial_database(db: Session):
    """
    Ensures all 6 supported languages (en, kn, te, mr, hi, es) exist in the languages table
    and that published foundational courses exist for each language in the database.
    """
    lang_map: Dict[str, models.Language] = {}

    # 1. Seed Languages
    for l_data in LANGUAGES_TO_SEED:
        existing_lang = db.query(models.Language).filter(models.Language.code == l_data["code"]).first()
        if not existing_lang:
            new_lang = models.Language(
                id=uuid.uuid4(),
                code=l_data["code"],
                name=l_data["name"],
                native_name=l_data["native_name"]
            )
            db.add(new_lang)
            db.commit()
            db.refresh(new_lang)
            lang_map[l_data["code"]] = new_lang
        else:
            lang_map[l_data["code"]] = existing_lang

    # 2. Seed Courses for Each Language
    for c_data in COURSES_TO_SEED:
        target_lang = lang_map.get(c_data["lang_code"])
        if not target_lang:
            continue

        existing_course = db.query(models.Course).filter(
            models.Course.language_id == target_lang.id,
            models.Course.title == c_data["title"]
        ).first()

        if not existing_course:
            course = models.Course(
                id=uuid.uuid4(),
                language_id=target_lang.id,
                title=c_data["title"],
                description=c_data["description"],
                level=c_data["level"],
                cefr_level=c_data["cefr_level"],
                is_published=True
            )
            db.add(course)
            db.commit()
            db.refresh(course)

            # Seed Topics, Lessons, Assessments for Course
            for t_template in TOPICS_TEMPLATES:
                topic = models.Topic(
                    id=uuid.uuid4(),
                    course_id=course.id,
                    title=t_template["title"],
                    description=t_template["description"],
                    order=t_template["order"]
                )
                db.add(topic)
                db.commit()
                db.refresh(topic)

                for l_template in t_template["lessons"]:
                    lesson = models.Lesson(
                        id=uuid.uuid4(),
                        topic_id=topic.id,
                        title=l_template["title"],
                        content=l_template["content"],
                        duration_minutes=l_template["duration_minutes"],
                        order=l_template["order"]
                    )
                    db.add(lesson)
                    db.commit()
                    db.refresh(lesson)

                    ass_template = l_template.get("assessment")
                    if ass_template:
                        assessment = models.Assessment(
                            id=uuid.uuid4(),
                            lesson_id=lesson.id,
                            title=ass_template["title"],
                            type=models.AssessmentType.quiz,
                            pass_percentage=70.0
                        )
                        db.add(assessment)
                        db.commit()
                        db.refresh(assessment)

                        for q_template in ass_template["questions"]:
                            question = models.Question(
                                id=uuid.uuid4(),
                                assessment_id=assessment.id,
                                text=q_template["text"],
                                type=q_template["type"],
                                points=1,
                                competency_tag=q_template["competency_tag"],
                                difficulty_level=q_template["difficulty_level"]
                            )
                            db.add(question)
                            db.commit()
                            db.refresh(question)

                            for a_template in q_template["answers"]:
                                answer = models.Answer(
                                    id=uuid.uuid4(),
                                    question_id=question.id,
                                    text=a_template["text"],
                                    is_correct=a_template["is_correct"],
                                    explanation=a_template.get("explanation")
                                )
                                db.add(answer)
                            db.commit()

    # 3. Seed Default Admin Account
    import auth
    admin_email = "admin@neolearner.com"
    existing_admin = db.query(models.Learner).filter(models.Learner.email == admin_email).first()
    en_lang = db.query(models.Language).filter(models.Language.code == "en").first()
    kn_lang = db.query(models.Language).filter(models.Language.code == "kn").first()

    if not existing_admin:
        admin_user = models.Learner(
            id=uuid.uuid4(),
            email=admin_email,
            hashed_password=auth.get_password_hash("AdminPass123!"),
            full_name="System Administrator",
            is_admin=True,
            preferred_language_id=en_lang.id if en_lang else None,
            target_language_id=kn_lang.id if kn_lang else None,
            proficiency_level=models.ProficiencyLevel.Advanced,
            cefr_level="C2",
            benchmark_level="Proficient Master (C2)",
            has_completed_placement_test=True,
            placement_score=100.0,
            xp=2500,
            gems=2000,
            hearts=5,
            streak=14
        )
        db.add(admin_user)
        db.commit()
    elif existing_admin and (not existing_admin.preferred_language_id or not existing_admin.target_language_id):
        existing_admin.preferred_language_id = en_lang.id if en_lang else None
        existing_admin.target_language_id = kn_lang.id if kn_lang else None
        db.commit()

    # 4. Seed 10 Standard Achievement Definitions
    ACHIEVEMENTS_TO_SEED = [
        {"code": "first_lesson", "name": "First Step", "description": "Complete your first lesson in any language course.", "icon": "🚀", "category": "lessons", "threshold": 1, "xp_reward": 50, "gem_reward": 25},
        {"code": "lessons_5", "name": "Scholar", "description": "Complete 5 interactive literacy lessons.", "icon": "📚", "category": "lessons", "threshold": 5, "xp_reward": 100, "gem_reward": 50},
        {"code": "lessons_10", "name": "Literacy Champion", "description": "Complete 10 interactive lessons across topics.", "icon": "🎓", "category": "lessons", "threshold": 10, "xp_reward": 200, "gem_reward": 100},
        {"code": "streak_3", "name": "3-Day Streak", "description": "Maintain active learning for 3 consecutive days.", "icon": "🔥", "category": "streak", "threshold": 3, "xp_reward": 75, "gem_reward": 30},
        {"code": "streak_7", "name": "7-Day Warrior", "description": "Maintain active learning for a full 7 days.", "icon": "⚡", "category": "streak", "threshold": 7, "xp_reward": 150, "gem_reward": 75},
        {"code": "speaking_1", "name": "Voice Pioneer", "description": "Complete 1 pronunciation assessment in the Speaking Lab.", "icon": "🎤", "category": "speaking", "threshold": 1, "xp_reward": 50, "gem_reward": 25},
        {"code": "speaking_5", "name": "Speech Master", "description": "Complete 5 pronunciation practice sessions with >75% accuracy.", "icon": "🎧", "category": "speaking", "threshold": 5, "xp_reward": 150, "gem_reward": 60},
        {"code": "xp_500", "name": "500 XP Milestone", "description": "Earn 500 total XP points across drills and exercises.", "icon": "🌟", "category": "xp", "threshold": 500, "xp_reward": 100, "gem_reward": 50},
        {"code": "xp_1000", "name": "1,000 XP Master", "description": "Earn 1,000 total XP points.", "icon": "👑", "category": "xp", "threshold": 1000, "xp_reward": 250, "gem_reward": 125},
        {"code": "placement_done", "name": "Diagnostic Certified", "description": "Complete the 15-question initial diagnostic exam.", "icon": "🎖️", "category": "milestones", "threshold": 1, "xp_reward": 100, "gem_reward": 50}
    ]

    for ach_data in ACHIEVEMENTS_TO_SEED:
        existing_ach = db.query(models.AchievementDefinition).filter(models.AchievementDefinition.code == ach_data["code"]).first()
        if not existing_ach:
            new_ach = models.AchievementDefinition(
                id=uuid.uuid4(),
                code=ach_data["code"],
                name=ach_data["name"],
                description=ach_data["description"],
                icon=ach_data["icon"],
                category=ach_data["category"],
                threshold=ach_data["threshold"],
                xp_reward=ach_data["xp_reward"],
                gem_reward=ach_data["gem_reward"]
            )
            db.add(new_ach)
            db.commit()

