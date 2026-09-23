from datetime import datetime
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas, models, database, dependencies, gamification

router = APIRouter(prefix="/api/practice-hub", tags=["practice_hub"])

@router.get("/overview", response_model=schemas.PracticeHubOverviewResponse)
def get_practice_hub_overview(
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    gamification.recharge_hearts_by_time(current_learner, db)

    now = datetime.utcnow()

    # 1. Due SRS vocabulary count
    due_srs_count = db.query(models.VocabularySRS).filter(
        models.VocabularySRS.learner_id == current_learner.id,
        models.VocabularySRS.next_review_date <= now
    ).count()

    # 2. Unresolved mistakes count
    mistakes_count = db.query(models.ReviewItem).filter(
        models.ReviewItem.learner_id == current_learner.id,
        models.ReviewItem.is_resolved == False
    ).count()

    # 3. Total Flashcards in target language
    target_lang_id = current_learner.target_language_id
    flashcards_deck_size = 0
    if target_lang_id:
        flashcards_deck_size = db.query(models.Vocabulary).filter(
            models.Vocabulary.language_id == target_lang_id
        ).count()
    if flashcards_deck_size == 0:
        flashcards_deck_size = 20

    # 4. Weak Competencies calculation from recent assessments
    results = db.query(models.AssessmentResult).filter(
        models.AssessmentResult.learner_id == current_learner.id
    ).all()

    scores_by_tag = {
        "speaking": [75.0],
        "listening": [80.0],
        "writing": [70.0],
        "reading": [85.0]
    }
    for r in results:
        if r.assessment and r.assessment.questions:
            for q in r.assessment.questions:
                tag = (q.competency_tag or "reading").lower()
                if tag in scores_by_tag:
                    scores_by_tag[tag].append(r.score)

    weak_list = []
    for skill, scores in scores_by_tag.items():
        avg = sum(scores) / len(scores)
        if avg < 80.0:
            weak_list.append({
                "skill": skill.capitalize(),
                "score": round(avg, 1),
                "action": f"Practice {skill.capitalize()}"
            })

    # 5. Active Boost Check
    active_boost = db.query(models.LearnerBoost).filter(
        models.LearnerBoost.learner_id == current_learner.id,
        models.LearnerBoost.is_active == True,
        models.LearnerBoost.expires_at > now
    ).first()

    boost_data = None
    if active_boost:
        remaining_secs = int((active_boost.expires_at - now).total_seconds())
        boost_data = {
            "boost_type": active_boost.boost_type,
            "multiplier": active_boost.multiplier,
            "remaining_seconds": max(0, remaining_secs)
        }

    # 6. Assemble 12 targeted workout modes
    modes = [
        schemas.PracticeModeInfo(
            id="hearts",
            title="Restore Hearts",
            desc="Complete a short practice session to refill 1 heart for free and earn bonus XP.",
            icon="❤️",
            badge="FREE REFILL" if current_learner.hearts < 5 else "FULL",
            count=current_learner.hearts,
            route="/practice"
        ),
        schemas.PracticeModeInfo(
            id="mistakes",
            title="Mistakes Queue",
            desc="Review and correct all questions previously answered incorrectly.",
            icon="❌",
            badge="URGENT" if mistakes_count > 0 else None,
            count=mistakes_count,
            route="/review/mistakes"
        ),
        schemas.PracticeModeInfo(
            id="srs",
            title="Spaced Repetition (SRS)",
            desc="Review due vocabulary scheduled by the SuperMemo-2 cognitive memory algorithm.",
            icon="🔄",
            badge=f"{due_srs_count} DUE" if due_srs_count > 0 else "CAUGHT UP",
            count=due_srs_count,
            route="/review/srs"
        ),
        schemas.PracticeModeInfo(
            id="flashcards",
            title="Visual 3D Flashcards",
            desc="Interactive 3D flip-card deck to quickly memorize vocabulary and phrases.",
            icon="🃏",
            badge=f"{flashcards_deck_size} CARDS",
            count=flashcards_deck_size,
            route="/flashcards"
        ),
        schemas.PracticeModeInfo(
            id="speaking",
            title="Speaking Lab",
            desc="Voice recording and speech recognition lab focusing on accurate pronunciation.",
            icon="🎤",
            badge="VOICE AI",
            route="/adaptive-practice?focus=speaking"
        ),
        schemas.PracticeModeInfo(
            id="listening",
            title="Listening Studio",
            desc="Acoustic phonetics and auditory comprehension challenges.",
            icon="🎧",
            badge="AUDIO",
            route="/adaptive-practice?focus=listening"
        ),
        schemas.PracticeModeInfo(
            id="writing",
            title="Writing & Spelling",
            desc="Fill-in-the-blank, missing letter decoding, and sentence construction.",
            icon="✍️",
            badge="SPELLING",
            route="/adaptive-practice?focus=writing"
        ),
        schemas.PracticeModeInfo(
            id="matching",
            title="Speed Matching",
            desc="Fast-paced association of words with their corresponding native meanings.",
            icon="⚡",
            badge="RAPID FIRE",
            route="/adaptive-practice?focus=match_pairs"
        ),
        schemas.PracticeModeInfo(
            id="conversation",
            title="AI Conversation Lab",
            desc="Open-ended dialogue with your virtual native-language tutor in real-world scenarios.",
            icon="💬",
            badge="AI MAX",
            route="/conversation"
        ),
        schemas.PracticeModeInfo(
            id="stories",
            title="NeoStories",
            desc="Engaging narrative stories with character dialogues and inline comprehension.",
            icon="📖",
            badge="STORIES",
            route="/stories"
        ),
        schemas.PracticeModeInfo(
            id="adventures",
            title="NeoAdventures",
            desc="Immersive branching real-world quests (Airport, Market, Hospital, Hotel).",
            icon="🌎",
            badge="ADVENTURES",
            route="/adventures"
        ),
        schemas.PracticeModeInfo(
            id="smart_adaptive",
            title="Smart AI Workout",
            desc="Holistic multi-skill workout targeted dynamically at your lowest proficiency vectors.",
            icon="🎯",
            badge="RECOMMENDED",
            route="/adaptive-practice"
        )
    ]

    return schemas.PracticeHubOverviewResponse(
        hearts_restore_available=current_learner.hearts < 5,
        current_hearts=current_learner.hearts,
        due_srs_count=due_srs_count,
        mistakes_count=mistakes_count,
        flashcards_deck_size=flashcards_deck_size,
        weak_competencies=weak_list,
        active_boost=boost_data,
        modes=modes
    )
