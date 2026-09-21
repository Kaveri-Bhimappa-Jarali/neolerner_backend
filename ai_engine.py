import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
import models, schemas, gamification
from recommendation_engine import default_recommendation_engine

# Strict Concept Translation Matrix for all 5 Supported Languages
MULTILINGUAL_CONCEPTS = {
    "hello": {"en": "Hello", "kn": "ನಮಸ್ಕಾರ", "te": "నమస్కారం", "mr": "नमस्कार", "hi": "नमस्ते"},
    "milk": {"en": "Milk", "kn": "ಹಾಲು", "te": "పాలు", "mr": "दूध", "hi": "दूध"},
    "dog": {"en": "Dog", "kn": "ನಾಯಿ", "te": "కుక్క", "mr": "कुत्रा", "hi": "कुत्ता"},
    "house": {"en": "House", "kn": "ಮನೆ", "te": "ఇల్లు", "mr": "घर", "hi": "घर"},
    "book": {"en": "Book", "kn": "ಪುಸ್ತಕ", "te": "పుస్తకం", "mr": "पुस्तक", "hi": "किताब"},
    "water": {"en": "Water", "kn": "ನೀರು", "te": "నీరు", "mr": "पाणी", "hi": "पानी"},
    "friend": {"en": "Friend", "kn": "ಸ್ನೇಹಿತ", "te": "స్నేహితుడు", "mr": "मित्र", "hi": "दोस्त"},
    "school": {"en": "School", "kn": "ಶಾಲೆ", "te": "ಪಾಠಶಾಲ", "mr": "शाळा", "hi": "विद्यालय"},
    "sun": {"en": "Sun", "kn": "ಸೂರ್ಯ", "te": "సూర్యుడు", "mr": "सूर्य", "hi": "सूरज"},
    "food": {"en": "Food", "kn": "ಆಹಾರ", "te": "ఆహారం", "mr": "अन्न", "hi": "भोजन"},
    "cat": {"en": "Cat", "kn": "ಬೆಕ್ಕು", "te": "పిల్లి", "mr": "मांजर", "hi": "बिल्ली"},
    "tree": {"en": "Tree", "kn": "ಮರ", "te": "చెట్టు", "mr": "झाड", "hi": "पेड़"},
    "flower": {"en": "Flower", "kn": "ಹೂವು", "te": "పువ్వు", "mr": "फूल", "hi": "फूल"},
    "one": {"en": "One", "kn": "ಒಂದು", "te": "ఒకటి", "mr": "एक", "hi": "एक"},
    "two": {"en": "Two", "kn": "ಎರಡು", "te": "రెండు", "mr": "दोन", "hi": "दो"},
    "drink": {"en": "Drink", "kn": "ಕುಡಿ", "te": "త్రాగు", "mr": "पिणे", "hi": "पीना"},
    "eat": {"en": "Eat", "kn": "ತಿನ್ನು", "te": "తిను", "mr": "खाणे", "hi": "खाना"},
    "read": {"en": "Read", "kn": "ಓದು", "te": "చదువు", "mr": "वाचणे", "hi": "पढ़ना"},
    "write": {"en": "Write", "kn": "ಬರೆ", "te": "రాయి", "mr": "लिहिणे", "hi": "लिखना"},
    "thank_you": {"en": "Thank you", "kn": "ಧನ್ಯವಾದ", "te": "ಧನ್ಯವಾದಗಳು", "mr": "धन्यवाद", "hi": "धन्यवाद"}
}

def get_concept_word(concept: str, lang_code: str) -> str:
    return MULTILINGUAL_CONCEPTS.get(concept, {}).get(lang_code, MULTILINGUAL_CONCEPTS.get(concept, {}).get("en", concept))

def format_bilingual_option(concept: str, target_code: str, pref_code: str = "en") -> str:
    return get_concept_word(concept, target_code)

def calculate_predicted_proficiency(learner_id: uuid.UUID, db: Session) -> schemas.ProficiencyPredictionResponse:
    """
    Learner Proficiency Prediction Algorithm:
    Evaluates multi-competency accuracy across reading, writing, comprehension,
    listening, and speaking assessments to compute a weighted proficiency score
    and benchmark classification.
    """
    learner = db.query(models.Learner).filter(models.Learner.id == learner_id).first()
    if not learner:
        return schemas.ProficiencyPredictionResponse(
            reading=0.0, writing=0.0, comprehension=0.0, listening=0.0, speaking=0.0,
            composite_score=0.0, benchmark_level="Emergent Reader", total_assessments=0,
            recommendation_focus="Start basic phonics and reading"
        )

    # Fetch all assessment results
    results = db.query(models.AssessmentResult).filter(
        models.AssessmentResult.learner_id == learner_id
    ).all()

    # Competency score trackers: { 'reading': [scores], ... }
    competencies: Dict[str, List[float]] = {
        "reading": [],
        "writing": [],
        "comprehension": [],
        "listening": [],
        "speaking": []
    }

    if not results:
        # Initial baseline calibration based on registration proficiency level
        baseline = 25.0 if learner.proficiency_level == models.ProficiencyLevel.Beginner else (
            55.0 if learner.proficiency_level == models.ProficiencyLevel.Intermediate else 80.0
        )
        for k in competencies:
            competencies[k].append(baseline)
    else:
        for r in results:
            assessment = db.query(models.Assessment).filter(models.Assessment.id == r.assessment_id).first()
            if not assessment or not assessment.questions:
                competencies["reading"].append(r.score)
                continue

            # Weight by question competency tag if available
            for q in assessment.questions:
                tag = (q.competency_tag or "reading").lower()
                if tag in ["multiple_choice", "word_order", "phonics", "reading"]:
                    competencies["reading"].append(r.score)
                elif tag in ["fill_in_blank", "translation", "writing"]:
                    competencies["writing"].append(r.score)
                elif tag in ["match_pairs", "true_false", "comprehension"]:
                    competencies["comprehension"].append(r.score)
                elif tag in ["listening"]:
                    competencies["listening"].append(r.score)
                elif tag in ["speaking"]:
                    competencies["speaking"].append(r.score)
                else:
                    competencies["reading"].append(r.score)

    # Calculate mean per competency
    reading_avg = sum(competencies["reading"]) / len(competencies["reading"]) if competencies["reading"] else 0.0
    writing_avg = sum(competencies["writing"]) / len(competencies["writing"]) if competencies["writing"] else 0.0
    comp_avg = sum(competencies["comprehension"]) / len(competencies["comprehension"]) if competencies["comprehension"] else 0.0
    listening_avg = sum(competencies["listening"]) / len(competencies["listening"]) if competencies["listening"] else 0.0
    speaking_avg = sum(competencies["speaking"]) / len(competencies["speaking"]) if competencies["speaking"] else 0.0

    # Composite weighted proficiency index
    composite = (
        0.25 * reading_avg +
        0.20 * writing_avg +
        0.20 * comp_avg +
        0.15 * listening_avg +
        0.20 * speaking_avg
    )
    composite = round(min(100.0, max(0.0, composite)), 1)

    # 4-Tier Standardized Literacy Benchmark
    if composite < 40.0:
        benchmark = "Emergent Reader (ಮೂಲ ಓದುಗ / शुरुआती स्तर)"
    elif composite < 70.0:
        benchmark = "Early Reader (ಮಧ್ಯಮ ಓದುಗ / प्रारंभिक स्तर)"
    elif composite < 90.0:
        benchmark = "Fluent Reader (ನಿರರ್ಗಳ ಓದುಗ / धाराप्रवाह स्तर)"
    else:
        benchmark = "Master Reader (ಪ್ರವೀಣ ಓದುಗ / प्रवीण स्तर)"

    # Identify weakest skill for focal recommendation
    skill_scores = {
        "Reading & Phonics": reading_avg,
        "Writing & Spelling": writing_avg,
        "Reading Comprehension": comp_avg,
        "Listening & Auditory": listening_avg,
        "Speaking & Pronunciation": speaking_avg
    }
    weakest_skill = min(skill_scores, key=skill_scores.get)
    rec_focus = f"Reinforce {weakest_skill} with targeted interactive drills"

    # Persist predicted values back to Learner record
    learner.predicted_proficiency_score = composite
    learner.benchmark_level = benchmark
    db.commit()

    return schemas.ProficiencyPredictionResponse(
        reading=round(reading_avg, 1),
        writing=round(writing_avg, 1),
        comprehension=round(comp_avg, 1),
        listening=round(listening_avg, 1),
        speaking=round(speaking_avg, 1),
        composite_score=composite,
        benchmark_level=benchmark,
        total_assessments=len(results),
        recommendation_focus=rec_focus
    )


def generate_ai_recommendations(learner_id: uuid.UUID, db: Session) -> List[schemas.AIRecommendationItem]:
    """
    Adaptive Learning Recommendation Engine:
    Inspects mistakes, SRS memory retention, and learning path progress to generate
    context-aware, prioritized learning recommendations.
    """
    learner = db.query(models.Learner).filter(models.Learner.id == learner_id).first()
    if not learner:
        return []

    recommendations: List[schemas.AIRecommendationItem] = []

    # 1. Unresolved Mistakes in ReviewItem
    mistakes_count = db.query(models.ReviewItem).filter(
        models.ReviewItem.learner_id == learner_id,
        models.ReviewItem.is_resolved == False
    ).count()
    if mistakes_count > 0:
        recommendations.append(schemas.AIRecommendationItem(
            id=f"rec-mistakes-{learner_id}",
            title=f"Review {mistakes_count} Missed Concept{'s' if mistakes_count > 1 else ''}",
            reason="AI identified previous exercise mistakes requiring remediation.",
            type="remedial_phonics",
            action_url="/adaptive-practice?focus=mistakes",
            priority=1,
            confidence=0.95,
            competency_tag="mistakes"
        ))

    # 2. Spaced Repetition Due Cards
    due_srs_count = db.query(models.VocabularySRS).filter(
        models.VocabularySRS.learner_id == learner_id,
        models.VocabularySRS.next_review_date <= datetime.utcnow()
    ).count()
    if due_srs_count > 0:
        recommendations.append(schemas.AIRecommendationItem(
            id=f"rec-srs-{learner_id}",
            title=f"Spaced Repetition: {due_srs_count} Vocabulary Card{'s' if due_srs_count > 1 else ''} Due",
            reason="Reinforce long-term memory retention before forgetting occurs.",
            type="spaced_review",
            action_url="/review/srs",
            priority=2,
            confidence=0.92,
            competency_tag="vocabulary"
        ))

    # 3. Next Milestone in Target Learning Path
    if learner.target_language_id:
        target_course = db.query(models.Course).filter(
            models.Course.language_id == learner.target_language_id,
            models.Course.is_published == True
        ).first()

        if target_course:
            # Find first uncompleted lesson
            all_lessons: List[models.Lesson] = []
            for t in target_course.topics:
                all_lessons.extend(t.lessons)

            for l in all_lessons:
                prog = db.query(models.LearningProgress).filter(
                    models.LearningProgress.learner_id == learner_id,
                    models.LearningProgress.lesson_id == l.id,
                    models.LearningProgress.status == models.ProgressStatus.completed
                ).first()
                if not prog:
                    recommendations.append(schemas.AIRecommendationItem(
                        id=f"rec-lesson-{l.id}",
                        title=f"Next Milestone: {l.title}",
                        reason=f"Progress through your {target_course.title} curriculum.",
                        type="next_milestone",
                        action_url=f"/lessons/{l.id}",
                        priority=3,
                        confidence=0.88,
                        competency_tag=l.competency_tag or "phonics"
                    ))
                    break

    # 4. Adaptive Booster Drill for Weakest Competency
    prediction = calculate_predicted_proficiency(learner_id, db)
    scores = {
        "reading": prediction.reading,
        "writing": prediction.writing,
        "comprehension": prediction.comprehension,
        "listening": prediction.listening,
        "speaking": prediction.speaking
    }
    weakest = min(scores, key=scores.get)
    if scores[weakest] < 75.0:
        recommendations.append(schemas.AIRecommendationItem(
            id=f"rec-adaptive-{weakest}",
            title=f"AI Adaptive Booster: {weakest.capitalize()} Workout",
            reason=f"Current predicted mastery for {weakest} is {scores[weakest]}%. Complete an adaptive drill to boost your score.",
            type="challenge",
            action_url=f"/adaptive-practice?focus={weakest}",
            priority=4,
            confidence=0.85,
            competency_tag=weakest
        ))

    return sorted(recommendations, key=lambda x: x.priority)


def generate_adaptive_lesson(learner_id: uuid.UUID, focus: Optional[str], db: Session) -> schemas.AdaptiveLessonResponse:
    """
    Personalized Lesson Generation Workflow:
    Dynamically constructs a tailored exercise set addressing the learner's
    specific weaknesses and target vocabulary.
    """
    learner = db.query(models.Learner).filter(models.Learner.id == learner_id).first()
    target_lang_code = "en"
    pref_lang_code = "en"
    if learner:
        if learner.target_language:
            target_lang_code = learner.target_language.code
        if learner.preferred_language:
            pref_lang_code = learner.preferred_language.code

    questions: List[schemas.AdaptiveQuestion] = []
    session_id = str(uuid.uuid4())

    # Determine learner CEFR scaffold level
    cefr = (learner.cefr_level or "A0").upper() if learner else "A0"
    if cefr in ["C1", "C2", "ADVANCED"]:
        scaffold_level = "advanced"
    elif cefr in ["B1", "B2", "INTERMEDIATE"]:
        scaffold_level = "intermediate"
    else:
        scaffold_level = "beginner"

    if focus:
        focus = focus.lower().strip()
        if focus in ['listening', 'auditory']:
            focus = 'listening'
        elif focus in ['speaking', 'pronunciation']:
            focus = 'speaking'
        elif focus in ['writing', 'spelling', 'grammar']:
            focus = 'writing'
        elif focus in ['reading', 'comprehension', 'vocabulary']:
            focus = 'reading'
        elif focus in ['match', 'match_pairs', 'speed']:
            focus = 'match_pairs'

    # Focus 1: Unresolved Mistakes
    if focus == "mistakes":
        unresolved_items = db.query(models.ReviewItem).filter(
            models.ReviewItem.learner_id == learner_id,
            models.ReviewItem.is_resolved == False
        ).limit(5).all()

        for item in unresolved_items:
            q = item.question
            if q:
                answers = [
                    schemas.AdaptiveQuestionAnswer(
                        id=str(a.id),
                        text=a.text,
                        is_correct=a.is_correct,
                        explanation=a.explanation
                    ) for a in q.answers
                ]
                questions.append(schemas.AdaptiveQuestion(
                    id=str(q.id),
                    text=q.text,
                    type=q.type,
                    competency_tag=q.competency_tag or "reading",
                    points=q.points,
                    prompt_audio_text=q.text,
                    target_word=q.text,
                    scaffold_level=scaffold_level,
                    answers=answers
                ))

    # Focus 2: Dynamic synthetic exercises from Multilingual Concept Pool
    if len(questions) < 5:
        import random
        concept_keys = list(MULTILINGUAL_CONCEPTS.keys())
        random.shuffle(concept_keys)

        needed = 5 - len(questions)
        selected_concepts = concept_keys[:needed]

        for idx, c_key in enumerate(selected_concepts):
            q_id = str(uuid.uuid4())
            target_word = get_concept_word(c_key, target_lang_code)
            pref_meaning = get_concept_word(c_key, pref_lang_code)
            other_concepts = [c for c in concept_keys if c != c_key]

            # Cycle through exercise types based on requested competency
            if focus == "listening" or (not focus and idx % 5 == 0):
                q_type = models.QuestionType.listening
                q_text = target_word
                distractor_concepts = random.sample(other_concepts, min(3, len(other_concepts)))
                ans_list = [
                    schemas.AdaptiveQuestionAnswer(
                        id=str(uuid.uuid4()),
                        text=pref_meaning,
                        is_correct=True,
                        explanation=f"Correct! '{target_word}' means '{pref_meaning}'."
                    ),
                ]
                for d_c in distractor_concepts:
                    ans_list.append(schemas.AdaptiveQuestionAnswer(
                        id=str(uuid.uuid4()),
                        text=get_concept_word(d_c, pref_lang_code),
                        is_correct=False
                    ))
                random.shuffle(ans_list)
                tag = "listening"

            elif focus == "speaking" or (not focus and idx % 5 == 1):
                q_type = models.QuestionType.speaking
                q_text = target_word
                ans_list = [
                    schemas.AdaptiveQuestionAnswer(
                        id=str(uuid.uuid4()),
                        text=target_word,
                        is_correct=True,
                        explanation=f"Accurate pronunciation for '{target_word}' ({pref_meaning})!"
                    )
                ]
                tag = "speaking"

            elif focus == "writing" or (not focus and idx % 5 == 2):
                q_type = models.QuestionType.fill_in_blank
                # Create a spelling challenge with missing letters in target language word
                word_len = len(target_word)
                if word_len > 3:
                    masked = target_word[0] + "_" * (word_len - 2) + target_word[-1]
                elif word_len > 1:
                    masked = target_word[0] + "_" * (word_len - 1)
                else:
                    masked = target_word
                spell_prompts = {
                    "kn": f"ಕಾಗುಣಿತವನ್ನು ಪೂರ್ಣಗೊಳಿಸಿ ({masked}):",
                    "te": f"సరైన అక్షరాలను పూరించండి ({masked}):",
                    "hi": f"वर्तनी पूरी करें ({masked}):",
                    "mr": f"स्पेलिंग पूर्ण करा ({masked}):",
                    "en": f"Complete the spelling ({masked}):"
                }
                q_text = spell_prompts.get(target_lang_code, f"Complete the spelling ({masked}):")
                ans_list = [
                    schemas.AdaptiveQuestionAnswer(
                        id=str(uuid.uuid4()),
                        text=target_word,
                        is_correct=True,
                        explanation=f"Well done! Full word is '{target_word}' ({pref_meaning})."
                    )
                ]
                tag = "writing"

            elif focus == "match_pairs" or (not focus and idx % 5 == 3):
                q_type = models.QuestionType.match_pairs
                match_prompts = {
                    "kn": "ಪದಗಳನ್ನು ಅವುಗಳ ಸರಿಯಾದ ಅರ್ಥದೊಂದಿಗೆ ಹೊಂದಿಸಿ:",
                    "te": "పదాలను సరైన అర్థాలతో జతపరచండి:",
                    "hi": "शब्दों को उनके सही अर्थ से मिलाएं:",
                    "mr": "शब्दांच्या योग्य जोड्या जुळवा:",
                    "en": "Match the vocabulary words with their meanings:"
                }
                q_text = match_prompts.get(target_lang_code, "Match the vocabulary pairs:")
                pair_concepts = [c_key] + random.sample(other_concepts, min(7, len(other_concepts)))
                pair_str = ",".join([
                    f"{get_concept_word(pc, target_lang_code)}:{get_concept_word(pc, pref_lang_code)}"
                    for pc in pair_concepts
                ])
                ans_list = [
                    schemas.AdaptiveQuestionAnswer(
                        id=str(uuid.uuid4()),
                        text=pair_str,
                        is_correct=True,
                        explanation="All vocabulary pairs matched successfully!"
                    )
                ]
                tag = "comprehension"

            elif focus == "reading":
                q_type = models.QuestionType.multiple_choice
                q_text = f"Translate '{target_word}'"
                distractor_concepts = random.sample(other_concepts, min(3, len(other_concepts)))
                ans_list = [
                    schemas.AdaptiveQuestionAnswer(
                        id=str(uuid.uuid4()),
                        text=pref_meaning,
                        is_correct=True,
                        explanation=f"Correct translation! '{target_word}' means '{pref_meaning}'."
                    )
                ]
                for d_c in distractor_concepts:
                    ans_list.append(schemas.AdaptiveQuestionAnswer(
                        id=str(uuid.uuid4()),
                        text=get_concept_word(d_c, pref_lang_code),
                        is_correct=False
                    ))
                random.shuffle(ans_list)
                tag = "reading"

            else: # multiple_choice default
                q_type = models.QuestionType.multiple_choice
                mc_prompts = {
                    "kn": f"'{target_word}' ಪದದ ಸರಿಯಾದ ಅರ್ಥವೇನು?",
                    "te": f"'{target_word}' అనే పదానికి అర్థం ఏమిటి?",
                    "hi": f"'{target_word}' शब्द का क्या अर्थ है?",
                    "mr": f"'{target_word}' या शब्दाचा अर्थ काय आहे?",
                    "en": f"What is the meaning of '{target_word}'?"
                }
                q_text = mc_prompts.get(target_lang_code, f"What is the meaning of '{target_word}'?")
                distractor_concepts = random.sample(other_concepts, min(3, len(other_concepts)))
                target_meaning = get_concept_word(c_key, pref_lang_code)
                ans_list = [
                    schemas.AdaptiveQuestionAnswer(
                        id=str(uuid.uuid4()),
                        text=target_meaning,
                        is_correct=True,
                        explanation=f"Correct! '{target_word}' translates to '{target_meaning}'."
                    )
                ]
                for d_c in distractor_concepts:
                    ans_list.append(schemas.AdaptiveQuestionAnswer(
                        id=str(uuid.uuid4()),
                        text=get_concept_word(d_c, pref_lang_code),
                        is_correct=False
                    ))
                random.shuffle(ans_list)
                tag = "reading"

            questions.append(schemas.AdaptiveQuestion(
                id=q_id,
                text=q_text,
                type=q_type,
                competency_tag=tag,
                points=1,
                prompt_audio_text=target_word,
                prompt_translation=pref_meaning,
                target_word=target_word,
                scaffold_level=scaffold_level,
                answers=ans_list
            ))

    mode_titles = {
        "speaking": "AI Pronunciation & Speaking Lab",
        "listening": "AI Auditory & Listening Studio",
        "writing": "AI Writing & Spelling Challenge",
        "match_pairs": "AI Speed Matching Drill",
        "mistakes": "AI Remedial Mistake Correction",
        "reading": "AI Reading & Comprehension Drill"
    }
    title = mode_titles.get(focus, "AI Personalized Adaptive Workout")
    reason = f"Generated on-the-fly by LinguaLearn AI Engine tailored for your {target_lang_code.upper()} track."

    return schemas.AdaptiveLessonResponse(
        session_id=session_id,
        title=title,
        reason=reason,
        target_competency=focus or "composite",
        language_code=target_lang_code,
        questions=questions,
        total_points=len(questions)
    )


def process_adaptive_lesson_submission(
    learner_id: uuid.UUID,
    submission: schemas.AdaptiveLessonSubmit,
    db: Session
) -> schemas.AssessmentResultResponse:
    """
    Submits and resolves an adaptive lesson workout, rewarding the learner,
    updating mistake items, restoring hearts, and recalculating proficiency predictions.
    """
    learner = db.query(models.Learner).filter(models.Learner.id == learner_id).first()
    if not learner:
        raise ValueError("Learner not found")

    correct_count = sum(1 for s in submission.submissions if s.is_correct)
    total_count = len(submission.submissions)
    score_pct = (correct_count / total_count * 100.0) if total_count > 0 else 100.0
    passed = score_pct >= 70.0

    # Resolve any review mistake items
    for s in submission.submissions:
        if s.is_correct:
            try:
                q_uuid = uuid.UUID(s.question_id)
                review_item = db.query(models.ReviewItem).filter(
                    models.ReviewItem.learner_id == learner_id,
                    models.ReviewItem.question_id == q_uuid
                ).first()
                if review_item:
                    review_item.is_resolved = True
                    review_item.resolved_at = datetime.utcnow()
            except Exception:
                pass

    # Gamification Rewards
    xp_earned = 15 + (correct_count * 5)
    gems_earned = 10 if passed else 2
    hearts_lost = 0

    # Practice Bonus: Restore 1 heart if scored >= 80%
    if score_pct >= 80.0 and learner.hearts < 5:
        learner.hearts = min(5, learner.hearts + 1)

    gamification.award_xp_and_gems(learner, xp_earned, gems_earned, db)
    gamification.update_streak(learner, db)

    # Re-evaluate predicted proficiency score
    calculate_predicted_proficiency(learner_id, db)
    db.commit()

    return schemas.AssessmentResultResponse(
        id=uuid.uuid4(),
        learner_id=learner_id,
        assessment_id=uuid.uuid4(),
        score=score_pct,
        max_score=100.0,
        passed=passed,
        completed_at=datetime.utcnow(),
        xp_earned=xp_earned,
        gems_earned=gems_earned,
        hearts_lost=hearts_lost,
        current_hearts=learner.hearts
    )


def generate_learning_path(
    learner_id: uuid.UUID,
    db: Session,
    course_id: Optional[uuid.UUID] = None
) -> schemas.LearningPathResponse:
    """
    Learning Path Management API Engine:
    Traverses the course curriculum as a sequential DAG roadmap with locked/unlocked
    states, mastery progress, and milestone checkpoints.
    Dynamically resolves target course based on optional explicit course_id, existing
    active progress, or placement test score recommendation.
    """
    learner = db.query(models.Learner).filter(models.Learner.id == learner_id).first()
    if not learner:
        raise ValueError("Learner not found")

    target_course = None
    target_lang_name = "Target Language"

    if learner.target_language:
        target_lang_name = f"{learner.target_language.name} ({learner.target_language.native_name})"

    # 1. Explicit course_id requested
    if course_id:
        target_course = db.query(models.Course).filter(
            models.Course.id == course_id,
            models.Course.is_published == True
        ).first()

    # 2. Check if learner has recent progress in a course for target language
    if not target_course and learner.target_language_id:
        recent_prog = db.query(models.LearningProgress).filter(
            models.LearningProgress.learner_id == learner.id
        ).order_by(models.LearningProgress.last_accessed.desc()).all()
        for prog in recent_prog:
            if prog.lesson and prog.lesson.topic and prog.lesson.topic.course:
                if prog.lesson.topic.course.language_id == learner.target_language_id and prog.lesson.topic.course.is_published:
                    target_course = prog.lesson.topic.course
                    break

    # 3. Use recommendation engine based on placement score & CEFR level
    if not target_course and learner.target_language_id:
        try:
            from recommendation_engine import default_recommendation_engine
            rec_res = default_recommendation_engine.rank_courses_for_learner(learner, db)
            if rec_res.primary_recommendation and rec_res.primary_recommendation.course_id:
                target_course = db.query(models.Course).filter(
                    models.Course.id == rec_res.primary_recommendation.course_id,
                    models.Course.is_published == True
                ).first()
        except Exception:
            pass

    # 4. Fallback: match by learner proficiency level
    if not target_course and learner.target_language_id:
        target_course = db.query(models.Course).filter(
            models.Course.language_id == learner.target_language_id,
            models.Course.level == learner.proficiency_level,
            models.Course.is_published == True
        ).first()

    # 5. Ultimate fallback: first published course for target language
    if not target_course and learner.target_language_id:
        target_course = db.query(models.Course).filter(
            models.Course.language_id == learner.target_language_id,
            models.Course.is_published == True
        ).first()

    if not target_course:
        target_course = db.query(models.Course).filter(models.Course.is_published == True).first()
        if target_course and target_course.language:
            target_lang_name = target_course.language.name

    if not target_course:
        return schemas.LearningPathResponse(
            course_id=None,
            course_title="No Course Available",
            target_language_name=target_lang_name,
            nodes=[],
            current_node_index=0,
            total_nodes=0,
            completion_rate=0.0,
            predicted_proficiency_score=learner.predicted_proficiency_score or 0.0,
            benchmark_level=learner.benchmark_level or "Emergent Reader"
        )

    nodes: List[schemas.LearningPathNode] = []
    order_counter = 1
    has_unlocked_current = False
    current_active_idx = 0
    completed_nodes_count = 0

    for topic in target_course.topics:
        for lesson in topic.lessons:
            # 1. Lesson Node (Reading / Phonics Theory)
            lesson_prog = db.query(models.LearningProgress).filter(
                models.LearningProgress.learner_id == learner_id,
                models.LearningProgress.lesson_id == lesson.id,
                models.LearningProgress.status == models.ProgressStatus.completed
            ).first()

            is_lesson_done = lesson_prog is not None
            if is_lesson_done:
                l_status = "completed"
                completed_nodes_count += 1
            elif not has_unlocked_current:
                l_status = "in_progress"
                has_unlocked_current = True
                current_active_idx = order_counter - 1
            else:
                l_status = "locked"

            nodes.append(schemas.LearningPathNode(
                id=f"node-lesson-{lesson.id}",
                title=lesson.title,
                description=f"Topic: {topic.title}",
                type="lesson",
                status=l_status,
                order=order_counter,
                score=100.0 if is_lesson_done else None,
                duration_minutes=lesson.duration_minutes or 10,
                lesson_id=lesson.id,
                competency_tag=lesson.competency_tag or "phonics"
            ))
            order_counter += 1

            # 2. Assessment Node (Interactive Quiz Checkpoint)
            if lesson.assessments:
                assessment = lesson.assessments[0]
                result = db.query(models.AssessmentResult).filter(
                    models.AssessmentResult.learner_id == learner_id,
                    models.AssessmentResult.assessment_id == assessment.id,
                    models.AssessmentResult.passed == True
                ).first()

                is_quiz_done = result is not None
                if is_quiz_done:
                    q_status = "completed"
                    completed_nodes_count += 1
                elif is_lesson_done and not has_unlocked_current:
                    q_status = "in_progress"
                    has_unlocked_current = True
                    current_active_idx = order_counter - 1
                else:
                    q_status = "locked" if not (is_lesson_done and is_quiz_done) else "completed"

                nodes.append(schemas.LearningPathNode(
                    id=f"node-quiz-{assessment.id}",
                    title=f"{lesson.title} Quiz Checkpoint",
                    description="Passing score required to advance (70%+)",
                    type="quiz",
                    status=q_status,
                    order=order_counter,
                    score=result.score if result else None,
                    duration_minutes=15,
                    assessment_id=assessment.id,
                    competency_tag="comprehension"
                ))
                order_counter += 1

        # 3. Topic Milestone Checkpoint Node
        nodes.append(schemas.LearningPathNode(
            id=f"node-milestone-{topic.id}",
            title=f"🏆 Milestone: {topic.title} Mastery",
            description=f"Comprehensive literacy milestone for {topic.title}",
            type="milestone_checkpoint",
            status="completed" if completed_nodes_count >= (order_counter - 1) else "locked",
            order=order_counter,
            score=None,
            duration_minutes=5,
            competency_tag="milestone"
        ))
        order_counter += 1

    total_nodes = len(nodes)
    completion_rate = round((completed_nodes_count / total_nodes * 100.0), 1) if total_nodes > 0 else 0.0

    return schemas.LearningPathResponse(
        course_id=target_course.id,
        course_title=target_course.title,
        target_language_name=target_lang_name,
        nodes=nodes,
        current_node_index=current_active_idx,
        total_nodes=total_nodes,
        completion_rate=completion_rate,
        predicted_proficiency_score=learner.predicted_proficiency_score or 0.0,
        benchmark_level=learner.benchmark_level or "Emergent Reader"
    )


# ---------------------------------------------------------------------------
# INITIAL EXAM & DIAGNOSTIC ENGINE (Computer Adaptive Diagnostic Test)
# ---------------------------------------------------------------------------

def generate_placement_test_session(
    learner_id: uuid.UUID,
    db: Session
) -> schemas.PlacementTestSessionResponse:
    """
    Generates a comprehensive 15-question Initial Exam testing the learner's
    target learning language across phonics, vocabulary, listening, spelling,
    pair matching, reading comprehension, grammar, and voice pronunciation.
    Correct questions and answers present both the target learning language
    and the interface language.
    """
    learner = db.query(models.Learner).filter(models.Learner.id == learner_id).first()
    if not learner:
        raise ValueError("Learner not found")

    target_lang = None
    if learner.target_language_id:
        target_lang = db.query(models.Language).filter(models.Language.id == learner.target_language_id).first()

    if not target_lang:
        target_lang = db.query(models.Language).filter(models.Language.code == "kn").first()
        if not target_lang:
            target_lang = db.query(models.Language).first()

    pref_lang = None
    if learner.preferred_language_id:
        pref_lang = db.query(models.Language).filter(models.Language.id == learner.preferred_language_id).first()
    if not pref_lang:
        pref_lang = db.query(models.Language).filter(models.Language.code == "en").first()

    target_lang_id = target_lang.id
    target_lang_code = target_lang.code
    target_lang_name = target_lang.name
    pref_lang_name = pref_lang.name if pref_lang else "English"
    pref_lang_code = pref_lang.code if pref_lang else "en"

    # Language-specific question prompt templates
    first_vowel_data = {
        "kn": ("ಕನ್ನಡ ಅಕ್ಷರಮಾಲೆಯ ಮೊದಲನೆಯ ಸ್ವರ ಯಾವುದು?", "ಅ (a)", ["ಕ (ka)", "ರ (ra)", "ಮ (ma)"], "ಸರಿ! 'ಅ' ಕನ್ನಡ ಅಕ್ಷರಮಾಲೆಯ ಮೊದಲನೆಯ ಹ್ರಸ್ವ ಸ್ವರವಾಗಿದೆ."),
        "te": ("తెలుగు వర్ణమాలలో మొదటి అచ్చు ఏది?", "అ (a)", ["క (ka)", "ర (ra)", "మ (ma)"], "సరైన సమాధానం! 'అ' మొదటి అచ్చు."),
        "hi": ("हिन्दी वर्णमाला का पहला स्वर कौन सा है?", "अ (a)", ["क (ka)", "र (ra)", "म (ma)"], "सही! 'अ' हिन्दी वर्णमाला का पहला स्वर है।"),
        "mr": ("मराठी वर्णमालेतील पहिला स्वर कोणता आहे?", "अ (a)", ["क (ka)", "र (ra)", "म (ma)"], "बरोबर! 'अ' हा पहिला स्वर आहे."),
        "en": ("Which letter represents the primary open vowel sound /a/ in English?", "The letter A (/æ/ or /ɑː/)", ["The letter B (/b/)", "The letter K (/k/)", "The letter T (/t/)"], "Correct! 'A' is the first letter and vowel sound in the English alphabet.")
    }

    sentence_data = {
        "en": {
            "sentence": "I drink fresh milk",
            "distractors": ["I read a book", "I go to school", "The dog is in the house"]
        },
        "kn": {
            "sentence": "ನಾನು ಹಾಲು ಕುಡಿಯುತ್ತೇನೆ",
            "distractors": ["ನಾನು ಪುಸ್ತಕ ಓದುತ್ತೇನೆ", "ನಾನು ಶಾಲೆಗೆ ಹೋಗುತ್ತೇನೆ", "ನಾಯಿ ಮನೆಯಲ್ಲಿದೆ"]
        },
        "te": {
            "sentence": "నేను పాలు తాగుతాను",
            "distractors": ["నేను పుస్తకం చదువుతాను", "నేను పాఠశాలకు వెళ్తాను", "కుక్క ఇంట్లో ఉంది"]
        },
        "mr": {
            "sentence": "मी दूध पितो",
            "distractors": ["मी पुस्तक वाचतो", "मी शाळेत जातो", "कुत्रा घरात आहे"]
        },
        "hi": {
            "sentence": "मैं दूध पीता हूँ",
            "distractors": ["मैं किताब पढ़ता हूँ", "मैं विद्यालय जाता हूँ", "कुत्ता घर में है"]
        }
    }

    speaking_data = {
        "en": {
            "phrase": "Hello, my good friend",
            "meanings": {"en": "Hello, my good friend", "kn": "ನಮಸ್ಕಾರ, ನನ್ನ ಸ್ನೇಹಿತ", "te": "నమస్కారం, నా స్నేహితుడు", "mr": "नमस्कार, माझा मित्र", "hi": "नमस्ते, मेरे दोस्त"}
        },
        "kn": {
            "phrase": "ನಮಸ್ಕಾರ, ಸ್ನೇಹಿತ",
            "meanings": {"en": "Hello, friend", "kn": "ನಮಸ್ಕಾರ, ಸ್ನೇಹಿತ", "te": "నమస్కారం, స్నేహితుడు", "mr": "नमस्कार, मित्र", "hi": "नमस्ते, दोस्त"}
        },
        "te": {
            "phrase": "నమస్కారం, స్నేహితుడు",
            "meanings": {"en": "Hello, friend", "kn": "ನಮಸ್ಕಾರ, ಸ್ನೇಹಿತ", "te": "నమస్కారం, స్నేహితుడు", "mr": "नमस्कार, मित्र", "hi": "नमस्ते, दोस्त"}
        },
        "mr": {
            "phrase": "नमस्कार, मित्र",
            "meanings": {"en": "Hello, friend", "kn": "ನಮಸ್ಕಾರ, ಸ್ನೇಹಿತ", "te": "నమస్కారం, స్నేహితుడు", "mr": "नमस्कार, मित्र", "hi": "नमस्ते, दोस्त"}
        },
        "hi": {
            "phrase": "नमस्ते, दोस्त",
            "meanings": {"en": "Hello, friend", "kn": "ನಮಸ್ಕಾರ, ಸ್ನೇಹಿತ", "te": "నమస్కారం, స్నేహితుడు", "mr": "नमस्कार, मित्र", "hi": "नमस्ते, दोस्त"}
        }
    }

    cloze_templates = {
        "en": "I drink ____ every morning.",
        "kn": "ನಾನು ____ ಕುಡಿಯುತ್ತೇನೆ.",
        "te": "నేను ____ తాగుతాను.",
        "mr": "मी ____ पितो.",
        "hi": "मैं ____ पीता हूँ।"
    }

    import random
    session_id = f"initial-exam-{uuid.uuid4().hex[:8]}"
    questions: List[schemas.PlacementTestQuestion] = []

    # ----------------------------------------------------
    # Q1: Phonics / Vowel Sound Identification (Difficulty 1)
    # ----------------------------------------------------
    v_info = first_vowel_data.get(target_lang_code, first_vowel_data["en"])
    q1_answers = [
        schemas.AdaptiveQuestionAnswer(id=str(uuid.uuid4()), text=v_info[1], is_correct=True, explanation=v_info[3])
    ]
    for d in v_info[2]:
        q1_answers.append(schemas.AdaptiveQuestionAnswer(id=str(uuid.uuid4()), text=d, is_correct=False))
    random.shuffle(q1_answers)

    questions.append(schemas.PlacementTestQuestion(
        id=str(uuid.uuid4()),
        text=v_info[0],
        type=models.QuestionType.multiple_choice,
        competency_tag="phonics",
        difficulty_level=1,
        points=1,
        prompt_audio_text=None,
        prompt_translation=None,
        target_word=v_info[1].split()[0],
        interface_translation=None,
        answers=q1_answers
    ))

    # ----------------------------------------------------
    # Q2: Common Greetings & Salutation (Difficulty 1)
    # ----------------------------------------------------
    pref_hello = get_concept_word("hello", pref_lang_code)
    target_hello = get_concept_word("hello", target_lang_code)
    q2_prompts = {
        "kn": f"ಕನ್ನಡದಲ್ಲಿ '{pref_hello}' ಎಂದು ಶುಭಾಶಯ ತಿಳಿಸಲು ಸೂಕ್ತ ಪದ ಯಾವುದು?",
        "te": f"తెలుగులో '{pref_hello}' తెలపడానికి ఏ పదం వాడతారు?",
        "hi": f"हिन्दी में '{pref_hello}' कहने के लिए कौन सा शब्द सही है?",
        "mr": f"मराठीत '{pref_hello}' म्हणण्यासाठी कोणता शब्द वापरतात?",
        "en": f"Select the polite greeting in English (meaning '{pref_hello}'):"
    }
    q2_text = q2_prompts.get(target_lang_code, f"Select the greeting meaning '{pref_hello}':")

    q2_answers = [
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("hello", target_lang_code),
            is_correct=True,
            explanation=f"Correct! '{target_hello}' is the greeting in {target_lang_name} (meaning '{pref_hello}')."
        ),
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("milk", target_lang_code),
            is_correct=False
        ),
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("dog", target_lang_code),
            is_correct=False
        ),
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("house", target_lang_code),
            is_correct=False
        )
    ]
    random.shuffle(q2_answers)

    questions.append(schemas.PlacementTestQuestion(
        id=str(uuid.uuid4()),
        text=q2_text,
        type=models.QuestionType.multiple_choice,
        competency_tag="vocabulary",
        difficulty_level=1,
        points=1,
        prompt_audio_text=None,
        prompt_translation=None,
        target_word=target_hello,
        interface_translation=pref_hello,
        answers=q2_answers
    ))

    # ----------------------------------------------------
    # Q3: Everyday Noun Identification (Difficulty 1)
    # ----------------------------------------------------
    pref_house = get_concept_word("house", pref_lang_code)
    target_house = get_concept_word("house", target_lang_code)
    q3_prompts = {
        "kn": f"ಕನ್ನಡದಲ್ಲಿ '{pref_house}' ಅರ್ಥವನ್ನು ನೀಡುವ ಪದ ಯಾವುದು?",
        "te": f"తెలుగులో '{pref_house}' అర్థాన్ని ఇచ్చే పదం ఏది?",
        "hi": f"हिन्दी में '{pref_house}' अर्थ वाला शब्द कौन सा है?",
        "mr": f"मराठीत '{pref_house}' अर्थ असणारा शब्द कोणता?",
        "en": f"Which word in English means '{pref_house}'?"
    }
    q3_text = q3_prompts.get(target_lang_code, f"Which word means '{pref_house}'?")

    q3_answers = [
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("house", target_lang_code),
            is_correct=True,
            explanation=f"'{target_house}' translates to '{pref_house}'."
        ),
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("book", target_lang_code),
            is_correct=False
        ),
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("water", target_lang_code),
            is_correct=False
        ),
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("school", target_lang_code),
            is_correct=False
        )
    ]
    random.shuffle(q3_answers)

    questions.append(schemas.PlacementTestQuestion(
        id=str(uuid.uuid4()),
        text=q3_text,
        type=models.QuestionType.multiple_choice,
        competency_tag="vocabulary",
        difficulty_level=1,
        points=1,
        prompt_audio_text=None,
        prompt_translation=None,
        target_word=target_house,
        interface_translation=pref_house,
        answers=q3_answers
    ))

    # ----------------------------------------------------
    # Q4: Auditory Listening Discrimination (Difficulty 2)
    # ----------------------------------------------------
    target_water = get_concept_word("water", target_lang_code)
    pref_water = get_concept_word("water", pref_lang_code)
    q4_prompts = {
        "kn": "🎧 ಆಡಿಯೋ ಆಲಿಸಿ ಮತ್ತು ಕೇಳಿದ ಸರಿಯಾದ ಪದವನ್ನು ಆಯ್ಕೆಮಾಡಿ:",
        "te": "🎧 ఆడియోను విని సరైన పదాన్ని ఎంచుకోండి:",
        "hi": "🎧 ऑडियो सुनकर सही शब्द चुनें:",
        "mr": "🎧 ऑडिओ ऐका आणि योग्य शब्द निवडा:",
        "en": "🎧 Listen to the spoken audio and select the word you hear:"
    }

    q4_answers = [
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("water", target_lang_code),
            is_correct=True,
            explanation=f"Audio matched '{target_water}' which means '{pref_water}'."
        ),
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("milk", target_lang_code),
            is_correct=False
        ),
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("food", target_lang_code),
            is_correct=False
        ),
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("dog", target_lang_code),
            is_correct=False
        )
    ]
    random.shuffle(q4_answers)

    questions.append(schemas.PlacementTestQuestion(
        id=str(uuid.uuid4()),
        text=q4_prompts.get(target_lang_code, "🎧 Listen to the spoken audio and select the word you hear:"),
        type=models.QuestionType.listening,
        competency_tag="listening",
        difficulty_level=2,
        points=2,
        prompt_audio_text=target_water,
        prompt_translation=pref_water,
        target_word=target_water,
        interface_translation=pref_water,
        answers=q4_answers
    ))

    # ----------------------------------------------------
    # Q5: Food & Beverage Vocabulary (Difficulty 2)
    # ----------------------------------------------------
    target_milk = get_concept_word("milk", target_lang_code)
    pref_milk = get_concept_word("milk", pref_lang_code)
    q5_prompts = {
        "kn": f"'{target_milk}' ಪದದ ಅರ್ಥವೇನು?",
        "te": f"'{target_milk}' అనే పదానికి అర్థం ఏమిటి?",
        "hi": f"'{target_milk}' शब्द का सही अर्थ क्या है?",
        "mr": f"'{target_milk}' या शब्दाचा अर्थ काय आहे?",
        "en": f"What is the meaning of '{target_milk}'?"
    }

    q5_answers = [
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("milk", pref_lang_code),
            is_correct=True,
            explanation=f"'{target_milk}' translates to '{pref_milk}' in your interface language."
        ),
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("water", pref_lang_code),
            is_correct=False
        ),
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("book", pref_lang_code),
            is_correct=False
        ),
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("dog", pref_lang_code),
            is_correct=False
        )
    ]
    random.shuffle(q5_answers)

    questions.append(schemas.PlacementTestQuestion(
        id=str(uuid.uuid4()),
        text=q5_prompts.get(target_lang_code, f"What is the meaning of '{target_milk}'?"),
        type=models.QuestionType.multiple_choice,
        competency_tag="vocabulary",
        difficulty_level=2,
        points=2,
        prompt_audio_text=target_milk,
        prompt_translation=pref_milk,
        target_word=target_milk,
        interface_translation=pref_milk,
        answers=q5_answers
    ))

    # ----------------------------------------------------
    # Q6: Auditory Word Comprehension (Difficulty 2)
    # ----------------------------------------------------
    target_dog = get_concept_word("dog", target_lang_code)
    pref_dog = get_concept_word("dog", pref_lang_code)
    q6_prompts = {
        "kn": "🎧 ಆಡಿಯೋ ಆಲಿಸಿ ಮತ್ತು ಸರಿಯಾದ ಅರ್ಥವನ್ನು ಆಯ್ಕೆಮಾಡಿ:",
        "te": "🎧 ఆడియోను విని సరైన అర్థాన్ని ఎంచుకోండి:",
        "hi": "🎧 ऑडियो सुनकर सही अर्थ चुनें:",
        "mr": "🎧 ऑडिओ ऐका आणि योग्य अर्थ निवडा:",
        "en": "🎧 Listen to the spoken audio and select the correct meaning:"
    }

    q6_answers = [
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("dog", pref_lang_code),
            is_correct=True,
            explanation=f"Accurate! Spoken audio was '{target_dog}' which means '{pref_dog}'."
        ),
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("cat", pref_lang_code),
            is_correct=False
        ),
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("friend", pref_lang_code),
            is_correct=False
        ),
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("house", pref_lang_code),
            is_correct=False
        )
    ]
    random.shuffle(q6_answers)

    questions.append(schemas.PlacementTestQuestion(
        id=str(uuid.uuid4()),
        text=q6_prompts.get(target_lang_code, "🎧 Listen to the audio and select the correct meaning:"),
        type=models.QuestionType.listening,
        competency_tag="listening",
        difficulty_level=2,
        points=2,
        prompt_audio_text=target_dog,
        prompt_translation=pref_dog,
        target_word=target_dog,
        interface_translation=pref_dog,
        answers=q6_answers
    ))

    # ----------------------------------------------------
    # Q7: Social & Family Relationships (Difficulty 2)
    # ----------------------------------------------------
    pref_friend = get_concept_word("friend", pref_lang_code)
    target_friend = get_concept_word("friend", target_lang_code)
    q7_prompts = {
        "kn": f"ಕನ್ನಡದಲ್ಲಿ '{pref_friend}' ಅರ್ಥವನ್ನು ನೀಡುವ ಪದ ಯಾವುದು?",
        "te": f"తెలుగులో '{pref_friend}' అర్థాన్ని ఇచ్చే పదం ఏది?",
        "hi": f"हिन्दी में '{pref_friend}' अर्थ वाला शब्द कौन सा है?",
        "mr": f"मराठीत '{pref_friend}' अर्थ असणारा शब्द कोणता?",
        "en": f"Which word in English means '{pref_friend}'?"
    }

    q7_answers = [
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("friend", target_lang_code),
            is_correct=True,
            explanation=f"'{target_friend}' translates to '{pref_friend}'."
        ),
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("dog", target_lang_code),
            is_correct=False
        ),
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("tree", target_lang_code),
            is_correct=False
        ),
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("sun", target_lang_code),
            is_correct=False
        )
    ]
    random.shuffle(q7_answers)

    questions.append(schemas.PlacementTestQuestion(
        id=str(uuid.uuid4()),
        text=q7_prompts.get(target_lang_code, f"Which word means '{pref_friend}'?"),
        type=models.QuestionType.multiple_choice,
        competency_tag="vocabulary",
        difficulty_level=2,
        points=2,
        prompt_audio_text=None,
        prompt_translation=None,
        target_word=target_friend,
        interface_translation=pref_friend,
        answers=q7_answers
    ))

    # ----------------------------------------------------
    # Q8: Spelling & Missing Character (Difficulty 2)
    # ----------------------------------------------------
    w8 = get_concept_word("book", target_lang_code)
    pref_book = get_concept_word("book", pref_lang_code)
    w_len = len(w8)
    masked8 = w8[0] + "_" * max(1, w_len - 2) + (w8[-1] if w_len > 2 else "")
    
    q8_prompts = {
        "kn": f"'{pref_book}' ಪದದ ಕಾಗುಣಿತವನ್ನು ಪೂರ್ಣಗೊಳಿಸಿ ({masked8}):",
        "te": f"'{pref_book}' పదానికి సరైన అక్షరాలను పూరించండి ({masked8}):",
        "hi": f"'{pref_book}' शब्द की वर्तनी पूरी करें ({masked8}):",
        "mr": f"'{pref_book}' शब्दाचे स्पेलिंग पूर्ण करा ({masked8}):",
        "en": f"Complete the spelling for the word meaning '{pref_book}' ({masked8}):"
    }

    questions.append(schemas.PlacementTestQuestion(
        id=str(uuid.uuid4()),
        text=q8_prompts.get(target_lang_code, f"Complete the spelling ({masked8}):"),
        type=models.QuestionType.fill_in_blank,
        competency_tag="writing",
        difficulty_level=2,
        points=2,
        prompt_audio_text=None,
        prompt_translation=None,
        target_word=w8,
        interface_translation=pref_book,
        answers=[schemas.AdaptiveQuestionAnswer(id=str(uuid.uuid4()), text=w8, is_correct=True, explanation=f"Full spelling: '{w8}' ({pref_book})")]
    ))

    # ----------------------------------------------------
    # Q9: Numerals & Quantities (Difficulty 3)
    # ----------------------------------------------------
    pref_one = get_concept_word("one", pref_lang_code)
    target_one = get_concept_word("one", target_lang_code)
    q9_prompts = {
        "kn": "ಕನ್ನಡದಲ್ಲಿ '1' ಸಂಖ್ಯೆಯನ್ನು ಸೂಚಿಸುವ ಪದ ಯಾವುದು?",
        "te": "తెలుగులో '1' సంఖ్యను సూచించే పదం ఏది?",
        "hi": "हिन्दी में '1' संख्या दर्शाने वाला शब्द कौन सा है?",
        "mr": "मराठीत '1' संख्या दर्शवणारा शब्द कोणता?",
        "en": "Which word represents the numeral '1' in English?"
    }

    q9_answers = [
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("one", target_lang_code),
            is_correct=True,
            explanation=f"'{target_one}' is cardinal number 1 ({pref_one})."
        ),
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("two", target_lang_code),
            is_correct=False
        ),
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("house", target_lang_code),
            is_correct=False
        ),
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("water", target_lang_code),
            is_correct=False
        )
    ]
    random.shuffle(q9_answers)

    questions.append(schemas.PlacementTestQuestion(
        id=str(uuid.uuid4()),
        text=q9_prompts.get(target_lang_code, "Which word represents numeral 1?"),
        type=models.QuestionType.multiple_choice,
        competency_tag="vocabulary",
        difficulty_level=3,
        points=3,
        prompt_audio_text=None,
        prompt_translation=None,
        target_word=target_one,
        interface_translation=pref_one,
        answers=q9_answers
    ))

    # ----------------------------------------------------
    # Q10: Action Verbs (Difficulty 3)
    # ----------------------------------------------------
    pref_drink = get_concept_word("drink", pref_lang_code)
    target_drink = get_concept_word("drink", target_lang_code)
    q10_prompts = {
        "kn": f"ಕನ್ನಡದಲ್ಲಿ '{pref_drink}' ಕ್ರಿಯಾಪದವನ್ನು ಆಯ್ಕೆಮಾಡಿ:",
        "te": f"తెలుగులో '{pref_drink}' క్రియా పదాన్ని ఎంచుకోండి:",
        "hi": f"हिन्दी में '{pref_drink}' क्रिया शब्द को चुनें:",
        "mr": f"मराठीत '{pref_drink}' क्रियापद निवडा:",
        "en": f"Select the action verb meaning '{pref_drink}' in English:"
    }

    q10_answers = [
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("drink", target_lang_code),
            is_correct=True,
            explanation=f"'{target_drink}' means 'to drink' ({pref_drink})."
        ),
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("eat", target_lang_code),
            is_correct=False
        ),
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("book", target_lang_code),
            is_correct=False
        ),
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("house", target_lang_code),
            is_correct=False
        )
    ]
    random.shuffle(q10_answers)

    questions.append(schemas.PlacementTestQuestion(
        id=str(uuid.uuid4()),
        text=q10_prompts.get(target_lang_code, f"Select the verb meaning '{pref_drink}':"),
        type=models.QuestionType.multiple_choice,
        competency_tag="vocabulary",
        difficulty_level=3,
        points=3,
        prompt_audio_text=None,
        prompt_translation=None,
        target_word=target_drink,
        interface_translation=pref_drink,
        answers=q10_answers
    ))

    # ----------------------------------------------------
    # Q11: Rapid Paired Vocabulary Association (Difficulty 3)
    # ----------------------------------------------------
    q11_prompts = {
        "kn": "ಕನ್ನಡ ಪದಗಳನ್ನು ಅವುಗಳ ಸರಿಯಾದ ಅರ್ಥದೊಂದಿಗೆ ಹೊಂದಿಸಿ:",
        "te": "తెలుగు పదాలను వాటి సరైన అర్థాలతో జతపరచండి:",
        "hi": "हिन्दी शब्दों को उनके सही अर्थ से मिलाएं:",
        "mr": "मराठी शब्दांच्या त्यांच्या योग्य जोड्या जुळवा:",
        "en": "Match the English vocabulary words with their meanings:"
    }

    pair_pool = [
        (get_concept_word("hello", target_lang_code), get_concept_word("hello", pref_lang_code)),
        (get_concept_word("milk", target_lang_code), get_concept_word("milk", pref_lang_code)),
        (get_concept_word("friend", target_lang_code), get_concept_word("friend", pref_lang_code)),
        (get_concept_word("water", target_lang_code), get_concept_word("water", pref_lang_code))
    ]
    pair_str = ",".join([f"{p[0]}:{p[1]}" for p in pair_pool])

    questions.append(schemas.PlacementTestQuestion(
        id=str(uuid.uuid4()),
        text=q11_prompts.get(target_lang_code, "Match the vocabulary pairs:"),
        type=models.QuestionType.match_pairs,
        competency_tag="comprehension",
        difficulty_level=3,
        points=3,
        prompt_audio_text=None,
        prompt_translation=None,
        target_word=get_concept_word("hello", target_lang_code),
        interface_translation=get_concept_word("hello", pref_lang_code),
        answers=[schemas.AdaptiveQuestionAnswer(id=str(uuid.uuid4()), text=pair_str, is_correct=True, explanation=f"All vocabulary pairs matched correctly!")]
    ))

    # ----------------------------------------------------
    # Q12: Full Word Written Spelling (Difficulty 3)
    # ----------------------------------------------------
    w12 = get_concept_word("sun", target_lang_code)
    pref_sun = get_concept_word("sun", pref_lang_code)
    q12_prompts = {
        "kn": f"'{pref_sun}' ಪದವನ್ನು ಟೈಪ್ ಮಾಡಿ ಅಥವಾ ಬರೆಯಿರಿ:",
        "te": f"'{pref_sun}' పదాన్ని టైప్ చేయండి లేదా వ్రాయండి:",
        "hi": f"'{pref_sun}' शब्द को टाइप करें या लिखें:",
        "mr": f"'{pref_sun}' शब्द टाइप करा किंवा लिहा:",
        "en": f"Type or spell the word meaning '{pref_sun}':"
    }

    questions.append(schemas.PlacementTestQuestion(
        id=str(uuid.uuid4()),
        text=q12_prompts.get(target_lang_code, f"Type or spell the word meaning '{pref_sun}':"),
        type=models.QuestionType.fill_in_blank,
        competency_tag="writing",
        difficulty_level=3,
        points=3,
        prompt_audio_text=None,
        prompt_translation=None,
        target_word=w12,
        interface_translation=pref_sun,
        answers=[schemas.AdaptiveQuestionAnswer(id=str(uuid.uuid4()), text=w12, is_correct=True, explanation=f"Full spelling: '{w12}' ({pref_sun})")]
    ))

    # ----------------------------------------------------
    # Q13: Sentence Reading Comprehension (Difficulty 4)
    # ----------------------------------------------------
    target_sentence = sentence_data.get(target_lang_code, sentence_data["en"])["sentence"]
    pref_sentence = sentence_data.get(pref_lang_code, sentence_data["en"])["sentence"]
    pref_distractors = sentence_data.get(pref_lang_code, sentence_data["en"])["distractors"]

    q13_prompts = {
        "kn": f"ಈ ವಾಕ್ಯವನ್ನು ಓದಿ ಮತ್ತು ಸರಿಯಾದ ಅರ್ಥವನ್ನು ಆಯ್ಕೆಮಾಡಿ: '{target_sentence}'",
        "te": f"ఈ వాక్యాన్ని చదివి సరైన అర్థాన్ని ఎంచుకోండి: '{target_sentence}'",
        "hi": f"इस वाक्य को पढ़ें और सही अर्थ चुनें: '{target_sentence}'",
        "mr": f"हे वाक्य वाचा आणि योग्य अर्थ निवडा: '{target_sentence}'",
        "en": f"Read this sentence and choose the accurate translation: '{target_sentence}'"
    }

    q13_answers = [
        schemas.AdaptiveQuestionAnswer(id=str(uuid.uuid4()), text=pref_sentence, is_correct=True, explanation=f"Accurate translation: '{target_sentence}' means '{pref_sentence}'.")
    ]
    for d in pref_distractors:
        q13_answers.append(schemas.AdaptiveQuestionAnswer(id=str(uuid.uuid4()), text=d, is_correct=False))
    random.shuffle(q13_answers)

    questions.append(schemas.PlacementTestQuestion(
        id=str(uuid.uuid4()),
        text=q13_prompts.get(target_lang_code, f"Read and choose the accurate translation: '{target_sentence}'"),
        type=models.QuestionType.multiple_choice,
        competency_tag="reading",
        difficulty_level=4,
        points=4,
        prompt_audio_text=target_sentence,
        prompt_translation=pref_sentence,
        target_word=target_sentence,
        interface_translation=pref_sentence,
        answers=q13_answers
    ))

    # ----------------------------------------------------
    # Q14: Sentence Construction & Grammar (Difficulty 4)
    # ----------------------------------------------------
    cloze_text = cloze_templates.get(target_lang_code, "I drink ____ every morning.")
    q14_prompts = {
        "kn": f"ವಾಕ್ಯವನ್ನು ಸೂಕ್ತ ಪದದಿಂದ ಪೂರ್ಣಗೊಳಿಸಿ: '{cloze_text}'",
        "te": f"వాక్యాన్ని సరైన పదంతో పూర్తి చేయండి: '{cloze_text}'",
        "hi": f"वाक्य को उपयुक्त शब्द से पूरा करें: '{cloze_text}'",
        "mr": f"योग्य शब्द वापरून वाक्य पूर्ण करा: '{cloze_text}'",
        "en": f"Complete the sentence with the appropriate word: '{cloze_text}'"
    }

    target_milk_ans = get_concept_word("milk", target_lang_code)
    q14_answers = [
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=target_milk_ans,
            is_correct=True,
            explanation=f"Correct! '{target_milk_ans}' fits the context."
        ),
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("book", target_lang_code),
            is_correct=False
        ),
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("house", target_lang_code),
            is_correct=False
        ),
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=get_concept_word("school", target_lang_code),
            is_correct=False
        )
    ]
    random.shuffle(q14_answers)

    questions.append(schemas.PlacementTestQuestion(
        id=str(uuid.uuid4()),
        text=q14_prompts.get(target_lang_code, f"Complete the sentence: '{cloze_text}'"),
        type=models.QuestionType.multiple_choice,
        competency_tag="comprehension",
        difficulty_level=4,
        points=4,
        prompt_audio_text=None,
        prompt_translation=None,
        target_word=target_milk_ans,
        interface_translation=get_concept_word("milk", pref_lang_code),
        answers=q14_answers
    ))

    # ----------------------------------------------------
    # Q15: Thank-You Vocabulary Test (Difficulty 5)
    # ----------------------------------------------------
    target_thank_you = get_concept_word("thank_you", target_lang_code)
    pref_thank_you = get_concept_word("thank_you", pref_lang_code)
    q15_prompts = {
        "kn": f"'{pref_thank_you}' ಎಂಬ ಅರ್ಥವನ್ನು ನೀಡುವ ಕನ್ನಡ ಪದ ಯಾವುದು?",
        "te": f"'{pref_thank_you}' అనే అర్థం ఇచ్చే తెలుగు పదం ఏది?",
        "hi": f"'{pref_thank_you}' अर्थ वाला हिन्दी शब्द कौन सा है?",
        "mr": f"'{pref_thank_you}' अर्थ असणारा मराठी शब्द कोणता?",
        "en": f"Which English phrase means '{pref_thank_you}'?"
    }
    q15_answers = [
        schemas.AdaptiveQuestionAnswer(
            id=str(uuid.uuid4()),
            text=target_thank_you,
            is_correct=True,
            explanation=f"Correct! '{target_thank_you}' means '{pref_thank_you}'."
        ),
        schemas.AdaptiveQuestionAnswer(id=str(uuid.uuid4()), text=get_concept_word("hello", target_lang_code), is_correct=False),
        schemas.AdaptiveQuestionAnswer(id=str(uuid.uuid4()), text=get_concept_word("friend", target_lang_code), is_correct=False),
        schemas.AdaptiveQuestionAnswer(id=str(uuid.uuid4()), text=get_concept_word("good morning", target_lang_code), is_correct=False)
    ]
    random.shuffle(q15_answers)

    questions.append(schemas.PlacementTestQuestion(
        id=str(uuid.uuid4()),
        text=q15_prompts.get(target_lang_code, f"Which word means '{pref_thank_you}'?"),
        type=models.QuestionType.multiple_choice,
        competency_tag="vocabulary",
        difficulty_level=5,
        points=5,
        prompt_audio_text=None,
        prompt_translation=None,
        target_word=target_thank_you,
        interface_translation=pref_thank_you,
        answers=q15_answers
    ))

    return schemas.PlacementTestSessionResponse(
        session_id=session_id,
        target_language_name=target_lang_name,
        target_language_code=target_lang_code,
        preferred_language_name=pref_lang_name,
        preferred_language_code=pref_lang_code,
        total_questions=len(questions),
        questions=questions
    )


def evaluate_placement_test(
    learner_id: uuid.UUID,
    submit_data: schemas.PlacementTestSubmit,
    db: Session
) -> schemas.PlacementTestResultResponse:
    """
    Evaluates the Initial Exam submissions, calculates difficulty-weighted score,
    calibrates CEFR proficiency level (A0-C2), computes multi-skill breakdown
    (vocabulary, grammar, reading, listening, writing, speaking), detects strengths
    and weak areas, auto-unlocks tested-out prerequisite modules, and returns
    tailored NeoLearner course path recommendations.
    """
    import json
    learner = db.query(models.Learner).filter(models.Learner.id == learner_id).first()
    if not learner:
        raise ValueError("Learner not found")

    total_weight = sum(s.difficulty_level for s in submit_data.submissions)
    earned_weight = sum(s.difficulty_level for s in submit_data.submissions if s.is_correct)
    
    score_pct = round((earned_weight / total_weight * 100.0), 1) if total_weight > 0 else 50.0

    # 1. CEFR Level & Benchmark Calibration
    if score_pct >= 95.0:
        cefr_code = "C2"
        benchmark = "Proficient Master (C2)"
        calibrated_level = models.ProficiencyLevel.Advanced
        recommended_course_level = models.CourseLevel.Advanced
        path_title = "Advanced Fluency & Native Immersion (C2)"
        path_desc = f"Initial Exam Score: {score_pct}%. You demonstrated near-native mastery across all core competencies."
        msg = f"Outstanding mastery! Scoring {score_pct}% places you at CEFR C2 ({benchmark}). All prerequisite modules are unlocked!"
    elif score_pct >= 85.0:
        cefr_code = "C1"
        benchmark = "Advanced Fluency (C1)"
        calibrated_level = models.ProficiencyLevel.Advanced
        recommended_course_level = models.CourseLevel.Advanced
        path_title = "Advanced Literacy & Discourse Track (C1)"
        path_desc = f"Initial Exam Score: {score_pct}%. Recommended path focuses on advanced idioms, nuanced grammar, and extended comprehension."
        msg = f"Impressive performance! Scoring {score_pct}% places you at CEFR C1 ({benchmark}). Prerequisite modules are unlocked!"
    elif score_pct >= 75.0:
        cefr_code = "B2"
        benchmark = "Upper Intermediate (B2)"
        calibrated_level = models.ProficiencyLevel.Intermediate
        recommended_course_level = models.CourseLevel.Intermediate
        path_title = "Upper Conversational Fluency Track (B2)"
        path_desc = f"Initial Exam Score: {score_pct}%. Solid foundation across grammar and vocabulary. Ready for complex dialogues."
        msg = f"Great work! Scoring {score_pct}% places you at CEFR B2 ({benchmark}). Foundational units are unlocked!"
    elif score_pct >= 60.0:
        cefr_code = "B1"
        benchmark = "Intermediate (B1)"
        calibrated_level = models.ProficiencyLevel.Intermediate
        recommended_course_level = models.CourseLevel.Intermediate
        path_title = "Conversational Literacy Track (B1)"
        path_desc = f"Initial Exam Score: {score_pct}%. Ready for real-life conversations, past tense, and situational dialogues."
        msg = f"Well done! Scoring {score_pct}% places you at CEFR B1 ({benchmark}). Beginner units are unlocked!"
    elif score_pct >= 45.0:
        cefr_code = "A2"
        benchmark = "Elementary (A2)"
        calibrated_level = models.ProficiencyLevel.Beginner
        recommended_course_level = models.CourseLevel.Beginner
        path_title = "Elementary Foundations & Daily Life (A2)"
        path_desc = f"Initial Exam Score: {score_pct}%. Focuses on common expressions, simple sentence structure, and core daily vocabulary."
        msg = f"Good start! Scoring {score_pct}% places you at CEFR A2 ({benchmark}). Let's strengthen your foundation!"
    elif score_pct >= 25.0:
        cefr_code = "A1"
        benchmark = "Beginner (A1)"
        calibrated_level = models.ProficiencyLevel.Beginner
        recommended_course_level = models.CourseLevel.Beginner
        path_title = "Foundational Literacy Track (A1)"
        path_desc = f"Initial Exam Score: {score_pct}%. Focuses on alphabet phonics, basic greetings, and introductory words."
        msg = f"Initial Exam Complete! You've been placed at CEFR A1 ({benchmark}) with a score of {score_pct}%."
    else:
        cefr_code = "A0"
        benchmark = "Absolute Beginner (A0)"
        calibrated_level = models.ProficiencyLevel.Beginner
        recommended_course_level = models.CourseLevel.Beginner
        path_title = "Emergent Phonics & Primer Track (A0)"
        path_desc = f"Initial Exam Score: {score_pct}%. Step-by-step introduction to letter sounds, pronunciation, and basic vocabulary."
        msg = f"Welcome to NeoLearner! You've been placed at CEFR A0 ({benchmark}). We will guide you step by step from the basics."

    # 2. Multi-Skill Breakdown Computation (6 core skill competencies)
    competency_map = {
        0: "reading",      # Q1: Phonics & Vowel sounds
        1: "vocabulary",   # Q2: Salutation / Greeting
        2: "reading",      # Q3: Phonics & Character recognition
        3: "grammar",      # Q4: Subject-Verb Agreement
        4: "vocabulary",   # Q5: Food & Beverage
        5: "listening",    # Q6: Auditory Identification
        6: "grammar",      # Q7: Pluralization & Syntax
        7: "vocabulary",   # Q8: Colors & Nature
        8: "listening",    # Q9: Audio Sentence Comprehension
        9: "grammar",      # Q10: Tense Conjugation
        10: "vocabulary",  # Q11: Rapid Paired Vocabulary
        11: "writing",     # Q12: Cross-Language Translation
        12: "reading",     # Q13: Complex Sentence Reading
        13: "writing",     # Q14: Cloze Contextual Sentence
        14: "speaking"     # Q15: Voice Pronunciation
    }

    skill_counts = {
        "vocabulary": [0, 0],
        "grammar": [0, 0],
        "reading": [0, 0],
        "listening": [0, 0],
        "writing": [0, 0],
        "speaking": [0, 0]
    }
    for idx, s in enumerate(submit_data.submissions):
        comp = competency_map.get(idx, "vocabulary")
        skill_counts[comp][1] += s.difficulty_level
        if s.is_correct:
            skill_counts[comp][0] += s.difficulty_level

    skill_breakdown = {}
    for k, (earned, tot) in skill_counts.items():
        if tot > 0:
            skill_breakdown[k] = round((earned / tot * 100.0), 1)
        else:
            skill_breakdown[k] = score_pct

    # Determine Strengths & Weak Areas
    sorted_skills = sorted(skill_breakdown.items(), key=lambda x: x[1], reverse=True)
    strengths = [s[0].capitalize() for s in sorted_skills if s[1] >= 60.0]
    if not strengths:
        strengths = [sorted_skills[0][0].capitalize()]

    weak_areas = [s[0].capitalize() for s in sorted_skills if s[1] < 60.0]
    if not weak_areas:
        weak_areas = [sorted_skills[-1][0].capitalize()]

    recommended_focus = f"Focus on {', '.join(weak_areas[:2])} drills to level up your mastery."

    # Query matching course for target language and calibrated level using recommendation engine
    from recommendation_engine import default_recommendation_engine
    course_recs = default_recommendation_engine.rank_courses_for_learner(learner, db)
    target_course = None
    if course_recs.primary_recommendation and course_recs.primary_recommendation.course_id:
        target_course = db.query(models.Course).filter(
            models.Course.id == course_recs.primary_recommendation.course_id,
            models.Course.is_published == True
        ).first()

    if not target_course and learner.target_language_id:
        target_course = db.query(models.Course).filter(
            models.Course.language_id == learner.target_language_id,
            models.Course.level == recommended_course_level,
            models.Course.is_published == True
        ).first()
    if not target_course:
        target_course = db.query(models.Course).filter(
            models.Course.is_published == True
        ).first()

    # Initial Placement Test is diagnostic: Calibrates learner level & starting unit recommendations.
    # Lessons and assessments remain uncompleted for the learner to actually study.
    tested_out_nodes_count = 0

    # Unconditionally record overall Diagnostic AssessmentResult
    diag_record = models.AssessmentResult(
        learner_id=learner_id,
        assessment_id=None,
        score=score_pct,
        max_score=100.0,
        passed=True,
        completed_at=datetime.utcnow(),
        cefr_level=cefr_code,
        skill_breakdown=json.dumps(skill_breakdown),
        strengths=json.dumps(strengths),
        weak_areas=json.dumps(weak_areas)
    )
    db.add(diag_record)

    # Update Learner Profile with CEFR and score diagnostics
    learner.has_completed_placement_test = True
    learner.placement_score = score_pct
    learner.proficiency_level = calibrated_level
    learner.predicted_proficiency_score = score_pct
    learner.benchmark_level = benchmark
    learner.cefr_level = cefr_code

    # Award placement rewards
    xp_bonus = 60 if score_pct >= 80 else (40 if score_pct >= 50 else 25)
    gems_bonus = 30 if score_pct >= 80 else (20 if score_pct >= 50 else 15)
    gamification.award_xp_and_gems(learner, xp_bonus, gems_bonus, db)
    gamification.update_streak(learner, db)

    db.commit()
    db.refresh(learner)

    # Generate tailored recommendations
    recs = generate_ai_recommendations(learner_id, db)
    course_title = target_course.title if target_course else "Foundational Literacy"

    if target_course:
        recs.insert(0, schemas.AIRecommendationItem(
            id=f"rec-course-{target_course.id}",
            title=f"Start {target_course.title}",
            reason=f"Recommended for your {cefr_code} ({benchmark}) placement.",
            type="recommended_course",
            action_url=f"/courses/{target_course.id}",
            priority=0,
            confidence=1.0,
            competency_tag="course"
        ))

    # Add targeted weak-skill practice recommendations
    for weak_skill in weak_areas[:2]:
        tag = weak_skill.lower()
        recs.append(schemas.AIRecommendationItem(
            id=f"rec-weak-{tag}",
            title=f"AI Adaptive: {weak_skill} Studio",
            reason=f"Targeted booster to raise your {weak_skill} mastery (current score: {skill_breakdown.get(tag, 50)}%).",
            type="challenge",
            action_url=f"/adaptive-practice?focus={tag}",
            priority=len(recs) + 1,
            confidence=0.92,
            competency_tag=tag
        ))

    course_recs = default_recommendation_engine.rank_courses_for_learner(learner, db)

    return schemas.PlacementTestResultResponse(
        placement_score=score_pct,
        calibrated_level=calibrated_level,
        benchmark_level=benchmark,
        cefr_level=cefr_code,
        skill_breakdown=skill_breakdown,
        strengths=strengths,
        weak_areas=weak_areas,
        recommended_focus=recommended_focus,
        tested_out_nodes_count=tested_out_nodes_count,
        xp_earned=xp_bonus,
        gems_earned=gems_bonus,
        message=msg,
        recommended_path_title=path_title,
        recommended_path_description=path_desc,
        recommended_course_title=course_title,
        recommended_course_id=target_course.id if target_course else None,
        recommendations=recs,
        course_recommendations=course_recs
    )

