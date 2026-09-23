import uuid
import os
import sys
from typing import Dict
from sqlalchemy.orm import Session

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

try:
    import models
    import auth
except ImportError:
    from . import models
    from . import auth

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
    Optimized to commit in a single batch to avoid SQLite locking on Vercel Serverless.
    """
    lang_map: Dict[str, models.Language] = {}

    try:
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

                                for a_template in q_template["answers"]:
                                    answer = models.Answer(
                                        id=uuid.uuid4(),
                                        question_id=question.id,
                                        text=a_template["text"],
                                        is_correct=a_template["is_correct"],
                                        explanation=a_template.get("explanation")
                                    )
                                    db.add(answer)

        # 3. Seed Default Admin Account
        import auth
        admin_email = "admin@neolearner.com"
        existing_admin = db.query(models.Learner).filter(models.Learner.email == admin_email).first()
        en_lang = lang_map.get("en") or db.query(models.Language).filter(models.Language.code == "en").first()
        kn_lang = lang_map.get("kn") or db.query(models.Language).filter(models.Language.code == "kn").first()

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
        elif existing_admin and (not existing_admin.preferred_language_id or not existing_admin.target_language_id):
            existing_admin.preferred_language_id = en_lang.id if en_lang else None
            existing_admin.target_language_id = kn_lang.id if kn_lang else None

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

        # 5. Seed Vocabulary Dataset across all 6 languages
        VOCABULARY_BY_LANG = {
            "en": [
                {"word": "Hello", "translation": "Greeting phrase", "explanation": "Standard polite greeting"},
                {"word": "Book", "translation": "Reading material", "explanation": "Bound sheets of paper for reading"},
                {"word": "Water", "translation": "Essential liquid", "explanation": "H2O vital for life"},
                {"word": "School", "translation": "Place of learning", "explanation": "Educational institution"},
                {"word": "Friend", "translation": "Companion", "explanation": "Person with whom one has a bond of affection"},
                {"word": "Apple", "translation": "Fruit", "explanation": "Round edible fruit"},
                {"word": "Sun", "translation": "Star of daylight", "explanation": "Central star of solar system"},
                {"word": "Read", "translation": "Literacy action", "explanation": "Look at and comprehend written words"},
                {"word": "Write", "translation": "Literacy action", "explanation": "Mark letters or symbols on paper"},
                {"word": "Learn", "translation": "Education action", "explanation": "Gain knowledge or skill through study"}
            ],
            "kn": [
                {"word": "ನಮಸ್ಕಾರ", "translation": "Hello / Greeting", "explanation": "ಕನ್ನಡ ಸಾಂಪ್ರದಾಯಿಕ ಶುಭಾಶಯ"},
                {"word": "ಪುಸ್ತಕ", "translation": "Book", "explanation": "ಓದಲು ಬಳಸುವ ಗ್ರಂಥ"},
                {"word": "ನೀರು", "translation": "Water", "explanation": "ಜೀವಜಲ"},
                {"word": "ಶಾಲೆ", "translation": "School", "explanation": "ವಿದ್ಯಾಲಯ"},
                {"word": "ಸ್ನೇಹಿತ", "translation": "Friend", "explanation": "ಆಪ್ತ ಮಿತ್ರ"},
                {"word": "ಸೇಬು", "translation": "Apple", "explanation": "ಸಿಹಿ ಹಣ್ಣು"},
                {"word": "ಸೂರ್ಯ", "translation": "Sun", "explanation": "ಬೆಳಕು ನೀಡುವ ಸೂರ್ಯದೇವ"},
                {"word": "ಓದು", "translation": "Read", "explanation": "ಅಕ್ಷರಗಳನ್ನು ಓದುವ ಕ್ರಿಯೆ"},
                {"word": "ಬರೆ", "translation": "Write", "explanation": "ಅಕ್ಷರಗಳನ್ನು ಬರೆಯುವ ಕ್ರಿಯೆ"},
                {"word": "ಕಲಿ", "translation": "Learn", "explanation": "ಜ್ಞಾನ ಪಡೆದುಕೊಳ್ಳುವುದು"}
            ],
            "te": [
                {"word": "నమస్కారం", "translation": "Hello / Greeting", "explanation": "తెలుగు సాంప్రదాయ నమస్కారం"},
                {"word": "పుస్తకం", "translation": "Book", "explanation": "చదివే గ్రంథం"},
                {"word": "నీరు", "translation": "Water", "explanation": "తాగునీరు"},
                {"word": "బడి", "translation": "School", "explanation": "పాఠశాల"},
                {"word": "స్నేహితుడు", "translation": "Friend", "explanation": "మిత్రుడు"},
                {"word": "ఆపిల్", "translation": "Apple", "explanation": "పండు"},
                {"word": "సూర్యుడు", "translation": "Sun", "explanation": "వెలుగు నిచ్చే సూర్యుడు"},
                {"word": "చదువు", "translation": "Read", "explanation": "అక్షరాలు చదవడం"},
                {"word": "రాయి", "translation": "Write", "explanation": "రాయడం"},
                {"word": "నేర్చుకో", "translation": "Learn", "explanation": "విద్య అభ్యసించడం"}
            ],
            "mr": [
                {"word": "नमस्कार", "translation": "Hello / Greeting", "explanation": "मराठी पारंपारिक नमस्कार"},
                {"word": "पुस्तक", "translation": "Book", "explanation": "वाचनाचे पुस्तक"},
                {"word": "पाणी", "translation": "Water", "explanation": "पिण्याचे पाणी"},
                {"word": "शाळा", "translation": "School", "explanation": "शाळा / विद्यालय"},
                {"word": "मित्र", "translation": "Friend", "explanation": "सखा / मित्र"},
                {"word": "सफरचंद", "translation": "Apple", "explanation": "फळ"},
                {"word": "सूर्य", "translation": "Sun", "explanation": "प्रकाश देणारा सूर्य"},
                {"word": "वाच", "translation": "Read", "explanation": "वाचन करणे"},
                {"word": "लिही", "translation": "Write", "explanation": "लेखन करणे"},
                {"word": "शिक", "translation": "Learn", "explanation": "ज्ञान मिळवणे"}
            ],
            "hi": [
                {"word": "नमस्ते", "translation": "Hello / Greeting", "explanation": "हिन्दी अभिवादन"},
                {"word": "किताब", "translation": "Book", "explanation": "पढ़ने की पुस्तक"},
                {"word": "पानी", "translation": "Water", "explanation": "पेय जल"},
                {"word": "विद्यालय", "translation": "School", "explanation": "पाठशाला"},
                {"word": "मित्र", "translation": "Friend", "explanation": "दोस्त"},
                {"word": "सेब", "translation": "Apple", "explanation": "फल"},
                {"word": "सूर्य", "translation": "Sun", "explanation": "सूरज"},
                {"word": "पढ़ो", "translation": "Read", "explanation": "पढ़ना"},
                {"word": "लिखो", "translation": "Write", "explanation": "लिखना"},
                {"word": "सीखो", "translation": "Learn", "explanation": "ज्ञान अर्जित करना"}
            ],
            "es": [
                {"word": "Hola", "translation": "Hello", "explanation": "Saludos en español"},
                {"word": "Libro", "translation": "Book", "explanation": "Texto para leer"},
                {"word": "Agua", "translation": "Water", "explanation": "Líquido vital"},
                {"word": "Escuela", "translation": "School", "explanation": "Lugar de aprendizaje"},
                {"word": "Amigo", "translation": "Friend", "explanation": "Compañero afectuoso"},
                {"word": "Manzana", "translation": "Apple", "explanation": "Fruta comestible"},
                {"word": "Sol", "translation": "Sun", "explanation": "Estrella central"},
                {"word": "Leer", "translation": "Read", "explanation": "Acción de leer"},
                {"word": "Escribir", "translation": "Write", "explanation": "Acción de escribir"},
                {"word": "Aprender", "translation": "Learn", "explanation": "Adquirir conocimiento"}
            ]
        }

        for lang_code, vocab_list in VOCABULARY_BY_LANG.items():
            lang_obj = lang_map.get(lang_code) or db.query(models.Language).filter(models.Language.code == lang_code).first()
            if lang_obj:
                for v_item in vocab_list:
                    existing_vocab = db.query(models.Vocabulary).filter(
                        models.Vocabulary.language_id == lang_obj.id,
                        models.Vocabulary.word == v_item["word"]
                    ).first()
                    if not existing_vocab:
                        new_vocab = models.Vocabulary(
                            id=uuid.uuid4(),
                            language_id=lang_obj.id,
                            word=v_item["word"],
                            translation=v_item["translation"],
                            explanation=v_item["explanation"],
                            difficulty_level=1
                        )
                        db.add(new_vocab)

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[WARN] Error during database seeding: {e}")


