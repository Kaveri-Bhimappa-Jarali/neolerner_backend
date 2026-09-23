import uuid
import json
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import schemas, models, database, dependencies, gamification

router = APIRouter(prefix="/api/stories", tags=["stories"])

DEFAULT_STORIES_DATA = {
    "kn": [
        {
            "title": "ರೈಲ್ವೆ ನಿಲ್ದಾಣದಲ್ಲಿ ಒಂದು ದಿನ (A Day at the Railway Station)",
            "cefr": "A1",
            "icon": "🚆",
            "scenes": [
                {"scene": 1, "char": "ರವಿ (Ravi)", "avatar": "👨", "target": "ನಮಸ್ಕಾರ ಸ್ವಾಮಿ! ಬೆಂಗಳೂರಿಗೆ ಹೋಗುವ ರೈಲು ಎಷ್ಟು ಗಂಟೆಗೆ ಬರುತ್ತದೆ?", "trans": "Hello sir! At what time does the train to Bengaluru arrive?"},
                {"scene": 2, "char": "ಟಿಕೆಟ್ ಅಧಿಕಾರಿ (Officer)", "avatar": "👮", "target": "ನಮಸ್ಕಾರ. ಬೆಂಗಳೂರು ಎಕ್ಸ್‌ಪ್ರೆಸ್ ಸರಿಯಾಗಿ ಮೂರು ಗಂಟೆಗೆ ಪ್ಲಾಟ್‌ಫಾರ್ಮ್ 1 ಕ್ಕೆ ಬರುತ್ತದೆ.", "trans": "Hello. The Bengaluru Express arrives at platform 1 sharp at 3 o'clock."},
                {"scene": 3, "char": "ರವಿ (Ravi)", "avatar": "👨", "target": "ತುಂಬಾ ಧನ್ಯವಾದಗಳು. ನನಗೆ ಒಂದು ಎರಡನೇ ದರ್ಜೆಯ ಟಿಕೆಟ್ ಕೊಡಿ.", "trans": "Thank you very much. Please give me one second-class ticket."},
                {"scene": 4, "char": "ಟಿಕೆಟ್ ಅಧಿಕಾರಿ (Officer)", "avatar": "👮", "target": "ಇಗೋ ನಿಮ್ಮ ಟಿಕೆಟ್. ಪ್ರಯಾಣ ಸುಖಕರವಾಗಿರಲಿ!", "trans": "Here is your ticket. Have a pleasant journey!"}
            ],
            "exercises": [
                {
                    "scene": 2,
                    "question": "ರವಿ ಎಲ್ಲಿಗೆ ಹೋಗಲು ಬಯಸುತ್ತಿದ್ದಾನೆ? (Where does Ravi want to go?)",
                    "options": [
                        {"text": "ಬೆಂಗಳೂರು (Bengaluru)", "is_correct": True, "explanation": "ರವಿ ಬೆಂಗಳೂರಿಗೆ ಹೋಗುವ ರೈಲಿನ ಸಮಯ ಕೇಳಿದನು."},
                        {"text": "ಮೈಸೂರು (Mysuru)", "is_correct": False, "explanation": "ತಪ್ಪಾದ ಆಯ್ಕೆ."},
                        {"text": "ದೆಹಲಿ (Delhi)", "is_correct": False, "explanation": "ತಪ್ಪಾದ ಆಯ್ಕೆ."}
                    ],
                    "type": "comprehension"
                },
                {
                    "scene": 4,
                    "question": "ರೈಲು ಯಾವ ಪ್ಲಾಟ್‌ಫಾರ್ಮ್‌ಗೆ ಬರುತ್ತದೆ? (Which platform does the train arrive on?)",
                    "options": [
                        {"text": "ಪ್ಲಾಟ್‌ಫಾರ್ಮ್ 1 (Platform 1)", "is_correct": True, "explanation": "ಅಧಿಕಾರಿ ಪ್ಲಾಟ್‌ಫಾರ್ಮ್ 1 ಎಂದು ತಿಳಿಸಿದರು."},
                        {"text": "ಪ್ಲಾಟ್‌ಫಾರ್ಮ್ 5 (Platform 5)", "is_correct": False, "explanation": "ತಪ್ಪಾದ ಆಯ್ಕೆ."}
                    ],
                    "type": "comprehension"
                }
            ]
        },
        {
            "title": "ಬೆಳಗಿನ ಕಾಫಿ (The Morning Filter Coffee)",
            "cefr": "A1",
            "icon": "☕",
            "scenes": [
                {"scene": 1, "char": "ಅನು (Anu)", "avatar": "👩", "target": "ಅಣ್ಣಾ, ನನಗೆ ಒಂದು ಬಿಸಿ ಫಿಲ್ಟರ್ ಕಾಫಿ ಕೊಡಿ.", "trans": "Brother, please give me one hot filter coffee."},
                {"scene": 2, "char": "ಕಾಫಿ ಮಾಲೀಕ (Barista)", "avatar": "👨‍🍳", "target": "ಸಕ್ಕರೆ ಜಾಸ್ತಿ ಬೇಕಾ ಅಥವಾ ಮಧ್ಯಮವೇ?", "trans": "Do you want extra sugar or medium?"},
                {"scene": 3, "char": "ಅನು (Anu)", "avatar": "👩", "target": "ಮಧ್ಯಮ ಸಕ್ಕರೆ ಹಾಕಿ, ತುಂಬಾ ಬಿಸಿಯಾಗಿರಲಿ.", "trans": "Put medium sugar, and make it very hot."},
                {"scene": 4, "char": "ಕಾಫಿ ಮಾಲೀಕ (Barista)", "avatar": "👨‍🍳", "target": "ಇಗೋ ಬಿಸಿ ಬಿಸಿ ಕರ್ನಾಟಕ ಫಿಲ್ಟರ್ ಕಾಫಿ!", "trans": "Here is steaming hot Karnataka filter coffee!"}
            ],
            "exercises": [
                {
                    "scene": 3,
                    "question": "ಅನು ಕಾಫಿಯಲ್ಲಿ ಎಷ್ಟು ಸಕ್ಕರೆ ಕೇಳಿದಳು? (How much sugar did Anu ask for?)",
                    "options": [
                        {"text": "ಮಧ್ಯಮ ಸಕ್ಕರೆ (Medium sugar)", "is_correct": True, "explanation": "ಅನು ಮಧ್ಯಮ ಸಕ್ಕರೆ ಕೇಳಿದಳು."},
                        {"text": "ಸಕ್ಕರೆ ಬೇಡ (No sugar)", "is_correct": False, "explanation": "ತಪ್ಪಾದ ಉತ್ತರ."},
                        {"text": "ತುಂಬಾ ಜಾಸ್ತಿ (Very high)", "is_correct": False, "explanation": "ತಪ್ಪಾದ ಉತ್ತರ."}
                    ],
                    "type": "comprehension"
                }
            ]
        }
    ],
    "te": [
        {
            "title": "రైల్వే స్టేషన్‌లో ఒక రోజు (A Day at the Railway Station)",
            "cefr": "A1",
            "icon": "🚆",
            "scenes": [
                {"scene": 1, "char": "రవి (Ravi)", "avatar": "👨", "target": "నమస్కారం అండీ! హైదరాబాద్ వెళ్లే రైలు ఎప్పుడు వస్తుంది?", "trans": "Hello sir! When will the train to Hyderabad arrive?"},
                {"scene": 2, "char": "టికెట్ అధికారి (Officer)", "avatar": "👮", "target": "హైదరాబాద్ ఎక్స్‌ప్రెస్ మూడు గంటలకు ప్లాట్‌ఫారమ్ 2 పై వస్తుంది.", "trans": "The Hyderabad Express arrives at platform 2 at 3 o'clock."},
                {"scene": 3, "char": "రవి (Ravi)", "avatar": "👨", "target": "చాలా ధన్యవాదాలు. నాకు ఒక టికెట్ ఇవ్వండి.", "trans": "Thank you very much. Please give me one ticket."}
            ],
            "exercises": [
                {
                    "scene": 2,
                    "question": "రైలు ఎక్కడికి వెళ్తుంది? (Where is the train going?)",
                    "options": [
                        {"text": "హైదరాబాద్ (Hyderabad)", "is_correct": True, "explanation": "రైలు హైదరాబాద్ వెళ్తుంది."},
                        {"text": "విజయవాడ (Vijayawada)", "is_correct": False, "explanation": "తప్పు సమాధానం."}
                    ],
                    "type": "comprehension"
                }
            ]
        }
    ],
    "mr": [
        {
            "title": "रेल्वे स्थानकावर एक दिवस (A Day at the Railway Station)",
            "cefr": "A1",
            "icon": "🚆",
            "scenes": [
                {"scene": 1, "char": "रवी (Ravi)", "avatar": "👨", "target": "नमस्कार! पुण्याला जाणारी गाडी किती वाजता येईल?", "trans": "Hello! What time will the train to Pune arrive?"},
                {"scene": 2, "char": "तिकीट अधिकारी (Officer)", "avatar": "👮", "target": "पुणे एक्सप्रेस दुपारी तीन वाजता प्लॅटफॉर्म 1 वर येईल.", "trans": "Pune Express will arrive at platform 1 at 3 PM."},
                {"scene": 3, "char": "रवी (Ravi)", "avatar": "👨", "target": "खूप धन्यवाद! मला एक तिकीट द्या.", "trans": "Thank you so much! Please give me one ticket."}
            ],
            "exercises": [
                {
                    "scene": 2,
                    "question": "रवीला कुठे जायचे आहे? (Where does Ravi want to go?)",
                    "options": [
                        {"text": "पुणे (Pune)", "is_correct": True, "explanation": "रवी पुण्याला जात आहे."},
                        {"text": "मुंबई (Mumbai)", "is_correct": False, "explanation": "चुकीचा पर्याय."}
                    ],
                    "type": "comprehension"
                }
            ]
        }
    ],
    "hi": [
        {
            "title": "रेलवे स्टेशन पर एक दिन (A Day at the Railway Station)",
            "cefr": "A1",
            "icon": "🚆",
            "scenes": [
                {"scene": 1, "char": "रवि (Ravi)", "avatar": "👨", "target": "नमस्ते बाबूजी! दिल्ली जाने वाली ट्रेन कितने बजे आएगी?", "trans": "Hello sir! What time does the train to Delhi arrive?"},
                {"scene": 2, "char": "टिकट बाबू (Officer)", "avatar": "👮", "target": "दिल्ली एक्सप्रेस दोपहर 3 बजे प्लेटफ़ॉर्म 1 पर आएगी।", "trans": "Delhi Express will arrive at platform 1 at 3 PM."},
                {"scene": 3, "char": "रवि (Ravi)", "avatar": "👨", "target": "बहुत धन्यवाद! मुझे एक टिकट दे दीजिए।", "trans": "Thank you very much! Please give me one ticket."}
            ],
            "exercises": [
                {
                    "scene": 2,
                    "question": "रवि कहाँ जा रहा है? (Where is Ravi going?)",
                    "options": [
                        {"text": "दिल्ली (Delhi)", "is_correct": True, "explanation": "रवि दिल्ली जा रहा है।"},
                        {"text": "जयपुर (Jaipur)", "is_correct": False, "explanation": "गलत उत्तर।"}
                    ],
                    "type": "comprehension"
                }
            ]
        }
    ],
    "en": [
        {
            "title": "A Day at the Railway Station",
            "cefr": "A1",
            "icon": "🚆",
            "scenes": [
                {"scene": 1, "char": "Ravi", "avatar": "👨", "target": "Excuse me, officer! When does the express train to London arrive?", "trans": "Excuse me, officer! When does the express train to London arrive?"},
                {"scene": 2, "char": "Station Officer", "avatar": "👮", "target": "The London Express arrives at Platform 1 at 3:00 PM sharp.", "trans": "The London Express arrives at Platform 1 at 3:00 PM sharp."},
                {"scene": 3, "char": "Ravi", "avatar": "👨", "target": "Thank you very much! I'd like one one-way ticket please.", "trans": "Thank you very much! I'd like one one-way ticket please."}
            ],
            "exercises": [
                {
                    "scene": 2,
                    "question": "Where does Ravi intend to travel?",
                    "options": [
                        {"text": "London", "is_correct": True, "explanation": "Ravi is taking the London Express."},
                        {"text": "Oxford", "is_correct": False, "explanation": "Incorrect destination."}
                    ],
                    "type": "comprehension"
                }
            ]
        }
    ]
}

def ensure_stories_seeded(language_id: UUID, lang_code: str, db: Session):
    existing_count = db.query(models.Story).filter(models.Story.language_id == language_id).count()
    if existing_count > 0:
        return

    data = DEFAULT_STORIES_DATA.get(lang_code, DEFAULT_STORIES_DATA["en"])
    order = 1
    for s_item in data:
        story = models.Story(
            language_id=language_id,
            title=s_item["title"],
            target_cefr=s_item["cefr"],
            icon=s_item["icon"],
            xp_reward=30,
            gem_reward=15,
            order=order
        )
        db.add(story)
        db.commit()
        db.refresh(story)

        for sc in s_item["scenes"]:
            scene = models.StoryScene(
                story_id=story.id,
                scene_number=sc["scene"],
                character_name=sc["char"],
                character_avatar=sc["avatar"],
                dialogue_target=sc["target"],
                dialogue_translation=sc["trans"]
            )
            db.add(scene)

        for ex in s_item["exercises"]:
            exercise = models.StoryExercise(
                story_id=story.id,
                scene_number=ex["scene"],
                question_text=ex["question"],
                options_json=json.dumps(ex["options"]),
                exercise_type=ex["type"]
            )
            db.add(exercise)

        db.commit()
        order += 1

@router.get("", response_model=List[schemas.StorySummaryResponse])
@router.get("/", response_model=List[schemas.StorySummaryResponse])
def get_stories_list(
    language_id: Optional[UUID] = Query(None),
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    target_lang_id = language_id or current_learner.target_language_id
    if not target_lang_id:
        target_lang = db.query(models.Language).first()
        target_lang_id = target_lang.id if target_lang else None

    if not target_lang_id:
        return []

    lang = db.query(models.Language).filter(models.Language.id == target_lang_id).first()
    lang_code = lang.code if lang else "kn"

    ensure_stories_seeded(target_lang_id, lang_code, db)

    stories = db.query(models.Story).filter(models.Story.language_id == target_lang_id).order_by(models.Story.order).all()

    # Query completed progress for current learner
    progress_map = {
        p.story_id: p for p in db.query(models.StoryProgress).filter(
            models.StoryProgress.learner_id == current_learner.id
        ).all()
    }

    result = []
    for s in stories:
        prog = progress_map.get(s.id)
        result.append(schemas.StorySummaryResponse(
            id=s.id,
            title=s.title,
            target_cefr=s.target_cefr,
            icon=s.icon,
            xp_reward=s.xp_reward,
            gem_reward=s.gem_reward,
            order=s.order,
            is_completed=prog.is_completed if prog else False,
            best_score=prog.score if prog else None
        ))
    return result

@router.get("/{story_id}", response_model=schemas.StoryDetailResponse)
def get_story_detail(
    story_id: UUID,
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    story = db.query(models.Story).filter(models.Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    prog = db.query(models.StoryProgress).filter(
        models.StoryProgress.learner_id == current_learner.id,
        models.StoryProgress.story_id == story_id
    ).first()

    scenes = []
    for sc in story.scenes:
        scenes.append(schemas.StorySceneResponse(
            id=sc.id,
            scene_number=sc.scene_number,
            character_name=sc.character_name,
            character_avatar=sc.character_avatar,
            dialogue_target=sc.dialogue_target,
            dialogue_translation=sc.dialogue_translation,
            audio_cue_url=sc.audio_cue_url
        ))

    exercises = []
    for ex in story.exercises:
        opts = json.loads(ex.options_json) if ex.options_json else []
        exercises.append(schemas.StoryExerciseResponse(
            id=ex.id,
            scene_number=ex.scene_number,
            question_text=ex.question_text,
            options=opts,
            exercise_type=ex.exercise_type
        ))

    return schemas.StoryDetailResponse(
        id=story.id,
        title=story.title,
        target_cefr=story.target_cefr,
        icon=story.icon,
        xp_reward=story.xp_reward,
        gem_reward=story.gem_reward,
        scenes=scenes,
        exercises=exercises,
        is_completed=prog.is_completed if prog else False
    )

@router.post("/{story_id}/complete", response_model=schemas.StoryCompleteResponse)
def complete_story(
    story_id: UUID,
    submit: schemas.StoryCompleteSubmit,
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    story = db.query(models.Story).filter(models.Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    prog = db.query(models.StoryProgress).filter(
        models.StoryProgress.learner_id == current_learner.id,
        models.StoryProgress.story_id == story_id
    ).first()

    is_first_time = not prog or not prog.is_completed

    if not prog:
        prog = models.StoryProgress(
            learner_id=current_learner.id,
            story_id=story_id,
            is_completed=True,
            score=submit.score
        )
        db.add(prog)
    else:
        prog.is_completed = True
        prog.score = max(prog.score, submit.score)
        prog.completed_at = datetime.utcnow()

    # Award rewards
    xp = story.xp_reward if is_first_time else 10
    gems = story.gem_reward if is_first_time else 5
    gamification.award_xp_and_gems(current_learner, xp=xp, gems=gems, db=db)
    gamification.update_streak(current_learner, db=db)

    db.commit()

    return schemas.StoryCompleteResponse(
        story_id=story.id,
        xp_earned=xp,
        gems_earned=gems,
        is_completed=True
    )
