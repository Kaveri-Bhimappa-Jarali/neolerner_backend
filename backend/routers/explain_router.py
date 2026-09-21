from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas, models, database, dependencies

router = APIRouter(prefix="/api/ai", tags=["ai_explainer"])

@router.post("/explain-mistake", response_model=schemas.ExplainMistakeResponse)
def explain_mistake(
    req: schemas.ExplainMistakeRequest,
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    q_text = req.question_text or "Question"
    user_choice = req.user_answer_text or "Your selected answer"
    correct_choice = req.correct_answer_text or "Correct answer"

    if req.question_id:
        question = db.query(models.Question).filter(models.Question.id == req.question_id).first()
        if question:
            q_text = question.text
            correct_ans = next((a for a in question.answers if a.is_correct), None)
            if correct_ans:
                correct_choice = correct_ans.text

            if req.selected_answer_id:
                user_ans = db.query(models.Answer).filter(models.Answer.id == req.selected_answer_id).first()
                if user_ans:
                    user_choice = user_ans.text
                    if user_ans.explanation:
                        why_inc = user_ans.explanation

    # Target language identification
    lang_code = current_learner.target_language.code if current_learner.target_language else "kn"

    # Contextual explanation generation
    if lang_code == "kn":
        why_incorrect = (
            f"You selected '{user_choice}', which does not match the grammatical role or semantic meaning required by '{q_text}'. "
            f"In Kannada, sentence endings, tense markers, and case suffixes (ವಿಭಕ್ತಿ ಪ್ರತ್ಯಯಗಳು) must align strictly with the subject."
        )
        grammar_rule = (
            "Rule: Subject-Object-Verb (SOV) agreement. When forming verbs in Kannada, masculine singular takes -ಆನೆ (-aane), "
            "feminine singular takes -ಆಳೆ (-aale), and polite/plural forms take -ಆರೆ (-aare)."
        )
        contrast_examples = [
            f"❌ '{user_choice}' — Incorrect grammatical concord in this context.",
            f"✅ '{correct_choice}' — Correct concord matching gender, number, and respect."
        ]
        memory_tip = "💡 Memory Tip: Look at the last syllable of the word. Polite forms almost always end with soft 'ರಿ' or 'ರೆ'."
    elif lang_code == "te":
        why_incorrect = (
            f"You selected '{user_choice}', whereas the context specifically demands '{correct_choice}'. "
            "In Telugu, vowel harmony and gender concord dictate the verb suffix."
        )
        grammar_rule = "Rule: Telugu nouns and verbs must agree in gender (Mahat vs. A-mahat) and number."
        contrast_examples = [
            f"❌ '{user_choice}' — Clashes with the subject pronoun.",
            f"✅ '{correct_choice}' — Harmonizes perfectly with the sentence predicate."
        ]
        memory_tip = "💡 Memory Tip: Plural polite verbs in Telugu consistently end in '-రు' (-ru)."
    elif lang_code == "mr":
        why_incorrect = (
            f"You selected '{user_choice}'. In Marathi, verb conjugations reflect grammatical gender (पुल्लिंग, स्त्रीलिंग, नपुंसकलिंग)."
        )
        grammar_rule = "Rule: Neuter and feminine agreement rules require specific inflectional endings."
        contrast_examples = [
            f"❌ '{user_choice}' — Gender mismatch with the noun.",
            f"✅ '{correct_choice}' — Correct grammatical agreement."
        ]
        memory_tip = "💡 Memory Tip: Marathi third-person plural polite verbs end in '-तात' (-taat)."
    elif lang_code == "hi":
        why_incorrect = (
            f"You selected '{user_choice}', but the sentence grammar requires '{correct_choice}'. "
            "In Hindi, tense and aspect markers must strictly agree with the subject's gender and honorific level."
        )
        grammar_rule = "Rule: Habitual aspect uses -ता है / -ती है / -ते हैं depending on gender and honorific status (आप)."
        contrast_examples = [
            f"❌ '{user_choice}' — Incompatible with the subject gender/tense.",
            f"✅ '{correct_choice}' — Proper grammatical concord."
        ]
        memory_tip = "💡 Memory Tip: Respectful addressing with 'आप' always takes the plural suffix '-ते हैं'."
    else:
        why_incorrect = (
            f"You selected '{user_choice}', which creates a grammatical or semantic mismatch with the sentence prompt."
        )
        grammar_rule = "Rule: Verb tense and subject-verb agreement must be preserved throughout the clause."
        contrast_examples = [
            f"❌ '{user_choice}' — Incorrect tense/number form.",
            f"✅ '{correct_choice}' — Correct standard English form."
        ]
        memory_tip = "💡 Memory Tip: Check whether the sentence refers to the present, past, or a habitual action."

    return schemas.ExplainMistakeResponse(
        question_text=q_text,
        user_selection_text=user_choice,
        correct_answer_text=correct_choice,
        why_incorrect=why_incorrect,
        grammar_rule=grammar_rule,
        contrast_examples=contrast_examples,
        memory_tip=memory_tip
    )
