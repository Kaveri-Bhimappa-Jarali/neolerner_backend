import re
import uuid
import json
from datetime import datetime
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
import models, schemas, gamification

def clean_text(text: str) -> List[str]:
    """Normalizes text by removing punctuation and lowercasing."""
    if not text:
        return []
    cleaned = re.sub(r'[^\w\s]', '', text.lower())
    return [w for w in cleaned.split() if w]

def levenshtein_distance(s1: str, s2: str) -> int:
    """Computes Levenshtein edit distance between two words."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def calculate_word_similarity(w1: str, w2: str) -> float:
    """Returns 0.0 - 1.0 similarity score between two words."""
    if w1 == w2:
        return 1.0
    dist = levenshtein_distance(w1, w2)
    max_len = max(len(w1), len(w2))
    if max_len == 0:
        return 1.0
    return max(0.0, 1.0 - (dist / max_len))

def assess_pronunciation(
    target_text: str,
    spoken_text: str,
    language_code: str = "en"
) -> Dict[str, Any]:
    """
    Pronunciation Assessment Algorithm:
    Converts target and spoken text to token streams, computes word-level edit distance,
    identifies mispronounced/omitted words, calculates accuracy & fluency scores,
    and returns actionable feedback.
    """
    target_words = clean_text(target_text)
    spoken_words = clean_text(spoken_text)

    if not target_words:
        return {
            "overall_score": 100.0,
            "accuracy_score": 100.0,
            "fluency_score": 100.0,
            "problematic_words": [],
            "feedback": "Perfect pronunciation!"
        }

    if not spoken_words:
        return {
            "overall_score": 0.0,
            "accuracy_score": 0.0,
            "fluency_score": 0.0,
            "problematic_words": target_words,
            "feedback": "No speech detected. Please speak loudly into the microphone."
        }

    # Match target words against spoken words
    word_scores: List[float] = []
    problematic_words: List[str] = []

    for t_word in target_words:
        best_match_score = 0.0
        for s_word in spoken_words:
            sim = calculate_word_similarity(t_word, s_word)
            if sim > best_match_score:
                best_match_score = sim

        word_scores.append(best_match_score)
        if best_match_score < 0.70:
            problematic_words.append(t_word)

    accuracy_score = round((sum(word_scores) / len(word_scores)) * 100.0, 1)

    # Fluency estimate based on length ratio & completeness
    length_ratio = min(1.0, len(spoken_words) / len(target_words))
    fluency_score = round(accuracy_score * (0.8 + 0.2 * length_ratio), 1)

    overall_score = round((accuracy_score * 0.7) + (fluency_score * 0.3), 1)

    # Generate feedback
    if overall_score >= 90:
        feedback = "Outstanding pronunciation! Excellent clarity and native fluency."
    elif overall_score >= 75:
        feedback = f"Good effort! Focus on practicing: {', '.join(problematic_words)}" if problematic_words else "Good pronunciation with clear articulation."
    elif overall_score >= 50:
        feedback = f"Passable pronunciation. Pay close attention to: {', '.join(problematic_words)}"
    else:
        feedback = f"Needs practice. Try speaking slower and emphasize sounds in: {', '.join(problematic_words or target_words[:3])}"

    return {
        "overall_score": overall_score,
        "accuracy_score": accuracy_score,
        "fluency_score": fluency_score,
        "problematic_words": problematic_words,
        "feedback": feedback
    }

def process_and_save_pronunciation(
    learner_id: uuid.UUID,
    req: schemas.PronunciationAssessmentRequest,
    db: Session
) -> schemas.PronunciationAssessmentResponse:
    """Evaluates speech, saves record, updates speaking competency, and awards XP."""
    eval_res = assess_pronunciation(req.target_text, req.spoken_text, req.language_code or "en")

    attempt = models.PronunciationAttempt(
        id=uuid.uuid4(),
        learner_id=learner_id,
        target_text=req.target_text,
        spoken_text=req.spoken_text,
        audio_url=req.audio_url,
        overall_score=eval_res["overall_score"],
        accuracy_score=eval_res["accuracy_score"],
        fluency_score=eval_res["fluency_score"],
        problematic_words_json=json.dumps(eval_res["problematic_words"]),
        feedback=eval_res["feedback"],
        language_code=req.language_code or "en",
        created_at=datetime.utcnow()
    )

    db.add(attempt)

    # Update Learner speaking competency score
    learner = db.query(models.Learner).filter(models.Learner.id == learner_id).first()
    if learner:
        xp_earned = 15 if eval_res["overall_score"] >= 60 else 5
        gamification.award_xp_and_gems(learner, xp_earned, 5, db)

    db.commit()
    db.refresh(attempt)

    return schemas.PronunciationAssessmentResponse(
        id=attempt.id,
        target_text=attempt.target_text,
        spoken_text=attempt.spoken_text,
        overall_score=attempt.overall_score,
        accuracy_score=attempt.accuracy_score,
        fluency_score=attempt.fluency_score,
        problematic_words=eval_res["problematic_words"],
        feedback=attempt.feedback,
        xp_earned=15 if attempt.overall_score >= 60 else 5,
        current_speaking_score=attempt.overall_score,
        created_at=attempt.created_at
    )
