import uuid
import sys
import os
import json
from datetime import datetime

# Adjust sys.path to allow importing backend modules
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from backend.database import SessionLocal, engine
from backend.models import (
    Base, Language, Learner, Course, Topic, Lesson,
    Assessment, Question, Answer, AssessmentResult, LearningProgress, Recommendation,
    Vocabulary, VocabularySRS, ReviewItem,
    ProficiencyLevel, CourseLevel, ProgressStatus, AssessmentType, QuestionType
)
from backend.auth import get_password_hash

def seed_database():
    print("Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        print("Seeding Languages (English, Kannada, Telugu, Marathi, Hindi)...")
        languages_data = [
            {"name": "English", "code": "en", "native_name": "English"},
            {"name": "Kannada", "code": "kn", "native_name": "ಕನ್ನಡ"},
            {"name": "Telugu", "code": "te", "native_name": "తెలుగు"},
            {"name": "Marathi", "code": "mr", "native_name": "मराठी"},
            {"name": "Hindi", "code": "hi", "native_name": "हिन्दी"}
        ]
        lang_map = {}
        for l in languages_data:
            lang = Language(id=uuid.uuid4(), name=l["name"], code=l["code"], native_name=l["native_name"])
            db.add(lang)
            lang_map[l["code"]] = lang
        db.commit()

        print("Seeding Vocabulary for Indian languages & English...")
        vocab_pool = {
            "kn": [
                {"word": "ನಮಸ್ಕಾರ", "translation": "hello", "explanation": "ಸಾಮಾನ್ಯ ಶುಭಾಶಯ (Common respectful greeting)."},
                {"word": "ಧನ್ಯವಾದ", "translation": "thank you", "explanation": "ಕೃತಜ್ಞತೆ ವ್ಯಕ್ತಪಡಿಸಲು (Express gratitude)."},
                {"word": "ಸ್ನೇಹಿತ", "translation": "friend", "explanation": "ಆಪ್ತ ಗೆಳೆಯ (Close companion)."},
                {"word": "ಹಾಲು", "translation": "milk", "explanation": "ಪೌಷ್ಟಿಕ ಬಿಳಿ ಪಾನೀಯ (Nutritious white beverage)."},
                {"word": "ನೀರು", "translation": "water", "explanation": "ಜೀವಜಲ (Essential drinking water)."},
                {"word": "ಊಟ", "translation": "food", "explanation": "ದೈನಂದಿನ ಆಹಾರ (Daily meal / nourishment)."},
                {"word": "ನಾಯಿ", "translation": "dog", "explanation": "ವಿಶ್ವಾಸಾರ್ಹ ಪ್ರಾಣಿ (Domestic canine)."},
                {"word": "ಬೆಕ್ಕು", "translation": "cat", "explanation": "ಮುದ್ದಾದ ಸಾಕು ಪ್ರಾಣಿ (Cute feline pet)."},
                {"word": "ಮನೆ", "translation": "house", "explanation": "ವಾಸಿಸುವ ಸ್ಥಳ (Living place / home)."},
                {"word": "ಶಾಲೆ", "translation": "school", "explanation": "ವಿದ್ಯಾಲಯ (Educational institution)."},
                {"word": "ಪುಸ್ತಕ", "translation": "book", "explanation": "ಜ್ಞಾನದ ಗ್ರಂಥ (Reading material / book)."},
                {"word": "ಸೂರ್ಯ", "translation": "sun", "explanation": "ಪ್ರಕಾಶಮಾನ ನಕ್ಷತ್ರ (The shining solar star)."},
                {"word": "ಚಂದ್ರ", "translation": "moon", "explanation": "ರಾತ್ರಿಯ ನೈಸರ್ಗಿಕ ಉಪಗ್ರಹ (Earth's lunar satellite)."},
                {"word": "ಒಂದು", "translation": "one", "explanation": "ಮೊದಲನೆಯ ಸಂಖ್ಯೆ (First cardinal number)."},
                {"word": "ಎರಡು", "translation": "two", "explanation": "ಎರಡನೆಯ ಸಂಖ್ಯೆ (Second cardinal number)."},
                {"word": "ಹೂವು", "translation": "flower", "explanation": "ಸುವಾಸನೆಯ ಪುಷ್ಪ (Aromatic blossom)."},
                {"word": "ಮರ", "translation": "tree", "explanation": "ನೆರಳು ನೀಡುವ ಸಸ್ಯ (Tall perennial woody plant)."},
                {"word": "ಕುಡಿ", "translation": "drink", "explanation": "ದ್ರವ ಸೇವಿಸುವ ಕ್ರಿಯಾಪದ (Action verb for drinking)."},
                {"word": "ತಿನ್ನು", "translation": "eat", "explanation": "ಆಹಾರ ಸೇವಿಸುವ ಕ್ರಿಯಾಪದ (Action verb for eating)."},
                {"word": "ಶುಭೋದಯ", "translation": "good morning", "explanation": "ಬೆಳಗಿನ ಶುಭ ಹಾರೈಕೆ (Morning salutation)."}
            ],
            "te": [
                {"word": "నమస్కారం", "translation": "hello", "explanation": "గౌరవప్రదమైన శుభాకాంక్షలు (Respectful greeting)."},
                {"word": "ధన్యవాదాలు", "translation": "thank you", "explanation": "కృతజ్ఞతలు తెలపడానికి (Express gratitude)."},
                {"word": "స్నేహితుడు", "translation": "friend", "explanation": "ఆప్త మిత్రుడు (Companion)."},
                {"word": "పాలు", "translation": "milk", "explanation": "తెల్లటి పోషక ద్రవం (White nutritious milk)."},
                {"word": "నీరు", "translation": "water", "explanation": "తాగునీరు (Essential drinking water)."},
                {"word": "భోజనం", "translation": "food", "explanation": "ఆహారం (Meal / nutrition)."},
                {"word": "కుక్క", "translation": "dog", "explanation": "విశ్వాసంగల పెంపుడు జంతువు (Pet canine)."},
                {"word": "పిల్లి", "translation": "cat", "explanation": "పెంపుడు జంతువు (Domestic cat)."},
                {"word": "ఇల్లు", "translation": "house", "explanation": "నివాసం (Residence / home)."},
                {"word": "పాఠశాల", "translation": "school", "explanation": "విద్యాలయం (Educational school)."},
                {"word": "పుస్తకం", "translation": "book", "explanation": "గ్రంథం (Book)."},
                {"word": "సూర్యుడు", "translation": "sun", "explanation": "వెలుగునిచ్చే గ్రహం (The Sun)."},
                {"word": "చంద్రుడు", "translation": "moon", "explanation": "రాత్రి వెలుగునిచ్చే చంద్రుడు (The Moon)."},
                {"word": "ఒకటి", "translation": "one", "explanation": "మొదటి సంఖ్య (Number one)."},
                {"word": "రెండు", "translation": "two", "explanation": "రెండవ సంఖ్య (Number two)."},
                {"word": "పువ్వు", "translation": "flower", "explanation": "సువాసనగల పుష్పం (Blossom)."},
                {"word": "చెట్టు", "translation": "tree", "explanation": "వృక్షం (Woody tree)."},
                {"word": "తాగు", "translation": "drink", "explanation": "ద్రవపదార్థం తీసుకునే క్రియ (Action of drinking)."},
                {"word": "తిను", "translation": "eat", "explanation": "ఆహారం తీసుకునే క్రియ (Action of eating)."},
                {"word": "శుభోదయం", "translation": "good morning", "explanation": "ఉదయపు శుభాకాంక్షలు (Morning greeting)."}
            ],
            "mr": [
                {"word": "नमस्कार", "translation": "hello", "explanation": "आदरपूर्वक अभिवादन (Respectful greeting)."},
                {"word": "धन्यवाद", "translation": "thank you", "explanation": "आभार मानण्यासाठी (Express gratitude)."},
                {"word": "मित्र", "translation": "friend", "explanation": "सोबती / स्नेही (Companion)."},
                {"word": "दूध", "translation": "milk", "explanation": "पौष्टिक पांढरे पेय (Nutritious milk)."},
                {"word": "पाणी", "translation": "water", "explanation": "पिण्याचे जीवनजल (Drinking water)."},
                {"word": "जेवण", "translation": "food", "explanation": "दैनंदिन आहार (Daily meal / food)."},
                {"word": "कुत्रा", "translation": "dog", "explanation": "इमानदार पाळीव प्राणी (Canine pet)."},
                {"word": "मांजर", "translation": "cat", "explanation": "पाळीव मांजर (Feline pet)."},
                {"word": "घर", "translation": "house", "explanation": "राहण्याची जागा (Home)."},
                {"word": "शाळा", "translation": "school", "explanation": "विद्या मंदिर (School)."},
                {"word": "पुस्तक", "translation": "book", "explanation": "वाचनाचे साधन (Book)."},
                {"word": "सूर्य", "translation": "sun", "explanation": "प्रकाश देणारा तारा (The Sun)."},
                {"word": "चंद्र", "translation": "moon", "explanation": "रात्रीचा चंद्र (The Moon)."},
                {"word": "एक", "translation": "one", "explanation": "पहिली संख्या (Number one)."},
                {"word": "दोन", "translation": "two", "explanation": "दुसरी संख्या (Number two)."},
                {"word": "फूल", "translation": "flower", "explanation": "सुवासिक पुष्प (Blossom)."},
                {"word": "झाड", "translation": "tree", "explanation": "वृक्ष (Perennial tree)."},
                {"word": "पिणे", "translation": "drink", "explanation": "द्रव पिण्याची क्रिया (Drinking action)."},
                {"word": "खाणे", "translation": "eat", "explanation": "अन्न खाण्याची क्रिया (Eating action)."},
                {"word": "शुभ सकाळ", "translation": "good morning", "explanation": "सकाळचे अभिवादन (Morning greeting)."}
            ],
            "hi": [
                {"word": "नमस्ते", "translation": "hello", "explanation": "पारंपरिक अभिवादन (Traditional greeting)."},
                {"word": "धन्यवाद", "translation": "thank you", "explanation": "आभार व्यक्त करना (Express gratitude)."},
                {"word": "दोस्त", "translation": "friend", "explanation": "मित्र / साथी (Companion)."},
                {"word": "दूध", "translation": "milk", "explanation": "सफेद पौष्टिक पेय (Nutritious milk)."},
                {"word": "पानी", "translation": "water", "explanation": "पीने का जल (Drinking water)."},
                {"word": "खाना", "translation": "food", "explanation": "दैनिक भोजन (Food/Meal)."},
                {"word": "कुत्ता", "translation": "dog", "explanation": "वफादार पालतू जानवर (Canine pet)."},
                {"word": "बिल्ली", "translation": "cat", "explanation": "पालतू बिल्ली (Feline pet)."},
                {"word": "घर", "translation": "house", "explanation": "रहने का स्थान (Home)."},
                {"word": "विद्यालय", "translation": "school", "explanation": "शिक्षा का केंद्र (School)."},
                {"word": "किताब", "translation": "book", "explanation": "पठन सामग्री (Book)."},
                {"word": "सूरज", "translation": "sun", "explanation": "प्रकाश देने वाला सूर्य (The Sun)."},
                {"word": "चाँद", "translation": "moon", "explanation": "रात का चंद्रमा (The Moon)."},
                {"word": "एक", "translation": "one", "explanation": "पहली संख्या (Number one)."},
                {"word": "दो", "translation": "two", "explanation": "दूसरी संख्या (Number two)."},
                {"word": "फूल", "translation": "flower", "explanation": "सुगंधित पुष्प (Blossom)."},
                {"word": "पेड़", "translation": "tree", "explanation": "छायादार वृक्ष (Tree)."},
                {"word": "पीना", "translation": "drink", "explanation": "द्रव पदार्थ पीने की क्रिया (Verb drink)."},
                {"word": "खाना", "translation": "eat", "explanation": "भोजन करने की क्रिया (Verb eat)."},
                {"word": "सुप्रभात", "translation": "good morning", "explanation": "प्रातःकालीन अभिवादन (Morning greeting)."}
            ],
            "en": [
                {"word": "hello", "translation": "ನಮಸ್ಕಾರ / hello", "explanation": "Common friendly greeting."},
                {"word": "thank you", "translation": "ಧನ್ಯವಾದ / thank you", "explanation": "Used to express gratitude."},
                {"word": "friend", "translation": "ಸ್ನೇಹಿತ / friend", "explanation": "A companion with a mutual bond."},
                {"word": "milk", "translation": "ಹಾಲು / milk", "explanation": "Nutritious white fluid."},
                {"word": "water", "translation": "ನೀರು / water", "explanation": "Clear liquid essential for life."},
                {"word": "food", "translation": "ಊಟ / food", "explanation": "Nutritious meal."},
                {"word": "dog", "translation": "ನಾಯಿ / dog", "explanation": "Domestic canine animal."},
                {"word": "cat", "translation": "ಬೆಕ್ಕು / cat", "explanation": "Domestic feline pet."},
                {"word": "house", "translation": "ಮನೆ / house", "explanation": "A building for human habitation."},
                {"word": "school", "translation": "ಶಾಲೆ / school", "explanation": "Institution for educating children."},
                {"word": "book", "translation": "ಪುಸ್ತಕ / book", "explanation": "Written or printed work consisting of pages."},
                {"word": "sun", "translation": "ಸೂರ್ಯ / sun", "explanation": "The star at the center of the solar system."},
                {"word": "moon", "translation": "ಚಂದ್ರ / moon", "explanation": "Natural satellite of the earth."},
                {"word": "one", "translation": "ಒಂದು / one", "explanation": "The lowest cardinal number."},
                {"word": "two", "translation": "ಎರಡು / two", "explanation": "Number equivalent to the sum of 1 and 1."},
                {"word": "flower", "translation": "ಹೂವು / flower", "explanation": "Seed-bearing part of a plant."},
                {"word": "tree", "translation": "ಮರ / tree", "explanation": "Woody perennial plant with trunk and branches."},
                {"word": "drink", "translation": "ಕುಡಿ / drink", "explanation": "Take liquid into the mouth and swallow."},
                {"word": "eat", "translation": "ತಿನ್ನು / eat", "explanation": "Put food into the mouth and chew and swallow it."},
                {"word": "good morning", "translation": "ಶುಭೋದಯ / good morning", "explanation": "Greeting said when meeting someone early in the day."}
            ]
        }
        for lang_code, words in vocab_pool.items():
            if lang_code in lang_map:
                lang_id = lang_map[lang_code].id
                for w in words:
                    vocab = Vocabulary(
                        id=uuid.uuid4(),
                        language_id=lang_id,
                        word=w["word"],
                        translation=w["translation"],
                        explanation=w["explanation"]
                    )
                    db.add(vocab)
        db.commit()

        # ----------------------------------------------------
        # 1. SEED KANNADA COURSE
        # ----------------------------------------------------
        print("Seeding Kannada Course...")
        kn_course = Course(
            id=uuid.uuid4(),
            title="Kannada Literacy Foundations",
            description="ಕನ್ನಡ ಅಕ್ಷರಮಾಲೆ, ಸ್ವರಗಳು ಮತ್ತು ನಿರರ್ಗಳ ಓದುವಿಕೆ ಕಲಿಯಿರಿ (Master Kannada alphabet, vowels, and conversational literacy).",
            language_id=lang_map["kn"].id,
            level=CourseLevel.Beginner,
            cefr_level="A1",
            min_score=0.0,
            max_score=29.9,
            skills_json=json.dumps(["vocabulary", "phonics", "reading"]),
            goals_json=json.dumps(["conversation", "travel", "daily-life"]),
            difficulty="beginner",
            thumbnail_url="https://images.unsplash.com/photo-1600585154340-be6161a56a0c",
            is_published=True
        )
        db.add(kn_course)
        db.commit()

        kn_topic = Topic(id=uuid.uuid4(), course_id=kn_course.id, title="ಸ್ವರಗಳು ಮತ್ತು ಅಕ್ಷರಮಾಲೆ (Kannada Vowels & Alphabet)", description="ಕನ್ನಡ ಸ್ವರಗಳ ಪರಿಚಯ ಮತ್ತು ಸರಿಯಾದ ಉಚ್ಚಾರಣೆ (Introduction to Kannada vowel sounds and phonic pronunciations).", order=1)
        db.add(kn_topic)
        db.commit()

        kn_lesson = Lesson(
            id=uuid.uuid4(),
            topic_id=kn_topic.id,
            title="ಕನ್ನಡ ಸ್ವರಗಳ ಉಚ್ಚಾರಣೆ (Pronouncing Kannada Vowels)",
            content="# ಕನ್ನಡ ಸ್ವರಗಳು (Kannada Vowels)\nಕನ್ನಡದಲ್ಲಿ ಪ್ರಮುಖ ಸ್ವರಗಳು:\n- ಅ (A) - ಅಮ್ಮ (Amma - Mother)\n- ಆ (Aa) - ಆನೆ (Aane - Elephant)\n- ಇ (I) - ಇಲಿ (Ili - Rat)\n- ಈ (Ee) - ಈಜು (Eeju - Swim)\n- ಉ (U) - ಉಡುಗೊರೆ (Udugore - Gift)\n- ಎ (E) - ಎಲೆ (Ele - Leaf)\n- ಒ (O) - ಒಂಟೆ (Onte - Camel)\n\nಧ್ವನಿ ಅಭ್ಯಾಸ ಗುಂಡಿಗಳನ್ನು ಒತ್ತಿ ಉಚ್ಚಾರಣೆಯನ್ನು ಆಲಿಸಿ!",
            duration_minutes=15,
            order=1
        )
        db.add(kn_lesson)
        db.commit()

        kn_assessment = Assessment(id=uuid.uuid4(), lesson_id=kn_lesson.id, title="ಕನ್ನಡ ಸ್ವರಗಳ ರಸಪ್ರಶ್ನೆ (Kannada Vowels Phonics Quiz)", type=AssessmentType.quiz, pass_percentage=70.0)
        db.add(kn_assessment)
        db.commit()

        kn_q1 = Question(id=uuid.uuid4(), assessment_id=kn_assessment.id, text="ಕನ್ನಡ ಅಕ್ಷರಮಾಲೆಯ ಮೊದಲ ಸ್ವರ ಯಾವುದು? (Which is the first vowel in Kannada?)", type=QuestionType.multiple_choice, points=1)
        db.add(kn_q1)
        db.commit()
        db.add_all([
            Answer(id=uuid.uuid4(), question_id=kn_q1.id, text="ಅ (a)", is_correct=True, explanation="ಸರಿ! 'ಅ' ಕನ್ನಡ ಅಕ್ಷರಮಾಲೆಯ ಮೊದಲನೆಯ ಸ್ವರವಾಗಿದೆ."),
            Answer(id=uuid.uuid4(), question_id=kn_q1.id, text="ಕ (ka)", is_correct=False, explanation="'ಕ' ವ್ಯಂಜನವಾಗಿದೆ, ಸ್ವರವಲ್ಲ."),
            Answer(id=uuid.uuid4(), question_id=kn_q1.id, text="ರ (ra)", is_correct=False)
        ])
        db.commit()

        kn_q2 = Question(id=uuid.uuid4(), assessment_id=kn_assessment.id, text="ವಾಕ್ಯವನ್ನು ಸರಿಯಾಗಿ ಜೋಡಿಸಿ: 'ನಾನು ಹಾಲು ಕುಡಿಯುತ್ತೇನೆ' (I drink milk)", type=QuestionType.word_order, points=1)
        db.add(kn_q2)
        db.commit()
        db.add_all([
            Answer(id=uuid.uuid4(), question_id=kn_q2.id, text="ನಾನು ಹಾಲು ಕುಡಿಯುತ್ತೇನೆ", is_correct=True, explanation="ಉತ್ತಮ! ವಾಕ್ಯ ರಚನೆ ಸರಿಯಾಗಿದೆ."),
            Answer(id=uuid.uuid4(), question_id=kn_q2.id, text="ನಾಯಿ", is_correct=False),
            Answer(id=uuid.uuid4(), question_id=kn_q2.id, text="ಮನೆ", is_correct=False)
        ])
        db.commit()

        kn_q3 = Question(id=uuid.uuid4(), assessment_id=kn_assessment.id, text="ಕನ್ನಡ ಪದಗಳನ್ನು ಇಂಗ್ಲಿಷ್ ಅರ್ಥಗಳೊಂದಿಗೆ ಹೊಂದಿಸಿ (Match Kannada words with English)", type=QuestionType.match_pairs, points=1)
        db.add(kn_q3)
        db.commit()
        db.add_all([
            Answer(id=uuid.uuid4(), question_id=kn_q3.id, text="ನಮಸ್ಕಾರ:hello,ಹಾಲು:milk,ಸ್ನೇಹಿತ:friend,ನಾಯಿ:dog,ಧನ್ಯವಾದ:thank you", is_correct=True, explanation="ಎಲ್ಲಾ ಪದಗಳನ್ನು ಸರಿಯಾಗಿ ಹೊಂದಿಸಿದ್ದೀರಿ!"),
            Answer(id=uuid.uuid4(), question_id=kn_q3.id, text="ನಮಸ್ಕಾರ:dog,ಹಾಲು:friend,ಸ್ನೇಹಿತ:milk,ನಾಯಿ:hello,ಧನ್ಯವಾದ:thank you", is_correct=False)
        ])
        db.commit()

        kn_q4 = Question(id=uuid.uuid4(), assessment_id=kn_assessment.id, text="ನಮಸ್ಕಾರ", type=QuestionType.listening, points=1)
        db.add(kn_q4)
        db.commit()
        db.add_all([
            Answer(id=uuid.uuid4(), question_id=kn_q4.id, text="hello", is_correct=True, explanation="'ನಮಸ್ಕಾರ' ಎಂದರೆ 'hello'."),
            Answer(id=uuid.uuid4(), question_id=kn_q4.id, text="goodbye", is_correct=False)
        ])
        db.commit()

        kn_q5 = Question(id=uuid.uuid4(), assessment_id=kn_assessment.id, text="ನಾನು ಹಾಲು ಕುಡಿಯುತ್ತೇನೆ", type=QuestionType.speaking, points=1)
        db.add(kn_q5)
        db.commit()
        db.add(Answer(id=uuid.uuid4(), question_id=kn_q5.id, text="ನಾನು ಹಾಲು ಕುಡಿಯುತ್ತೇನೆ", is_correct=True, explanation="ಅದ್ಭುತ ಉಚ್ಚಾರಣೆ!"))
        db.commit()

        kn_q6 = Question(id=uuid.uuid4(), assessment_id=kn_assessment.id, text="ನಾನು ____ ಕುಡಿಯುತ್ತೇನೆ.", type=QuestionType.fill_in_blank, points=1)
        db.add(kn_q6)
        db.commit()
        db.add_all([
            Answer(id=uuid.uuid4(), question_id=kn_q6.id, text="ಹಾಲು", is_correct=True, explanation="ಸರಿಯಾಗಿದೆ. 'ಹಾಲು' ಕುಡಿಯುವ ದ್ರವ."),
            Answer(id=uuid.uuid4(), question_id=kn_q6.id, text="ಪುಸ್ತಕ", is_correct=False)
        ])
        db.commit()

        # ----------------------------------------------------
        # 2. SEED TELUGU COURSE
        # ----------------------------------------------------
        print("Seeding Telugu Course...")
        te_course = Course(
            id=uuid.uuid4(),
            title="Telugu Literacy Foundations",
            description="తెలుగు వర్ణమాల, అచ్చులు మరియు ప్రాథమిక చదవడం నేర్చుకోండి (Master Telugu alphabet, vowels, and conversational literacy).",
            language_id=lang_map["te"].id,
            level=CourseLevel.Beginner,
            cefr_level="A1",
            min_score=0.0,
            max_score=29.9,
            skills_json=json.dumps(["vocabulary", "phonics", "reading"]),
            goals_json=json.dumps(["conversation", "travel", "daily-life"]),
            difficulty="beginner",
            thumbnail_url="https://images.unsplash.com/photo-1590073242678-70ee3fc28e8e",
            is_published=True
        )
        db.add(te_course)
        db.commit()

        te_topic = Topic(id=uuid.uuid4(), course_id=te_course.id, title="అచ్చులు మరియు అక్షరమాల (Telugu Vowels & Alphabet)", description="తెలుగు అచ్చుల పరిచయం మరియు ఉచ్చారణ (Introduction to Telugu vowel sounds and pronunciation).", order=1)
        db.add(te_topic)
        db.commit()

        te_lesson = Lesson(
            id=uuid.uuid4(),
            topic_id=te_topic.id,
            title="తెలుగు అచ్చుల ఉచ్చారణ (Pronouncing Telugu Vowels)",
            content="# తెలుగు అచ్చులు (Telugu Vowels)\nతెలుగు భాషలో ముఖ్యమైన అచ్చులు:\n- అ (A) - అమ్మ (Amma - Mother)\n- ఆ (Aa) - ఆవు (Aavu - Cow)\n- ఇ (I) - ఇల్లు (Illu - House)\n- ఈ (Ee) - ఈగ (Eega - Fly)\n- ఉ (U) - ఉడుత (Uduta - Squirrel)\n- ఎ (E) - ఎలుక (Eluka - Rat)\n- ఒ (O) - ఒంటె (Onte - Camel)\n\nధ్వని ప్రాక్టీస్ బటన్లను క్లిక్ చేసి ఉచ్చారణను వినండి!",
            duration_minutes=15,
            order=1
        )
        db.add(te_lesson)
        db.commit()

        te_assessment = Assessment(id=uuid.uuid4(), lesson_id=te_lesson.id, title="తెలుగు అచ్చుల క్విజ్ (Telugu Vowels Phonics Quiz)", type=AssessmentType.quiz, pass_percentage=70.0)
        db.add(te_assessment)
        db.commit()

        te_q1 = Question(id=uuid.uuid4(), assessment_id=te_assessment.id, text="తెలుగు అక్షరమాలలో మొదటి అచ్చు ఏది? (Which is the first vowel in Telugu?)", type=QuestionType.multiple_choice, points=1)
        db.add(te_q1)
        db.commit()
        db.add_all([
            Answer(id=uuid.uuid4(), question_id=te_q1.id, text="అ (a)", is_correct=True, explanation="సరైన సమాధానం! 'అ' మొదటి అచ్చు."),
            Answer(id=uuid.uuid4(), question_id=te_q1.id, text="క (ka)", is_correct=False),
            Answer(id=uuid.uuid4(), question_id=te_q1.id, text="ర (ra)", is_correct=False)
        ])
        db.commit()

        te_q2 = Question(id=uuid.uuid4(), assessment_id=te_assessment.id, text="వాక్యాన్ని క్రమపద్ధతిలో అమర్చండి: 'నేను పాలు తాగుతాను' (I drink milk)", type=QuestionType.word_order, points=1)
        db.add(te_q2)
        db.commit()
        db.add_all([
            Answer(id=uuid.uuid4(), question_id=te_q2.id, text="నేను పాలు తాగుతాను", is_correct=True, explanation="చాలా బాగుంది! వాక్యం సరైనది."),
            Answer(id=uuid.uuid4(), question_id=te_q2.id, text="కుక్క", is_correct=False),
            Answer(id=uuid.uuid4(), question_id=te_q2.id, text="ఇల్లు", is_correct=False)
        ])
        db.commit()

        te_q3 = Question(id=uuid.uuid4(), assessment_id=te_assessment.id, text="తెలుగు పదాలను ఆంగ్ల అర్థాలతో సరిపోల్చండి (Match Telugu words with English)", type=QuestionType.match_pairs, points=1)
        db.add(te_q3)
        db.commit()
        db.add_all([
            Answer(id=uuid.uuid4(), question_id=te_q3.id, text="నమస్కారం:hello,పాలు:milk,స్నేహితుడు:friend,కుక్క:dog,ధన్యవాదాలు:thank you", is_correct=True, explanation="అన్నింటినీ సరిగ్గా సరిపోల్చారు!"),
            Answer(id=uuid.uuid4(), question_id=te_q3.id, text="నమస్కారం:dog,పాలు:friend,స్నేహితుడు:milk,కుక్క:hello,ధన్యవాదాలు:thank you", is_correct=False)
        ])
        db.commit()

        te_q4 = Question(id=uuid.uuid4(), assessment_id=te_assessment.id, text="నమస్కారం", type=QuestionType.listening, points=1)
        db.add(te_q4)
        db.commit()
        db.add_all([
            Answer(id=uuid.uuid4(), question_id=te_q4.id, text="hello", is_correct=True, explanation="'నమస్కారం' అంటే 'hello'."),
            Answer(id=uuid.uuid4(), question_id=te_q4.id, text="goodbye", is_correct=False)
        ])
        db.commit()

        te_q5 = Question(id=uuid.uuid4(), assessment_id=te_assessment.id, text="నేను పాలు తాగుతాను", type=QuestionType.speaking, points=1)
        db.add(te_q5)
        db.commit()
        db.add(Answer(id=uuid.uuid4(), question_id=te_q5.id, text="నేను పాలు తాగుతాను", is_correct=True, explanation="అద్భుతమైన ఉచ్చారణ!"))
        db.commit()

        te_q6 = Question(id=uuid.uuid4(), assessment_id=te_assessment.id, text="నేను ____ తాగుతాను.", type=QuestionType.fill_in_blank, points=1)
        db.add(te_q6)
        db.commit()
        db.add_all([
            Answer(id=uuid.uuid4(), question_id=te_q6.id, text="పాలు", is_correct=True, explanation="సరైన సమాధానం!"),
            Answer(id=uuid.uuid4(), question_id=te_q6.id, text="పుస్తకం", is_correct=False)
        ])
        db.commit()

        # ----------------------------------------------------
        # 3. SEED MARATHI COURSE
        # ----------------------------------------------------
        print("Seeding Marathi Course...")
        mr_course = Course(
            id=uuid.uuid4(),
            title="Marathi Literacy Foundations",
            description="मराठी मूळाक्षरे, स्वर आणि अस्खलित वाचन शिका (Master Marathi alphabet, vowels, and conversational literacy).",
            language_id=lang_map["mr"].id,
            level=CourseLevel.Beginner,
            cefr_level="A1",
            min_score=0.0,
            max_score=29.9,
            skills_json=json.dumps(["vocabulary", "phonics", "reading"]),
            goals_json=json.dumps(["conversation", "travel", "daily-life"]),
            difficulty="beginner",
            thumbnail_url="https://images.unsplash.com/photo-1543783207-ec64e4d95325",
            is_published=True
        )
        db.add(mr_course)
        db.commit()

        mr_topic = Topic(id=uuid.uuid4(), course_id=mr_course.id, title="स्वर आणि मूळाक्षरे (Marathi Vowels & Alphabet)", description="मराठी स्वरांची ओळख आणि उच्चार (Introduction to Marathi vowel sounds and pronunciation).", order=1)
        db.add(mr_topic)
        db.commit()

        mr_lesson = Lesson(
            id=uuid.uuid4(),
            topic_id=mr_topic.id,
            title="मराठी स्वरांचे उच्चार (Pronouncing Marathi Vowels)",
            content="# मराठी स्वर (Marathi Vowels)\nमराठी वर्णमालेतील मुख्य स्वर:\n- अ (A) - अननस (Ananas - Pineapple)\n- आ (Aa) - आई (Aai - Mother)\n- इ (I) - इमारत (Imaarat - Building)\n- ई (Ee) - ईडलिंबू (Eedlimbu - Lemon)\n- उ (U) - उखळ (Ukhal - Mortar)\n- ए (E) - एक (Ek - One)\n- ओ (O) - ओठ (Oth - Lips)\n\nऑडिओ सराव बटणे दाबून उच्चार ऐका!",
            duration_minutes=15,
            order=1
        )
        db.add(mr_lesson)
        db.commit()

        mr_assessment = Assessment(id=uuid.uuid4(), lesson_id=mr_lesson.id, title="मराठी स्वर प्रश्नमंजुषा (Marathi Vowels Phonics Quiz)", type=AssessmentType.quiz, pass_percentage=70.0)
        db.add(mr_assessment)
        db.commit()

        mr_q1 = Question(id=uuid.uuid4(), assessment_id=mr_assessment.id, text="मराठी वर्णमालेतील पहिला स्वर कोणता आहे? (Which is the first vowel in Marathi?)", type=QuestionType.multiple_choice, points=1)
        db.add(mr_q1)
        db.commit()
        db.add_all([
            Answer(id=uuid.uuid4(), question_id=mr_q1.id, text="अ (a)", is_correct=True, explanation="बरोबर! 'अ' हा पहिला स्वर आहे."),
            Answer(id=uuid.uuid4(), question_id=mr_q1.id, text="क (ka)", is_correct=False),
            Answer(id=uuid.uuid4(), question_id=mr_q1.id, text="र (ra)", is_correct=False)
        ])
        db.commit()

        mr_q2 = Question(id=uuid.uuid4(), assessment_id=mr_assessment.id, text="वाक्य योग्य क्रमाने लावा: 'मी दूध पितो' (I drink milk)", type=QuestionType.word_order, points=1)
        db.add(mr_q2)
        db.commit()
        db.add_all([
            Answer(id=uuid.uuid4(), question_id=mr_q2.id, text="मी दूध पितो", is_correct=True, explanation="छान! वाक्य रचना योग्य आहे."),
            Answer(id=uuid.uuid4(), question_id=mr_q2.id, text="कुत्रा", is_correct=False),
            Answer(id=uuid.uuid4(), question_id=mr_q2.id, text="घर", is_correct=False)
        ])
        db.commit()

        mr_q3 = Question(id=uuid.uuid4(), assessment_id=mr_assessment.id, text="मराठी शब्द इंग्रजी अर्थांसोबत जुळवा (Match Marathi words with English)", type=QuestionType.match_pairs, points=1)
        db.add(mr_q3)
        db.commit()
        db.add_all([
            Answer(id=uuid.uuid4(), question_id=mr_q3.id, text="नमस्कार:hello,दूध:milk,मित्र:friend,कुत्रा:dog,धन्यवाद:thank you", is_correct=True, explanation="सर्व जोड्या अचूक जुळवल्या!"),
            Answer(id=uuid.uuid4(), question_id=mr_q3.id, text="नमस्कार:dog,दूध:friend,मित्र:milk,कुत्रा:hello,धन्यवाद:thank you", is_correct=False)
        ])
        db.commit()

        mr_q4 = Question(id=uuid.uuid4(), assessment_id=mr_assessment.id, text="नमस्कार", type=QuestionType.listening, points=1)
        db.add(mr_q4)
        db.commit()
        db.add_all([
            Answer(id=uuid.uuid4(), question_id=mr_q4.id, text="hello", is_correct=True, explanation="'नमस्कार' म्हणजे 'hello'."),
            Answer(id=uuid.uuid4(), question_id=mr_q4.id, text="goodbye", is_correct=False)
        ])
        db.commit()

        mr_q5 = Question(id=uuid.uuid4(), assessment_id=mr_assessment.id, text="मी दूध पितो", type=QuestionType.speaking, points=1)
        db.add(mr_q5)
        db.commit()
        db.add(Answer(id=uuid.uuid4(), question_id=mr_q5.id, text="मी दूध पितो", is_correct=True, explanation="उत्तम उच्चार!"))
        db.commit()

        mr_q6 = Question(id=uuid.uuid4(), assessment_id=mr_assessment.id, text="मी ____ पितो.", type=QuestionType.fill_in_blank, points=1)
        db.add(mr_q6)
        db.commit()
        db.add_all([
            Answer(id=uuid.uuid4(), question_id=mr_q6.id, text="दूध", is_correct=True, explanation="बरोबर उत्तर!"),
            Answer(id=uuid.uuid4(), question_id=mr_q6.id, text="पुस्तक", is_correct=False)
        ])
        db.commit()

        # ----------------------------------------------------
        # 4. SEED HINDI COURSE
        # ----------------------------------------------------
        print("Seeding Hindi Course...")
        hi_course = Course(
            id=uuid.uuid4(),
            title="Hindi Literacy Foundations",
            description="हिन्दी वर्णमाला, स्वर और धाराप्रवाह पठन सीखें (Master Hindi alphabet, vowels, and conversational literacy).",
            language_id=lang_map["hi"].id,
            level=CourseLevel.Beginner,
            cefr_level="A1",
            min_score=0.0,
            max_score=29.9,
            skills_json=json.dumps(["vocabulary", "phonics", "reading"]),
            goals_json=json.dumps(["conversation", "travel", "daily-life"]),
            difficulty="beginner",
            thumbnail_url="https://images.unsplash.com/photo-1524492412937-b28074a5d7da",
            is_published=True
        )
        db.add(hi_course)
        db.commit()

        hi_topic = Topic(id=uuid.uuid4(), course_id=hi_course.id, title="स्वर और वर्णमाला (Hindi Vowels & Alphabet)", description="हिन्दी स्वरों का परिचय और सही उच्चारण (Introduction to Hindi vowel sounds and pronunciation).", order=1)
        db.add(hi_topic)
        db.commit()

        hi_lesson = Lesson(
            id=uuid.uuid4(),
            topic_id=hi_topic.id,
            title="हिन्दी स्वरों का उच्चारण (Pronouncing Hindi Vowels)",
            content="# हिन्दी स्वर (Hindi Vowels)\nहिन्दी वर्णमाला के मुख्य स्वर:\n- अ (A) - अनार (Anaar - Pomegranate)\n- आ (Aa) - आम (Aam - Mango)\n- इ (I) - इमली (Imli - Tamarind)\n- ई (Ee) - ईख (Eekh - Sugarcane)\n- उ (U) - उल्लू (Ullu - Owl)\n- ए (E) - एक (Ek - One)\n- ओ (O) - ओखली (Okhli - Mortar)\n\nऑडियो अभ्यास बटन दबाकर उच्चारण सुनें!",
            duration_minutes=15,
            order=1
        )
        db.add(hi_lesson)
        db.commit()

        hi_assessment = Assessment(id=uuid.uuid4(), lesson_id=hi_lesson.id, title="हिन्दी स्वर प्रश्नोत्तरी (Hindi Vowels Phonics Quiz)", type=AssessmentType.quiz, pass_percentage=70.0)
        db.add(hi_assessment)
        db.commit()

        hi_q1 = Question(id=uuid.uuid4(), assessment_id=hi_assessment.id, text="हिन्दी वर्णमाला का पहला स्वर कौन सा है? (Which is the first vowel in Hindi?)", type=QuestionType.multiple_choice, points=1)
        db.add(hi_q1)
        db.commit()
        db.add_all([
            Answer(id=uuid.uuid4(), question_id=hi_q1.id, text="अ (a)", is_correct=True, explanation="सही! 'अ' पहला स्वर है।"),
            Answer(id=uuid.uuid4(), question_id=hi_q1.id, text="क (ka)", is_correct=False),
            Answer(id=uuid.uuid4(), question_id=hi_q1.id, text="र (ra)", is_correct=False)
        ])
        db.commit()

        hi_q2 = Question(id=uuid.uuid4(), assessment_id=hi_assessment.id, text="वाक्य को सही क्रम में लगाएं: 'मैं दूध पीता हूँ' (I drink milk)", type=QuestionType.word_order, points=1)
        db.add(hi_q2)
        db.commit()
        db.add_all([
            Answer(id=uuid.uuid4(), question_id=hi_q2.id, text="मैं दूध पीता हूँ", is_correct=True, explanation="बहुत बढ़िया! वाक्य सही है।"),
            Answer(id=uuid.uuid4(), question_id=hi_q2.id, text="कुत्ता", is_correct=False),
            Answer(id=uuid.uuid4(), question_id=hi_q2.id, text="घर", is_correct=False)
        ])
        db.commit()

        hi_q3 = Question(id=uuid.uuid4(), assessment_id=hi_assessment.id, text="हिन्दी शब्दों को अंग्रेजी अर्थों के साथ सुमेलित करें (Match Hindi words with English)", type=QuestionType.match_pairs, points=1)
        db.add(hi_q3)
        db.commit()
        db.add_all([
            Answer(id=uuid.uuid4(), question_id=hi_q3.id, text="नमस्ते:hello,दूध:milk,दोस्त:friend,कुत्ता:dog,धन्यवाद:thank you", is_correct=True, explanation="सभी जोड़े सही मिले!"),
            Answer(id=uuid.uuid4(), question_id=hi_q3.id, text="नमस्ते:dog,दूध:friend,दोस्त:milk,कुत्ता:hello,धन्यवाद:thank you", is_correct=False)
        ])
        db.commit()

        hi_q4 = Question(id=uuid.uuid4(), assessment_id=hi_assessment.id, text="नमस्ते", type=QuestionType.listening, points=1)
        db.add(hi_q4)
        db.commit()
        db.add_all([
            Answer(id=uuid.uuid4(), question_id=hi_q4.id, text="hello", is_correct=True, explanation="'नमस्ते' का अर्थ 'hello' है।"),
            Answer(id=uuid.uuid4(), question_id=hi_q4.id, text="goodbye", is_correct=False)
        ])
        db.commit()

        hi_q5 = Question(id=uuid.uuid4(), assessment_id=hi_assessment.id, text="मैं दूध पीता हूँ", type=QuestionType.speaking, points=1)
        db.add(hi_q5)
        db.commit()
        db.add(Answer(id=uuid.uuid4(), question_id=hi_q5.id, text="मैं दूध पीता हूँ", is_correct=True, explanation="उत्कृष्ट उच्चारण!"))
        db.commit()

        hi_q6 = Question(id=uuid.uuid4(), assessment_id=hi_assessment.id, text="मैं ____ पीता हूँ।", type=QuestionType.fill_in_blank, points=1)
        db.add(hi_q6)
        db.commit()
        db.add_all([
            Answer(id=uuid.uuid4(), question_id=hi_q6.id, text="दूध", is_correct=True, explanation="सही उत्तर!"),
            Answer(id=uuid.uuid4(), question_id=hi_q6.id, text="किताब", is_correct=False)
        ])
        db.commit()

        # ----------------------------------------------------
        # 5. SEED ENGLISH COURSE
        # ----------------------------------------------------
        print("Seeding English Course...")
        en_course = Course(
            id=uuid.uuid4(),
            title="English Literacy Foundations",
            description="Learn essential English vowel sounds, alphabet, phonics, and basic reading skills.",
            language_id=lang_map["en"].id,
            level=CourseLevel.Beginner,
            cefr_level="A1",
            min_score=0.0,
            max_score=29.9,
            skills_json=json.dumps(["vocabulary", "phonics", "reading"]),
            goals_json=json.dumps(["conversation", "travel", "daily-life"]),
            difficulty="beginner",
            thumbnail_url="https://images.unsplash.com/photo-1543783207-ec64e4d95325",
            is_published=True
        )
        db.add(en_course)
        db.commit()

        en_topic = Topic(id=uuid.uuid4(), course_id=en_course.id, title="English Vowels & Alphabet", description="Introduction to English vowel sounds and pronunciations.", order=1)
        db.add(en_topic)
        db.commit()

        en_lesson = Lesson(
            id=uuid.uuid4(),
            topic_id=en_topic.id,
            title="Pronouncing English Vowels (A, E, I, O, U)",
            content="# English Vowels\nEnglish vowels can have short and long sounds depending on spelling:\n- A as in *cat* (short) or *say* (long)\n- E as in *get* (short) or *see* (long)\n- I as in *sit* (short) or *mine* (long)\n- O as in *got* (short) or *go* (long)\n- U as in *cup* (short) or *rule* (long)",
            duration_minutes=15,
            order=1
        )
        db.add(en_lesson)
        db.commit()

        en_assessment = Assessment(id=uuid.uuid4(), lesson_id=en_lesson.id, title="English Vowels Phonics Quiz", type=AssessmentType.quiz, pass_percentage=70.0)
        db.add(en_assessment)
        db.commit()

        en_q1 = Question(id=uuid.uuid4(), assessment_id=en_assessment.id, text="Which vowel sound matches the 'ee' sound in 'bee'?", type=QuestionType.multiple_choice, points=1)
        db.add(en_q1)
        db.commit()
        db.add_all([
            Answer(id=uuid.uuid4(), question_id=en_q1.id, text="The letter E", is_correct=True, explanation="Correct! E sounds like 'bee' here."),
            Answer(id=uuid.uuid4(), question_id=en_q1.id, text="The letter A", is_correct=False),
            Answer(id=uuid.uuid4(), question_id=en_q1.id, text="The letter O", is_correct=False)
        ])
        db.commit()

        en_q2 = Question(id=uuid.uuid4(), assessment_id=en_assessment.id, text="Arrange the sentence: 'I drink milk'", type=QuestionType.word_order, points=1)
        db.add(en_q2)
        db.commit()
        db.add_all([
            Answer(id=uuid.uuid4(), question_id=en_q2.id, text="I drink milk", is_correct=True, explanation="Great job! Sentence structured correctly."),
            Answer(id=uuid.uuid4(), question_id=en_q2.id, text="dog", is_correct=False),
            Answer(id=uuid.uuid4(), question_id=en_q2.id, text="book", is_correct=False)
        ])
        db.commit()

        en_q3 = Question(id=uuid.uuid4(), assessment_id=en_assessment.id, text="Match English words with Kannada/Telugu meanings", type=QuestionType.match_pairs, points=1)
        db.add(en_q3)
        db.commit()
        db.add_all([
            Answer(id=uuid.uuid4(), question_id=en_q3.id, text="hello:ನಮಸ್ಕಾರ,milk:ಹಾಲು,friend:ಸ್ನೇಹಿತ,dog:ನಾಯಿ,thank you:ಧನ್ಯವಾದ", is_correct=True, explanation="Pairs matched successfully."),
            Answer(id=uuid.uuid4(), question_id=en_q3.id, text="hello:ನಾಯಿ,milk:ಸ್ನೇಹಿತ,friend:ಹಾಲು,dog:ನಮಸ್ಕಾರ,thank you:ಧನ್ಯವಾದ", is_correct=False)
        ])
        db.commit()

        en_q4 = Question(id=uuid.uuid4(), assessment_id=en_assessment.id, text="hello", type=QuestionType.listening, points=1)
        db.add(en_q4)
        db.commit()
        db.add_all([
            Answer(id=uuid.uuid4(), question_id=en_q4.id, text="ನಮಸ್ಕಾರ / hello", is_correct=True, explanation="'hello' means greeting."),
            Answer(id=uuid.uuid4(), question_id=en_q4.id, text="goodbye", is_correct=False)
        ])
        db.commit()

        en_q5 = Question(id=uuid.uuid4(), assessment_id=en_assessment.id, text="I drink milk", type=QuestionType.speaking, points=1)
        db.add(en_q5)
        db.commit()
        db.add(Answer(id=uuid.uuid4(), question_id=en_q5.id, text="I drink milk", is_correct=True, explanation="Perfect speaking."))
        db.commit()

        en_q6 = Question(id=uuid.uuid4(), assessment_id=en_assessment.id, text="I ____ milk.", type=QuestionType.fill_in_blank, points=1)
        db.add(en_q6)
        db.commit()
        db.add_all([
            Answer(id=uuid.uuid4(), question_id=en_q6.id, text="drink", is_correct=True, explanation="Correct."),
            Answer(id=uuid.uuid4(), question_id=en_q6.id, text="drinks", is_correct=False)
        ])
        db.commit()

        # ----------------------------------------------------
        # 6. SEED INTERMEDIATE & ADVANCED TIERS FOR ALL LANGUAGES
        # ----------------------------------------------------
        print("Seeding Intermediate & Advanced Course Tracks...")
        tiered_courses_data = [
            # Kannada
            {
                "lang": "kn",
                "title": "Kannada Conversational & Grammar Track",
                "desc": "ಕನ್ನಡ ಸಂಭಾಷಣೆ, ಕಾಲಗಳು ಮತ್ತು ವಾಕ್ಯ ರಚನೆ (Master intermediate conversational Kannada, verb tenses, and daily dialogues).",
                "level": CourseLevel.Intermediate,
                "topic": "ದೈನಂದಿನ ಸಂಭಾಷಣೆಗಳು (Daily Conversations)",
                "topic_desc": "ಕಚೇರಿ, ಮಾರುಕಟ್ಟೆ ಮತ್ತು ಸಾರ್ವಜನಿಕ ಸ್ಥಳಗಳಲ್ಲಿ ಮಾತನಾಡುವುದು (Conversations in markets, offices, and social environments).",
                "lesson": "ಮಾರುಕಟ್ಟೆಯಲ್ಲಿ ಸಂಭಾಷಣೆ (Conversations at the Market)",
                "content": "# ಮಾರುಕಟ್ಟೆ ಸಂಭಾಷಣೆ\n- ತರಕಾರಿ ಬೆಲೆ ಎಷ್ಟು? (How much are vegetables?)\n- ನನಗೆ ಎರಡು ಸೇಬು ಕೊಡಿ (Give me two apples).\n- ಧನ್ಯವಾದಗಳು, ಮತ್ತೆ ಬರುತ್ತೇನೆ (Thank you, will visit again).",
                "quiz": "ಕನ್ನಡ ಸಂಭಾಷಣಾ ರಸಪ್ರಶ್ನೆ (Conversational Quiz)",
                "q": "ಮಾರುಕಟ್ಟೆಯಲ್ಲಿ 'ಬೆಲೆ ಎಷ್ಟು?' ಎಂದರೆ ಏನು?",
                "ans": [
                    {"text": "How much does it cost?", "correct": True, "exp": "ಸರಿ! 'ಬೆಲೆ ಎಷ್ಟು' ಎಂದರೆ ಬೆಲೆ ಕೇಳುವುದು."},
                    {"text": "Where is the market?", "correct": False},
                    {"text": "What time is it?", "correct": False}
                ]
            },
            {
                "lang": "kn",
                "title": "Kannada Advanced Fluency & Literature",
                "desc": "ಕನ್ನಡ ಸುಧಾರಿತ ಸಾಹಿತ್ಯ, ಗಾದೆಗಳು ಮತ್ತು ನಿರರ್ಗಳ ಓದುವಿಕೆ (Explore classical and contemporary Kannada literature, idioms, and fluent comprehension).",
                "level": CourseLevel.Advanced,
                "topic": "ಗಾದೆ ಮಾತುಗಳು ಮತ್ತು ರೂಪಕಗಳು (Proverbs & Metaphors)",
                "topic_desc": "ಕನ್ನಡದ ಜನಪ್ರಿಯ ಗಾದೆಗಳು ಮತ್ತು ಅವುಗಳ ಆಂತರಿಕ ಅರ್ಥ (Popular Kannada proverbs and their contextual meanings).",
                "lesson": "ಕಾಯಕವೇ ಕೈಲಾಸ - ತಾತ್ವಿಕ ಪಠ್ಯ (Work is Worship)",
                "content": "# ಕಾಯಕವೇ ಕೈಲಾಸ\nಬಸವಣ್ಣನವರ ಪ್ರಸಿದ್ಧ ವಚನ ತತ್ವ. ಕರ್ತವ್ಯನಿಷ್ಠೆ ಮತ್ತು ಸಮಾಜ ಸೇವೆಯನ್ನು ಶ್ರೇಷ್ಠವಾಗಿ ಪರಿಗಣಿಸಲಾಗಿದೆ.",
                "quiz": "ಸುಧಾರಿತ ಕನ್ನಡ ಸಾಹಿತ್ಯ ಪರೀಕ್ಷೆ (Advanced Literature Quiz)",
                "q": "'ಕಾಯಕವೇ ಕೈಲಾಸ' ಎಂಬ ಸಂದೇಶವನ್ನು ಯಾರು ನೀಡಿದರು?",
                "ans": [
                    {"text": "ಬಸವಣ್ಣನವರು (Basavanna)", "correct": True, "exp": "ಸರಿ! ಬಸವಣ್ಣನವರು ಈ ತತ್ವವನ್ನು ಪ್ರತಿಪಾದಿಸಿದರು."},
                    {"text": "ಕಾಳಿದಾಸ (Kalidasa)", "correct": False},
                    {"text": "ವಾಲ್ಮೀಕಿ (Valmiki)", "correct": False}
                ]
            },
            # Hindi
            {
                "lang": "hi",
                "title": "Hindi Daily Conversations & Grammar",
                "desc": "हिन्दी दैनिक वार्तालाप एवं व्यावहारिक व्याकरण (Master everyday dialogues, verb conjugations, and practical sentence structures).",
                "level": CourseLevel.Intermediate,
                "topic": "दैनिक वार्तालाप (Daily Communication)",
                "topic_desc": "बाजार, यात्रा और मित्रों के साथ बातचीत (Conversations during shopping, travel, and socializing).",
                "lesson": "बाजार में बातचीत (At the Marketplace)",
                "content": "# बाजार में खरीदारी\n- इस फल का दाम क्या है? (What is the price of this fruit?)\n- कृपया मुझे दो किलो दीजिए (Please give me two kilograms).",
                "quiz": "हिन्दी वार्तालाप प्रश्नोत्तरी (Intermediate Dialogue Quiz)",
                "q": "'इसका दाम क्या है?' का सही अनुवाद क्या है?",
                "ans": [
                    {"text": "What is the price of this?", "correct": True, "exp": "बिल्कुल सही! दाम पूछने के लिए यह प्रयुक्त होता है।"},
                    {"text": "Where is the shop?", "correct": False},
                    {"text": "How far is the market?", "correct": False}
                ]
            },
            {
                "lang": "hi",
                "title": "Hindi Advanced Fluency & Literary Expression",
                "desc": "हिन्दी उच्चस्तरीय साहित्य एवं गहन अभिव्यक्ति (Advanced comprehension, Hindi literature, proverbs, and professional eloquence).",
                "level": CourseLevel.Advanced,
                "topic": "साहित्य और मुहावरे (Literature & Idioms)",
                "topic_desc": "प्रसिद्ध मुहावरे और साहित्यिक रचनाएं (Famous idioms and literary prose analysis).",
                "lesson": "मुहावरों का सटीक प्रयोग (Mastering Hindi Idioms)",
                "content": "# हिन्दी मुहावरे\n- 'आँखों का तारा' - बहुत प्यारा होना।\n- 'ईद का चाँद होना' - बहुत दिनों बाद दिखाई देना।",
                "quiz": "हिन्दी प्रगत साहित्य परीक्षा (Advanced Hindi Quiz)",
                "q": "'आँखों का तारा' मुहावरे का सही अर्थ क्या है?",
                "ans": [
                    {"text": "बहुत प्यारा (Extremely beloved)", "correct": True, "exp": "सही! यह अत्यधिक प्रिय व्यक्ति के लिए प्रयुक्त होता है।"},
                    {"text": "बहुत दूर (Very far)", "correct": False},
                    {"text": "गुस्से में होना (Being angry)", "correct": False}
                ]
            },
            # Telugu
            {
                "lang": "te",
                "title": "Telugu Daily Conversations & Grammar",
                "desc": "తెలుగు సంభాషణలు మరియు వ్యాకరణం (Intermediate spoken Telugu, sentence construction, and situational conversations).",
                "level": CourseLevel.Intermediate,
                "topic": "నిత్య జీవిత సంభాషణలు (Everyday Dialogues)",
                "topic_desc": "షాపింగ్, ప్రయాణం మరియు స్నేహితులతో సంభాషణ (Conversations during travel, shopping, and social visits).",
                "lesson": "దుకాణంలో సంభాషణ (Conversation at a Store)",
                "content": "# దుకాణంలో షాపింగ్\n- దీని వెల ఎంత? (How much is this?)\n- నాకు రెండు ఇవ్వండి (Give me two please).",
                "quiz": "తెలుగు సంభాషణ క్విజ్ (Intermediate Telugu Quiz)",
                "q": "'దీని వెల ఎంత?' అనే వాక్యానికి ఆంగ్ల అర్థం ఏమిటి?",
                "ans": [
                    {"text": "How much is this?", "correct": True, "exp": "సరైన సమాధానం! వెల అడగడానికి ఉపయోగిస్తారు."},
                    {"text": "Where is the shop?", "correct": False},
                    {"text": "Who are you?", "correct": False}
                ]
            },
            {
                "lang": "te",
                "title": "Telugu Advanced Fluency & Literature",
                "desc": "తెలుగు ఉన్నత స్థాయి భాషా ప్రావీణ్యం (Advanced Telugu prose, proverbs, poetry, and fluent reading mastery).",
                "level": CourseLevel.Advanced,
                "topic": "సామెతలు మరియు జాతీయాలు (Proverbs & Idioms)",
                "topic_desc": "తెలుగు సామెతలు మరియు వాటి అంతరార్థం (Telugu idioms and cultural expressions).",
                "lesson": "తెలుగు సామెతల పరిచయం (Telugu Idioms & Expressions)",
                "content": "# తెలుగు సామెతలు\nసామెతలు భాషకు అందాన్ని, లోతైన అర్థాన్ని చేకూరుస్తాయి.",
                "quiz": "తెలుగు సాహిత్య పరీక్ష (Advanced Telugu Quiz)",
                "q": "సామెతలు భాషలో దేనికి తోడ్పడతాయి?",
                "ans": [
                    {"text": "లోతైన భావ వ్యక్తీకరణకు (Deep contextual expression)", "correct": True, "exp": "సరైన సమాధానం!"},
                    {"text": "కేవలం అక్షరాల కోసం (Only for letters)", "correct": False},
                    {"text": "ఏమీ లేదు (None)", "correct": False}
                ]
            },
            # Marathi
            {
                "lang": "mr",
                "title": "Marathi Conversational Fluency",
                "desc": "मराठी दैनंदिन संभाषण आणि व्याकरण (Intermediate spoken Marathi, verb tenses, and practical dialogues).",
                "level": CourseLevel.Intermediate,
                "topic": "दैनंदिन संभाषण (Daily Conversations)",
                "topic_desc": "बाजार, प्रवास आणि कार्यालयीन संभाषण (Conversations at market, travel, and social contexts).",
                "lesson": "बाजारातील खरेदी (At the Market)",
                "content": "# बाजारात संवाद\n- याची किंमत काय आहे? (What is the price of this?)\n- मला दोन किलो द्या (Give me two kilograms).",
                "quiz": "मराठी संभाषण प्रश्नमंजुषा (Intermediate Marathi Quiz)",
                "q": "'याची किंमत काय आहे?' चा योग्य अर्थ निवडा:",
                "ans": [
                    {"text": "What is the price of this?", "correct": True, "exp": "बरोबर! किंमत विचारण्यासाठी हे वापरतात."},
                    {"text": "Where is the market?", "correct": False},
                    {"text": "When will you come?", "correct": False}
                ]
            },
            {
                "lang": "mr",
                "title": "Marathi Advanced Comprehension",
                "desc": "मराठी प्रगत वाचन आणि साहित्य (Advanced comprehension, Marathi idioms, proverbs, and literary expressions).",
                "level": CourseLevel.Advanced,
                "topic": "म्हणी आणि वाक्प्रचार (Proverbs & Idioms)",
                "topic_desc": "मराठीतील प्रसिद्ध म्हणी आणि त्यांचे अर्थ (Popular Marathi proverbs and their cultural context).",
                "lesson": "मराठी म्हणींचा सराव (Mastering Marathi Proverbs)",
                "content": "# प्रसिद्ध म्हणी\n- 'अति तेथे माती' - कोणत्याही गोष्टीचा अतिरेक वाईट असतो.",
                "quiz": "प्रगत मराठी साहित्य परीक्षा (Advanced Marathi Quiz)",
                "q": "'अति तेथे माती' या म्हणीचा योग्य अर्थ काय आहे?",
                "ans": [
                    {"text": "कोणत्याही गोष्टीचा अतिरेक वाईट (Excess of anything is bad)", "correct": True, "exp": "बरोबर! अतिरेक हानिकारक असतो."},
                    {"text": "माती गोळा करणे (Collecting soil)", "correct": False},
                    {"text": "झाडे लावणे (Planting trees)", "correct": False}
                ]
            },
            # English
            {
                "lang": "en",
                "title": "English Intermediate Dialogues & Grammar",
                "desc": "Master everyday conversations, complex tenses, active listening, and situational grammar in English.",
                "level": CourseLevel.Intermediate,
                "topic": "Practical Everyday Communication",
                "topic_desc": "Dialogue skills for travel, dining, workplace collaboration, and customer inquiries.",
                "lesson": "Ordering and Inquiring at a Restaurant",
                "content": "# Practical English Dialogue\n- Could I please have the menu?\n- What do you recommend for lunch today?\n- May we please have the bill?",
                "quiz": "Intermediate English Communication Quiz",
                "q": "Which sentence is the polite way to ask for the bill at a restaurant?",
                "ans": [
                    {"text": "Could we please have the check / bill?", "correct": True, "exp": "Correct! Polite modal question form."},
                    {"text": "Give bill now.", "correct": False},
                    {"text": "Where is food?", "correct": False}
                ]
            },
            {
                "lang": "en",
                "title": "English Professional Fluency & Advanced Composition",
                "desc": "Advanced literacy, nuanced expressions, professional discourse, and critical reading comprehension.",
                "level": CourseLevel.Advanced,
                "topic": "Nuanced Idioms & Professional Rhetoric",
                "topic_desc": "Idiomatic expressions, formal debate phrases, and analytical text comprehension.",
                "lesson": "Analytical Reasoning and Idiomatic Mastery",
                "content": "# Advanced Expressions\n- 'To hit the nail on the head' - to describe exactly what is causing a situation.\n- 'Burn the midnight oil' - to work late into the night.",
                "quiz": "Advanced English Fluency Assessment",
                "q": "What does the idiom 'to burn the midnight oil' signify?",
                "ans": [
                    {"text": "To study or work late into the night", "correct": True, "exp": "Correct! Derived from oil lamps used by late-night scholars."},
                    {"text": "To waste fuel", "correct": False},
                    {"text": "To cook dinner late", "correct": False}
                ]
            }
        ]

        for tc in tiered_courses_data:
            if tc["lang"] in lang_map:
                target_lang_obj = lang_map[tc["lang"]]
                is_inter = tc["level"] == CourseLevel.Intermediate
                cefr_val = "B1" if is_inter else "B2"
                min_s = 60.0 if is_inter else 80.0
                max_s = 79.9 if is_inter else 99.9
                skills_val = ["speaking", "listening", "vocabulary"] if is_inter else ["grammar", "writing", "reading"]
                goals_val = ["conversation", "career", "daily-life"] if is_inter else ["career", "academic", "exams"]
                diff_val = "intermediate" if is_inter else "advanced"

                c = Course(
                    id=uuid.uuid4(),
                    title=tc["title"],
                    description=tc["desc"],
                    language_id=target_lang_obj.id,
                    level=tc["level"],
                    cefr_level=cefr_val,
                    min_score=min_s,
                    max_score=max_s,
                    skills_json=json.dumps(skills_val),
                    goals_json=json.dumps(goals_val),
                    difficulty=diff_val,
                    thumbnail_url="https://images.unsplash.com/photo-1543783207-ec64e4d95325",
                    is_published=True
                )
                db.add(c)
                db.commit()

                top = Topic(id=uuid.uuid4(), course_id=c.id, title=tc["topic"], description=tc["topic_desc"], order=1)
                db.add(top)
                db.commit()

                les = Lesson(id=uuid.uuid4(), topic_id=top.id, title=tc["lesson"], content=tc["content"], duration_minutes=20, order=1)
                db.add(les)
                db.commit()

                asmt = Assessment(id=uuid.uuid4(), lesson_id=les.id, title=tc["quiz"], type=AssessmentType.quiz, pass_percentage=70.0)
                db.add(asmt)
                db.commit()

                q_obj = Question(id=uuid.uuid4(), assessment_id=asmt.id, text=tc["q"], type=QuestionType.multiple_choice, points=1)
                db.add(q_obj)
                db.commit()

                for a_item in tc["ans"]:
                    db.add(Answer(
                        id=uuid.uuid4(),
                        question_id=q_obj.id,
                        text=a_item["text"],
                        is_correct=a_item["correct"],
                        explanation=a_item.get("exp")
                    ))
                db.commit()

        # Seed demo user kaverijarali98@gmail.com
        demo_learner = Learner(
            id=uuid.uuid4(),
            email="kaverijarali98@gmail.com",
            hashed_password=get_password_hash("Kaveri@123"),
            full_name="Kaveri Jarali",
            preferred_language_id=lang_map["en"].id,
            target_language_id=lang_map["kn"].id,
            proficiency_level=ProficiencyLevel.Beginner,
            xp=240,
            gems=650,
            hearts=5,
            streak=3,
            has_completed_placement_test=False
        )
        db.add(demo_learner)
        db.commit()
        print("Demo user kaverijarali98@gmail.com seeded successfully!")

        print("Database seeded with complete multi-tier curriculum (Beginner, Intermediate, Advanced) across all languages!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
