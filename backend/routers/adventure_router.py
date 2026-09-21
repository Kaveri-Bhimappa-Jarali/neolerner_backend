import uuid
import json
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import schemas, models, database, dependencies, gamification

router = APIRouter(prefix="/api/adventures", tags=["adventures"])

DEFAULT_ADVENTURES_DATA = {
    "kn": [
        {
            "title": "ಕೆಂಪೇಗೌಡ ವಿಮಾನ ನಿಲ್ದಾಣದ ಸಾಹಸ (Airport Odyssey)",
            "scenario": "airport",
            "intro": "ನೀವು ಬೆಂಗಳೂರು ವಿಮಾನ ನಿಲ್ದಾಣ ತಲುಪಿದ್ದೀರಿ. ನಿಮ್ಮ ವಿಮಾನ ಹತ್ತಲು ಸರಿಯಾದ ಸೂಚನೆಗಳನ್ನು ಪಾಲಿಸಿ.",
            "diff": 2,
            "steps": [
                {
                    "step_key": "start",
                    "narrative": "ನೀವು ವಿಮಾನ ನಿಲ್ದಾಣದ ಪ್ರವೇಶ ದ್ವಾರದಲ್ಲಿದ್ದೀರಿ. ಭದ್ರತಾ ಸಿಬ್ಬಂದಿ ನಿಮ್ಮ ಗುರುತಿನ ಚೀಟಿ ಮತ್ತು ಟಿಕೆಟ್ ಕೇಳುತ್ತಿದ್ದಾರೆ.",
                    "prompt": "ಭದ್ರತಾ ಸಿಬ್ಬಂದಿಗೆ ನೀವು ಏನು ಹೇಳುತ್ತೀರಿ?",
                    "expected": "ಟಿಕೆಟ್ ಮತ್ತು ಆಧಾರ್ ಕಾರ್ಡ್ ಇಲ್ಲಿದೆ ನೋಡಿ",
                    "choices": [
                        {"text": "ನನ್ನ ಟಿಕೆಟ್ ಮತ್ತು ಆಧಾರ್ ಕಾರ್ಡ್ ಇಲ್ಲಿದೆ ನೋಡಿ (Here is my ticket and Aadhaar card)", "next": "check_in", "feedback": "ಸಿಬ್ಬಂದಿ ನಗುತ್ತಾ ನಿಮ್ಮನ್ನು ಒಳಗೆ ಬಿಟ್ಟರು. ಶುಭ ಪ್ರಯಾಣ!", "xp": 15},
                        {"text": "ನನ್ನ ಬಳಿ ಏನೂ ಇಲ್ಲ (I don't have anything)", "next": "retry", "feedback": "ಟಿಕೆಟ್ ಇಲ್ಲದೆ ಒಳಗೆ ಪ್ರವೇಶವಿಲ್ಲ!", "xp": 0}
                    ]
                },
                {
                    "step_key": "check_in",
                    "narrative": "ನೀವು ಚೆಕ್-ಇನ್ ಕೌಂಟರ್‌ಗೆ ಬಂದಿದ್ದೀರಿ. ಅಧಿಕಾರಿ ಕೇಳುತ್ತಾರೆ: 'ನಿಮ್ಮ ಲಗೇಜ್ ತೂಕ ಎಷ್ಟಿದೆ?'",
                    "prompt": "ಅಧಿಕಾರಿಗೆ ನಿಮ್ಮ ಸೂಟ್‌ಕೇಸ್ ಒಪ್ಪಿಸಿ ಏನು ಹೇಳುತ್ತೀರಿ?",
                    "expected": "ನನ್ನ ಬಳಿ ಒಂದು ಬ್ಯಾಗ್ ಮಾತ್ರ ಇದೆ",
                    "choices": [
                        {"text": "ನನ್ನ ಬಳಿ ಕೇವಲ 15 ಕೆಜಿ ತೂಕದ ಒಂದು ಬ್ಯಾಗ್ ಇದೆ (I have only one bag weighing 15 kg)", "next": "security", "feedback": "ಬ್ಯಾಗ್ ತೂಕ ಸರಿಯಾಗಿದೆ. ಬೋರ್ಡಿಂಗ್ ಪಾಸ್ ನೀಡಲಾಗಿದೆ!", "xp": 15},
                        {"text": "ಲಗೇಜ್ ಎಲ್ಲಿದೆ ನನಗೆ ಗೊತ್ತಿಲ್ಲ (I don't know where my luggage is)", "next": "retry", "feedback": "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಬ್ಯಾಗ್ ತೂಕ ಮಾಡಿ!", "xp": 0}
                    ]
                },
                {
                    "step_key": "security",
                    "narrative": "ಭದ್ರತಾ ತಪಾಸಣಾ ಕೊಠಡಿ. ಸಿಬ್ಬಂದಿ ಲ್ಯಾಪ್‌ಟಾಪ್ ಪ್ರತ್ಯೇಕ ಟ್ರೇನಲ್ಲಿ ಇಡಲು ಸೂಚಿಸುತ್ತಾರೆ.",
                    "prompt": "ನೀವು ಎಲೆಕ್ಟ್ರಾನಿಕ್ ವಸ್ತುಗಳನ್ನು ಟ್ರೇನಲ್ಲಿ ಇಡುವಾಗ ಏನು ಹೇಳುತ್ತೀರಿ?",
                    "expected": "ನನ್ನ ಲ್ಯಾಪ್‌ಟಾಪ್ ಅನ್ನು ಟ್ರೇನಲ್ಲಿ ಇಟ್ಟಿದ್ದೇನೆ",
                    "choices": [
                        {"text": "ನನ್ನ ಲ್ಯಾಪ್‌ಟಾಪ್ ಮತ್ತು ಮೊಬೈಲ್ ಅನ್ನು ಟ್ರೇನಲ್ಲಿ ಇಟ್ಟಿದ್ದೇನೆ (I have placed my laptop and mobile in the tray)", "next": "gate", "feedback": "ತಪಾಸಣೆ ಯಶಸ್ವಿಯಾಗಿ ಮುಗಿಯಿತು!", "xp": 15}
                    ]
                },
                {
                    "step_key": "gate",
                    "narrative": "ಬೋರ್ಡಿಂಗ್ ಗೇಟ್ 24. ಕೊನೆಯ ಕರೆ ಬರುತ್ತಿದೆ!",
                    "prompt": "ವಿಮಾನ ಹತ್ತುವಾಗ ಸಿಬ್ಬಂದಿಗೆ ಬೋರ್ಡಿಂಗ್ ಪಾಸ್ ತೋರಿಸಿ ಏನು ಹೇಳುತ್ತೀರಿ?",
                    "expected": "ಧನ್ಯವಾದಗಳು, ನಾನು ಸೀಟ್ ನಂಬರ್ 12A ಗೆ ಹೋಗುತ್ತಿದ್ದೇನೆ",
                    "choices": [
                        {"text": "ಧನ್ಯವಾದಗಳು, ನಾನು ಸೀಟ್ ನಂಬರ್ 12A ಗೆ ಹೋಗುತ್ತಿದ್ದೇನೆ (Thank you, I am going to seat 12A)", "next": "finish", "feedback": "ಅಭಿನಂದನೆಗಳು! ನೀವು ಯಶಸ್ವಿಯಾಗಿ ವಿಮಾನ ಹತ್ತಿದ್ದೀರಿ!", "xp": 20}
                    ]
                }
            ]
        }
    ],
    "te": [
        {
            "title": "విమానాశ్రయ సాహసం (Airport Odyssey)",
            "scenario": "airport",
            "intro": "మీరు విమానాశ్రయానికి చేరుకున్నారు. విమానం ఎక్కేందుకు సరైన సూచనలను పాటించండి.",
            "diff": 2,
            "steps": [
                {
                    "step_key": "start",
                    "narrative": "సెక్యూరిటీ అధికారి టికెట్ మరియు ఐడీ అడుగుతున్నారు.",
                    "prompt": "మీరు అధికారికి ఏమి చెబుతారు?",
                    "expected": "నా టికెట్ మరియు ఆధార్ కార్డ్ ఇదిగోండి",
                    "choices": [
                        {"text": "నా టికెట్ మరియు ఆధార్ కార్డ్ ఇదిగోండి (Here is my ticket and Aadhaar)", "next": "finish", "feedback": "మీరు విజయవంతంగా విమానాశ్రయంలోకి ప్రవేశించారు!", "xp": 50}
                    ]
                }
            ]
        }
    ],
    "mr": [
        {
            "title": "विमानतळावरील प्रवास (Airport Odyssey)",
            "scenario": "airport",
            "intro": "तुम्ही विमानतळावर पोहोचला आहात. विमानामध्ये बसण्यासाठी सर्व पायऱ्या पूर्ण करा.",
            "diff": 2,
            "steps": [
                {
                    "step_key": "start",
                    "narrative": "सुरक्षा अधिकारी तिकीट आणि ओळखपत्र मागत आहेत.",
                    "prompt": "तुम्ही अधिकाऱ्याला काय सांगाल?",
                    "expected": "हे माझे तिकीट आणि ओळखपत्र आहे",
                    "choices": [
                        {"text": "हे माझे तिकीट आणि ओळखपत्र आहे (Here is my ticket and ID)", "next": "finish", "feedback": "छान! तुम्ही सुरक्षितपणे आत गेलात.", "xp": 50}
                    ]
                }
            ]
        }
    ],
    "hi": [
        {
            "title": "हवाई अड्डे की यात्रा (Airport Odyssey)",
            "scenario": "airport",
            "intro": "आप हवाई अड्डे पहुँच चुके हैं। अपनी उड़ान पकड़ने के लिए सही दिशा-निर्देशों का पालन करें।",
            "diff": 2,
            "steps": [
                {
                    "step_key": "start",
                    "narrative": "सुरक्षा अधिकारी आपका टिकट और पहचान पत्र मांग रहे हैं।",
                    "prompt": "आप सुरक्षा अधिकारी से क्या कहेंगे?",
                    "expected": "यह रहा मेरा टिकट और आधार कार्ड",
                    "choices": [
                        {"text": "यह रहा मेरा टिकट और आधार कार्ड (Here is my ticket and ID card)", "next": "finish", "feedback": "बहुत बढ़िया! अधिकारी ने आपको अंदर जाने दिया।", "xp": 50}
                    ]
                }
            ]
        }
    ],
    "en": [
        {
            "title": "Airport Navigator Odyssey",
            "scenario": "airport",
            "intro": "You have arrived at Terminal 2. Navigate through check-in, security and board your flight.",
            "diff": 2,
            "steps": [
                {
                    "step_key": "start",
                    "narrative": "Security at the entry gate asks for your boarding document and photo ID.",
                    "prompt": "How do you present your credentials?",
                    "expected": "Here is my passport and mobile boarding pass",
                    "choices": [
                        {"text": "Here is my passport and mobile boarding pass, officer.", "next": "finish", "feedback": "Welcome to the terminal! Have a safe flight.", "xp": 50}
                    ]
                }
            ]
        }
    ]
}

def ensure_adventures_seeded(language_id: UUID, lang_code: str, db: Session):
    existing = db.query(models.Adventure).filter(models.Adventure.language_id == language_id).count()
    if existing > 0:
        return

    data = DEFAULT_ADVENTURES_DATA.get(lang_code, DEFAULT_ADVENTURES_DATA["en"])
    for adv in data:
        new_adv = models.Adventure(
            language_id=language_id,
            title=adv["title"],
            scenario_type=adv["scenario"],
            intro_text=adv["intro"],
            difficulty_level=adv["diff"],
            xp_reward=60
        )
        db.add(new_adv)
        db.commit()
        db.refresh(new_adv)

        for s in adv["steps"]:
            step = models.AdventureStep(
                adventure_id=new_adv.id,
                step_key=s["step_key"],
                narrative=s["narrative"],
                prompt_in_target=s["prompt"],
                expected_concept=s["expected"],
                choices_json=json.dumps(s["choices"])
            )
            db.add(step)
        db.commit()

@router.get("", response_model=List[schemas.AdventureSummaryResponse])
@router.get("/", response_model=List[schemas.AdventureSummaryResponse])
def get_adventures(
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    target_lang_id = current_learner.target_language_id
    if not target_lang_id:
        target_lang = db.query(models.Language).first()
        target_lang_id = target_lang.id if target_lang else None

    if not target_lang_id:
        return []

    lang = db.query(models.Language).filter(models.Language.id == target_lang_id).first()
    lang_code = lang.code if lang else "kn"

    ensure_adventures_seeded(target_lang_id, lang_code, db)

    adventures = db.query(models.Adventure).filter(models.Adventure.language_id == target_lang_id).all()
    progress_map = {
        p.adventure_id: p for p in db.query(models.AdventureProgress).filter(
            models.AdventureProgress.learner_id == current_learner.id
        ).all()
    }

    result = []
    for a in adventures:
        prog = progress_map.get(a.id)
        result.append(schemas.AdventureSummaryResponse(
            id=a.id,
            title=a.title,
            scenario_type=a.scenario_type,
            intro_text=a.intro_text,
            difficulty_level=a.difficulty_level,
            xp_reward=a.xp_reward,
            is_completed=prog.is_completed if prog else False
        ))
    return result

@router.get("/{adventure_id}", response_model=schemas.AdventureDetailResponse)
def get_adventure_detail(
    adventure_id: UUID,
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    adv = db.query(models.Adventure).filter(models.Adventure.id == adventure_id).first()
    if not adv:
        raise HTTPException(status_code=404, detail="Adventure not found")

    prog = db.query(models.AdventureProgress).filter(
        models.AdventureProgress.learner_id == current_learner.id,
        models.AdventureProgress.adventure_id == adventure_id
    ).first()

    steps = []
    for st in adv.steps:
        choices = json.loads(st.choices_json) if st.choices_json else []
        steps.append(schemas.AdventureStepResponse(
            id=st.id,
            step_key=st.step_key,
            narrative=st.narrative,
            prompt_in_target=st.prompt_in_target,
            expected_concept=st.expected_concept,
            choices=choices
        ))

    return schemas.AdventureDetailResponse(
        id=adv.id,
        title=adv.title,
        scenario_type=adv.scenario_type,
        intro_text=adv.intro_text,
        steps=steps,
        current_step_key=prog.current_step_key if prog else "start",
        is_completed=prog.is_completed if prog else False
    )

@router.post("/{adventure_id}/step", response_model=schemas.AdventureStepResult)
def submit_adventure_step(
    adventure_id: UUID,
    sub: schemas.AdventureStepSubmit,
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    adv = db.query(models.Adventure).filter(models.Adventure.id == adventure_id).first()
    if not adv:
        raise HTTPException(status_code=404, detail="Adventure not found")

    step = db.query(models.AdventureStep).filter(
        models.AdventureStep.adventure_id == adventure_id,
        models.AdventureStep.step_key == sub.step_key
    ).first()
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")

    choices = json.loads(step.choices_json) if step.choices_json else []
    chosen = choices[sub.chosen_index] if sub.chosen_index is not None and 0 <= sub.chosen_index < len(choices) else choices[0]

    next_step = chosen.get("next", "finish")
    feedback = chosen.get("feedback", "Great job navigating this scenario!")
    xp = chosen.get("xp", 15)
    is_final = next_step == "finish"

    prog = db.query(models.AdventureProgress).filter(
        models.AdventureProgress.learner_id == current_learner.id,
        models.AdventureProgress.adventure_id == adventure_id
    ).first()

    if not prog:
        prog = models.AdventureProgress(
            learner_id=current_learner.id,
            adventure_id=adventure_id,
            current_step_key=next_step,
            is_completed=is_final
        )
        db.add(prog)
    else:
        prog.current_step_key = next_step
        if is_final:
            prog.is_completed = True
            prog.completed_at = datetime.utcnow()

    gamification.award_xp_and_gems(current_learner, xp=xp, gems=5 if is_final else 0, db=db)
    gamification.update_streak(current_learner, db=db)
    db.commit()

    return schemas.AdventureStepResult(
        next_step_key=next_step,
        narrative_feedback=feedback,
        is_final=is_final,
        xp_earned=xp,
        is_completed=is_final
    )
