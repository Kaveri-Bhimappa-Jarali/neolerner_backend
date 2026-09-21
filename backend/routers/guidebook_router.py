import uuid
import json
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import schemas, models, database, dependencies, gamification

router = APIRouter(prefix="/api/guidebooks", tags=["guidebooks_mastery"])

@router.get("/topic/{topic_id}", response_model=schemas.UnitGuidebookResponse)
def get_unit_guidebook(
    topic_id: UUID,
    db: Session = Depends(database.get_db)
):
    topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    guidebook = db.query(models.UnitGuidebook).filter(models.UnitGuidebook.topic_id == topic_id).first()
    if not guidebook:
        # Generate rich contextual guidebook
        lang_code = topic.course.language.code if topic.course and topic.course.language else "kn"
        
        if lang_code == "kn":
            phrases = [
                {"phrase": "ನಮಸ್ಕಾರ (Namaskara)", "meaning": "Hello / Greetings", "audio_cue": "Formal respectful greeting"},
                {"phrase": "ಧನ್ಯವಾದಗಳು (Dhanyavaadagalu)", "meaning": "Thank you", "audio_cue": "Expressing gratitude"},
                {"phrase": "ಹೇಗಿದ್ದೀರಾ? (Hegiddeera?)", "meaning": "How are you?", "audio_cue": "Polite inquiry"},
                {"phrase": "ನಾನು ಚೆನ್ನಾಗಿದ್ದೇನೆ (Naanu chennaagiddene)", "meaning": "I am doing well", "audio_cue": "Standard affirmative reply"}
            ]
            notes = (
                f"### 📖 Unit Grammar Guide: {topic.title}\n\n"
                "**1. Sentence Word Order (SOV):**\n"
                "Kannada follows the **Subject-Object-Verb (SOV)** structure, unlike English (SVO).\n"
                "- English: *I (S) drink (V) milk (O).*\n"
                "- Kannada: *ನಾನು (S) ಹಾಲು (O) ಕುಡಿಯುತ್ತೇನೆ (V).*\n\n"
                "**2. Respectful Addressing:**\n"
                "Always use **ನೀವು (Neevu)** when addressing elders, teachers, or strangers respectfully. Use **ನೀನು (Neenu)** only with close friends or children."
            )
            mistakes = (
                "- Confusing soft **ಲ (La)** with retroflex **ಳ (Lha)**.\n"
                "- Omitting the polite plural suffix **-ರಿ (-ri)** when addressing elders."
            )
            culture = "In Karnataka, greeting someone with folded hands and saying *Namaskara* shows deep cultural reverence and warmth."
        elif lang_code == "te":
            phrases = [
                {"phrase": "నమస్కారం (Namaskaram)", "meaning": "Hello", "audio_cue": "Respectful greeting"},
                {"phrase": "ధన్యవాదాలు (Dhanyavaadaalu)", "meaning": "Thank you", "audio_cue": "Gratitude"},
                {"phrase": "ఎలా ఉన్నారు? (Elaa unnaaru?)", "meaning": "How are you?", "audio_cue": "Polite question"}
            ]
            notes = f"### 📖 Unit Grammar Guide: {topic.title}\n\nTelugu follows **Subject-Object-Verb** order. Words typically end in vowels (Italian of the East)."
            mistakes = "Confusing short vowels like 'అ' with elongated 'ఆ'."
            culture = "Telugu culture emphasizes polite prefixes and respectful verb conjugations for guests and family elders."
        elif lang_code == "mr":
            phrases = [
                {"phrase": "नमस्कार (Namaskar)", "meaning": "Hello", "audio_cue": "Respectful greeting"},
                {"phrase": "धन्यवाद (Dhanyavaad)", "meaning": "Thank you", "audio_cue": "Gratitude"}
            ]
            notes = f"### 📖 Unit Grammar Guide: {topic.title}\n\nMarathi sentences are built on **Subject-Object-Verb** structure with gender-concordant verbs."
            mistakes = "Mismatching verb endings with grammatical gender."
            culture = "Greeting with *Namaskar* or *Jai Maharashtra* is standard in daily social interactions."
        elif lang_code == "hi":
            phrases = [
                {"phrase": "नमस्ते (Namaste)", "meaning": "Hello", "audio_cue": "Universal greeting"},
                {"phrase": "धन्यवाद (Dhanyavaad)", "meaning": "Thank you", "audio_cue": "Gratitude"}
            ]
            notes = f"### 📖 Unit Grammar Guide: {topic.title}\n\nHindi uses the **SOV (Subject-Object-Verb)** word order. Gender agreement is crucial for verbs."
            mistakes = "Confusing masculine vs feminine verb endings (-ता है vs -ती है)."
            culture = "Folded hands (*Namaste*) is the hallmark of respectful greeting across Northern and Central India."
        else:
            phrases = [
                {"phrase": "Good morning", "meaning": "Early day greeting", "audio_cue": "Polite greeting"},
                {"phrase": "Thank you so much", "meaning": "Expressing gratitude", "audio_cue": "Polite response"}
            ]
            notes = f"### 📖 Unit Grammar Guide: {topic.title}\n\nEnglish follows **Subject-Verb-Object (SVO)** structure."
            mistakes = "Subject-verb agreement errors."
            culture = "Polite words like 'please', 'thank you', and 'excuse me' are foundational to courteous conversation."

        guidebook = models.UnitGuidebook(
            topic_id=topic.id,
            title=f"Guidebook: {topic.title}",
            grammar_notes_md=notes,
            key_phrases_json=json.dumps(phrases),
            common_mistakes_md=mistakes,
            cultural_tips_md=culture
        )
        db.add(guidebook)
        db.commit()
        db.refresh(guidebook)

    phrases_list = json.loads(guidebook.key_phrases_json) if guidebook.key_phrases_json else []

    return schemas.UnitGuidebookResponse(
        id=guidebook.id,
        topic_id=guidebook.topic_id,
        title=guidebook.title,
        grammar_notes_md=guidebook.grammar_notes_md,
        key_phrases=phrases_list,
        common_mistakes_md=guidebook.common_mistakes_md,
        cultural_tips_md=guidebook.cultural_tips_md
    )

@router.get("/mastery/{topic_id}", response_model=schemas.TopicMasteryResponse)
def get_topic_mastery(
    topic_id: UUID,
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    mastery = db.query(models.TopicMastery).filter(
        models.TopicMastery.learner_id == current_learner.id,
        models.TopicMastery.topic_id == topic_id
    ).first()

    if not mastery:
        # Check if user has completed lessons in this topic
        topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
        if topic and topic.lessons:
            lesson_ids = [l.id for l in topic.lessons]
            completed_count = db.query(models.LearningProgress).filter(
                models.LearningProgress.learner_id == current_learner.id,
                models.LearningProgress.lesson_id.in_(lesson_ids),
                models.LearningProgress.status == models.ProgressStatus.completed
            ).count()

            level = models.UnitMasteryLevel.not_started
            if completed_count == len(lesson_ids) and len(lesson_ids) > 0:
                level = models.UnitMasteryLevel.mastered
            elif completed_count > 0:
                level = models.UnitMasteryLevel.learning

            mastery = models.TopicMastery(
                learner_id=current_learner.id,
                topic_id=topic_id,
                level=level,
                legendary_passed=False,
                score=100.0 if level == models.UnitMasteryLevel.mastered else 50.0
            )
            db.add(mastery)
            db.commit()
            db.refresh(mastery)
        else:
            return schemas.TopicMasteryResponse(
                topic_id=topic_id,
                level=models.UnitMasteryLevel.not_started,
                legendary_passed=False,
                score=0.0
            )

    return schemas.TopicMasteryResponse(
        topic_id=mastery.topic_id,
        level=mastery.level,
        legendary_passed=mastery.legendary_passed,
        score=mastery.score
    )

@router.post("/test-out/{topic_id}", response_model=schemas.TopicTestOutResponse)
def test_out_topic(
    topic_id: UUID,
    submit: schemas.TopicTestOutSubmit,
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # In our adaptive engine, test-out requires scoring >= 80%
    correct_count = sum(1 for a in submit.answers if a.get("is_correct"))
    total_q = max(1, len(submit.answers))
    score = (correct_count / total_q) * 100.0
    passed = score >= 80.0

    if passed:
        # Mark all lessons in this topic as completed!
        unlocked_ids = []
        for l in topic.lessons:
            prog = db.query(models.LearningProgress).filter(
                models.LearningProgress.learner_id == current_learner.id,
                models.LearningProgress.lesson_id == l.id
            ).first()
            if not prog:
                prog = models.LearningProgress(
                    learner_id=current_learner.id,
                    lesson_id=l.id,
                    status=models.ProgressStatus.completed,
                    percentage_completed=100.0
                )
                db.add(prog)
            else:
                prog.status = models.ProgressStatus.completed
                prog.percentage_completed = 100.0
            unlocked_ids.append(l.id)

        # Update mastery
        mastery = db.query(models.TopicMastery).filter(
            models.TopicMastery.learner_id == current_learner.id,
            models.TopicMastery.topic_id == topic_id
        ).first()
        if not mastery:
            mastery = models.TopicMastery(
                learner_id=current_learner.id,
                topic_id=topic_id,
                level=models.UnitMasteryLevel.mastered,
                legendary_passed=False,
                score=score
            )
            db.add(mastery)
        else:
            mastery.level = models.UnitMasteryLevel.mastered
            mastery.score = max(mastery.score, score)

        gamification.award_xp_and_gems(current_learner, xp=50, gems=25, db=db)
        gamification.update_streak(current_learner, db=db)
        db.commit()

        return schemas.TopicTestOutResponse(
            topic_id=topic_id,
            score=score,
            passed=True,
            new_mastery_level=models.UnitMasteryLevel.mastered,
            xp_earned=50,
            message="🎉 Congratulations! You passed the unit test-out and unlocked all lessons in this unit!"
        )
    else:
        return schemas.TopicTestOutResponse(
            topic_id=topic_id,
            score=score,
            passed=False,
            new_mastery_level=models.UnitMasteryLevel.learning,
            xp_earned=10,
            message="You scored below 80%. Complete the bite-sized lessons to build your foundational knowledge!"
        )

@router.post("/legendary/{topic_id}")
def earn_legendary_status(
    topic_id: UUID,
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    mastery = db.query(models.TopicMastery).filter(
        models.TopicMastery.learner_id == current_learner.id,
        models.TopicMastery.topic_id == topic_id
    ).first()

    if not mastery:
        mastery = models.TopicMastery(
            learner_id=current_learner.id,
            topic_id=topic_id,
            level=models.UnitMasteryLevel.legendary,
            legendary_passed=True,
            score=100.0
        )
        db.add(mastery)
    else:
        mastery.level = models.UnitMasteryLevel.legendary
        mastery.legendary_passed = True

    gamification.award_xp_and_gems(current_learner, xp=40, gems=20, db=db)
    db.commit()

    return {"message": "👑 Legendary Crown unlocked! You have achieved mastery in this unit.", "level": "legendary"}
