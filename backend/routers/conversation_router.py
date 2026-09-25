import uuid
import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import schemas, models, database, dependencies, gamification

router = APIRouter(prefix="/api/conversation", tags=["conversation_lab"])

SCENARIOS = {
    "restaurant": {
        "name": "At the Local Restaurant",
        "icon": "🍽️",
        "description": "Order traditional food, ask for recommendations, and request the bill.",
        "cefr_target": "A1-A2",
        "prompts": {
            "kn": {
                "greeting": "ನಮಸ್ಕಾರ! ನಮ್ಮ ಉಪಾಹಾರ ಮಂದಿರಕ್ಕೆ ಸ್ವಾಗತ. ನೀವು ಏನು ಸೇವಿಸಲು ಇಷ್ಟಪಡುತ್ತೀರಿ?",
                "phonetic": "Namaskara! Namma upahara mandirakke swagata. Neevu enu sevisalu ishtapadutteeri?",
                "translation": "Hello! Welcome to our restaurant. What would you like to have?",
                "hints": ["ನನಗೆ ಒಂದು ಮಸಾಲೆ ದೋಸೆ ಬೇಕು (I want a masala dosa)", "ಕಾಫಿ ಇದೆಯೇ? (Do you have coffee?)", "ಬಿಲ್ ಎಷ್ಟು? (How much is the bill?)"],
                "expected": ["ದೋಸೆ", "ಕಾಫಿ", "ಊಟ", "ನೀರು", "ಬೇಕು", "ಬಿಲ್"]
            },
            "te": {
                "greeting": "నమస్కారం! మా హోటల్‌కి స్వాగతం. మీరు ఏమి ఆర్డర్ చేయాలనుకుంటున్నారు?",
                "phonetic": "Namaskaram! Maa hotel ki swagatam. Meeru emi order cheyalanukuntunnaru?",
                "translation": "Hello! Welcome to our restaurant. What would you like to order?",
                "hints": ["నాకు దోశ కావాలి (I want dosa)", "మంచి నీళ్లు ఇవ్వండి (Please give drinking water)", "బిల్ ఎంత? (How much is the bill?)"],
                "expected": ["దోశ", "కాఫీ", "భోజనం", "నీరు", "కావాలి", "బిల్"]
            },
            "mr": {
                "greeting": "नमस्कार! आमच्या उपहारगृहात आपले स्वागत आहे. आपण काय खाणार?",
                "phonetic": "Namaskar! Aamchya upahargruhat aaple swagat aahe. Aapan kaay khaanar?",
                "translation": "Hello! Welcome to our restaurant. What will you have?",
                "hints": ["मला चहा आणि पोहे हवे आहेत (I want tea and poha)", "पाणी द्या (Please give water)", "बिल किती झाले? (How much is the bill?)"],
                "expected": ["चहा", "पोहे", "जेवण", "पाणी", "हवे", "बिल"]
            },
            "hi": {
                "greeting": "नमस्ते! हमारे रेस्टोरेंट में आपका स्वागत है। आप क्या खाना पसंद करेंगे?",
                "phonetic": "Namaste! Hamaare restaurant mein aapka swaagat hai. Aap kya khaana pasand karenge?",
                "translation": "Hello! Welcome to our restaurant. What would you like to eat?",
                "hints": ["मुझे एक चाय और समोसा चाहिए (I want a tea and samosa)", "पीने का पानी दीजिए (Please give drinking water)", "बिल कितना हुआ? (How much is the bill?)"],
                "expected": ["चाय", "समोसा", "खाना", "पानी", "चाहिए", "बिल"]
            },
            "en": {
                "greeting": "Hello! Welcome to our cafe. What can I get started for you today?",
                "phonetic": "Hello! Welcome to our cafe. What can I get started for you today?",
                "translation": "Hello! Welcome to our cafe. What can I get started for you today?",
                "hints": ["I would like a coffee and sandwich", "Can I see the dessert menu?", "Could we have the check, please?"],
                "expected": ["coffee", "sandwich", "water", "menu", "bill", "check", "please"]
            }
        }
    },
    "airport": {
        "name": "Bengaluru Airport Navigator",
        "icon": "✈️",
        "description": "Find your check-in counter, boarding gate, and baggage claim.",
        "cefr_target": "A2-B1",
        "prompts": {
            "kn": {
                "greeting": "ನಮಸ್ಕಾರ ಪ್ರಯಾಣಿಕರೇ! ನಿಮಗೆ ವಿಮಾನ ನಿಲ್ದಾಣದಲ್ಲಿ ಯಾವ ಸಹಾಯ ಬೇಕು?",
                "phonetic": "Namaskara prayanikare! Nimage vimana nildanadalli yaava sahaaya beku?",
                "translation": "Hello passenger! What assistance do you need at the airport?",
                "hints": ["ನನ್ನ ಬೋರ್ಡಿಂಗ್ ಗೇಟ್ ಎಲ್ಲಿದೆ? (Where is my boarding gate?)", "ಲಗೇಜ್ ಎಲ್ಲಿ ಕೌಂಟರ್? (Where is the baggage counter?)"],
                "expected": ["ವಿಮಾನ", "ಗೇಟ್", "ಲಗೇಜ್", "ಎಲ್ಲಿದೆ", "ಟಿಕೆಟ್"]
            },
            "te": {
                "greeting": "నమస్కారం! విమానాశ్రయంలో మీకు ఏ సహాయం కావాలి?",
                "phonetic": "Namaskaram! Vimaanashrayamlo meeku e sahaayam kaavali?",
                "translation": "Hello! What help do you need at the airport?",
                "hints": ["బోర్డింగ్ గేట్ ఎక్కడ ఉంది? (Where is the boarding gate?)", "లగేజ్ చెక్-ఇన్ ఎక్కడ? (Where is baggage check-in?)"],
                "expected": ["విమానం", "గేట్", "లగేజ్", "ఎక్కడ", "టికెట్"]
            },
            "mr": {
                "greeting": "नमस्कार! विमानतळावर आपल्याला काय मदत हवी आहे?",
                "phonetic": "Namaskar! Vimaantalaavar aaplyala kaay madat havi aahe?",
                "translation": "Hello! What help do you need at the airport?",
                "hints": ["माझे बोर्डिंग गेट कुठे आहे? (Where is my boarding gate?)", "सामान कुठे जमा करायचे? (Where to deposit luggage?)"],
                "expected": ["विमान", "गेट", "सामान", "कुठे", "तिकीट"]
            },
            "hi": {
                "greeting": "नमस्ते! हवाई अड्डे पर आपको किस सहायता की आवश्यकता है?",
                "phonetic": "Namaste! Hawaai adde par aapko kis sahaayata ki aavashyakta hai?",
                "translation": "Hello! What assistance do you need at the airport?",
                "hints": ["मेरा बोर्डिंग गेट कहाँ है? (Where is my boarding gate?)", "सामान कहाँ जमा करना है? (Where to drop luggage?)"],
                "expected": ["विमान", "गेट", "सामान", "कहाँ", "टिकट"]
            },
            "en": {
                "greeting": "Hello traveller! How may I assist you with your flight today?",
                "phonetic": "Hello traveller! How may I assist you with your flight today?",
                "translation": "Hello traveller! How may I assist you with your flight today?",
                "hints": ["Where is terminal 2 boarding gate?", "Where can I drop my check-in bags?"],
                "expected": ["gate", "flight", "terminal", "baggage", "ticket", "where"]
            }
        }
    },
    "doctor": {
        "name": "Clinic & Health Consultation",
        "icon": "🏥",
        "description": "Describe simple health symptoms, ask about dosage and care.",
        "cefr_target": "A2",
        "prompts": {
            "kn": {
                "greeting": "ನಮಸ್ಕಾರ. ವೈದ್ಯರ ಕೊಠಡಿಗೆ ಬನ್ನಿ. ನಿಮಗೆ ಯಾವ ತೊಂದರೆ ಇದೆ?",
                "phonetic": "Namaskara. Vaidyara kothadige banni. Nimage yaava tondare ide?",
                "translation": "Hello. Come in. What discomfort are you experiencing?",
                "hints": ["ನನಗೆ ತಲೆನೋವು ಮತ್ತು ಜ್ವರ ಇದೆ (I have headache and fever)", "ಔಷಧಿ ಯಾವಾಗ ತಗೋಬೇಕು? (When should I take medicine?)"],
                "expected": ["ಜ್ವರ", "ತಲೆನೋವು", "ಔಷಧಿ", "ನೋವು", "ಇದೆ"]
            },
            "te": {
                "greeting": "నమస్కారం. లోపలికి రండి. మీకు ఏ సమస్య ఉంది?",
                "phonetic": "Namaskaram. Lopaliki randi. Meeku e samasya undi?",
                "translation": "Hello. Please come in. What issue do you have?",
                "hints": ["నాకు జ్వరం మరియు తలనొప్పి ఉంది (I have fever and headache)", "మందులు ఎప్పుడు వేసుకోవాలి? (When to take medicine?)"],
                "expected": ["జ్వరం", "తలనొప్పి", "మందులు", "నొప్పి", "ఉంది"]
            },
            "mr": {
                "greeting": "नमस्कार. या बसा. आपल्याला काय त्रास होत आहे?",
                "phonetic": "Namaskar. Yaa basa. Aaplyala kaay traas hot aahe?",
                "translation": "Hello. Please sit. What problem are you experiencing?",
                "hints": ["मला ताप आणि डोकेदुखी आहे (I have fever and headache)", "औषध कसे घ्यायचे? (How to take medicine?)"],
                "expected": ["ताप", "डोकेदुखी", "औषध", "त्रास", "आहे"]
            },
            "hi": {
                "greeting": "नमस्ते। बैठिए। आपको क्या समस्या हो रही है?",
                "phonetic": "Namaste. Baithiye. Aapko kya samasya ho rahi hai?",
                "translation": "Hello. Please sit. What symptoms are you having?",
                "hints": ["मुझे बुखार और सिरदर्द है (I have fever and headache)", "दवाई कब लेनी है? (When should I take medicine?)"],
                "expected": ["बुखार", "सिरदर्द", "दवाई", "दर्द", "है"]
            },
            "en": {
                "greeting": "Hello. Please have a seat. What brings you into the clinic today?",
                "phonetic": "Hello. Please have a seat. What brings you into the clinic today?",
                "translation": "Hello. Please have a seat. What brings you into the clinic today?",
                "hints": ["I have had a sore throat and slight fever", "How often should I take this prescription?"],
                "expected": ["fever", "headache", "pain", "medicine", "doctor", "throat"]
            }
        }
    },
    "interview": {
        "name": "Professional Career Interview",
        "icon": "💼",
        "description": "Introduce your strengths, experience, and educational background.",
        "cefr_target": "B1-B2",
        "prompts": {
            "kn": {
                "greeting": "ನಮಸ್ಕಾರ! ಸಂದರ್ಶನಕ್ಕೆ ಸ್ವಾಗತ. ದಯವಿಟ್ಟು ನಿಮ್ಮ ಪರಿಚಯ ಮಾಡಿಕೊಳ್ಳಿ.",
                "phonetic": "Namaskara! Sandarshanakke swagata. Dayavittu nimma parichaya maadikkoli.",
                "translation": "Hello! Welcome to the interview. Please introduce yourself.",
                "hints": ["ನನ್ನ ಹೆಸರು... ನಾನು ಸಾಫ್ಟ್‌ವೇರ್ ಇಂಜಿನಿಯರ್ (My name is... I am a software engineer)", "ನಾನು ಹೊಸ ವಿಷಯಗಳನ್ನು ಕಲಿಯಲು ಇಷ್ಟಪಡುತ್ತೇನೆ (I enjoy learning new things)"],
                "expected": ["ಹೆಸರು", "ಕೆಲಸ", "ಅನುಭವ", "ಓದಿದ್ದೇನೆ", "ಸಾಫ್ಟ್‌ವೇರ್"]
            },
            "te": {
                "greeting": "నమస్కారం! ఇంటర్వ్యూకి స్వాగతం. దయచేసి మీ గురించి పరిచయం చేయండి.",
                "phonetic": "Namaskaram! Interview ki swagatam. Dayachesi mee gurinchi parichayam cheyandi.",
                "translation": "Hello! Welcome to the interview. Please introduce yourself.",
                "hints": ["నా పేరు... నేను గ్రాడ్యుయేట్ అయ్యాను (My name is... I graduated)", "నాకు కంప్యూటర్ టెక్నాలజీలో ఆసక్తి ఉంది (I am interested in computer technology)"],
                "expected": ["పేరు", "పని", "అనుభవం", "చదివాను", "సాఫ్ట్‌వేర్"]
            },
            "mr": {
                "greeting": "नमस्कार! मुलाखतीमध्ये आपले स्वागत आहे. कृपया आपली थोडी माहिती सांगा.",
                "phonetic": "Namaskar! Mulakhatimadhye aaple swagat aahe. Krupaya aapli thodi maahiti saanga.",
                "translation": "Hello! Welcome to the interview. Please introduce yourself briefly.",
                "hints": ["माझे नाव... आहे, मला या क्षेत्रात रस आहे (My name is... I am interested in this field)"],
                "expected": ["नाव", "काम", "अनुभव", "शिक्षण", "कंपनी"]
            },
            "hi": {
                "greeting": "नमस्ते! साक्षात्कार में आपका स्वागत है। कृपया अपने बारे में संक्षेप में बताइए।",
                "phonetic": "Namaste! Saakshaatkaar mein aapka swaagat hai. Kripaya apne baare mein bataaiye.",
                "translation": "Hello! Welcome to the interview. Please tell us briefly about yourself.",
                "hints": ["मेरा नाम... है, मैंने बी.टेक किया है (My name is..., I completed B.Tech)"],
                "expected": ["नाम", "काम", "अनुभव", "शिक्षा", "कंपनी"]
            },
            "en": {
                "greeting": "Good day! Welcome to our team interview. Could you please introduce yourself?",
                "phonetic": "Good day! Welcome to our team interview. Could you please introduce yourself?",
                "translation": "Good day! Welcome to our team interview. Could you please introduce yourself?",
                "hints": ["I have experience developing web applications", "I am excited to contribute to your team"],
                "expected": ["experience", "project", "graduate", "developer", "skills", "team"]
            }
        }
    },
    "shopping": {
        "name": "Local Market Shopping",
        "icon": "🛒",
        "description": "Bargain for fresh vegetables, fruits, and inquire about prices.",
        "cefr_target": "A1-A2",
        "prompts": {
            "kn": {
                "greeting": "ಬನ್ನಿ ಅಮ್ಮ/ಅಣ್ಣ! ತಾಜಾ ತರಕಾರಿಗಳು ಮತ್ತು ಹಣ್ಣುಗಳು ಇವೆ. ನಿಮಗೆ ಏನು ಬೇಕು?",
                "phonetic": "Banni! Taaja tarakaarigalu mattu hannugalu ive. Nimage enu beku?",
                "translation": "Welcome! We have fresh vegetables and fruits. What do you need?",
                "hints": ["ಟೊಮೇಟೊ ಒಂದು ಕಿಲೋ ಎಷ್ಟು? (How much is 1 kg tomatoes?)", "ಸ್ವಲ್ಪ ಕಡಿಮೆ ಮಾಡಿ (Please reduce the price a bit)"],
                "expected": ["ಕಿಲೋ", "ಎಷ್ಟು", "ತರಕಾರಿ", "ಹಣ್ಣು", "ಬೇಕು", "ಕಡಿಮೆ"]
            },
            "te": {
                "greeting": "రండి! తాజా కూరగాయలు ఉన్నాయి. మీకు ఏం కావాలి?",
                "phonetic": "Randi! Taaja kooragaayalu unnaayi. Meeku em kaavali?",
                "translation": "Welcome! We have fresh vegetables. What do you want?",
                "hints": ["టమాటాలు కేజీ ఎంత? (How much is 1 kg of tomatoes?)", "కొంచెం తగ్గించండి (Please discount slightly)"],
                "expected": ["కేజీ", "ఎంత", "కూరగాయలు", "కావాలి", "ధర"]
            },
            "mr": {
                "greeting": "या! ताजी भाजी आणि फळे आहेत. काय हवे आहे आपल्याला?",
                "phonetic": "Yaa! Taaji bhaaji aani phale aahet. Kaay have aahe aaplyala?",
                "translation": "Welcome! We have fresh veggies and fruits. What would you like?",
                "hints": ["टोमॅटोचा भाव काय आहे? (What is the price of tomatoes?)", "एक किलो द्या (Give one kilogram)"],
                "expected": ["किलो", "भाव", "भाजी", "फळ", "हवे", "कमी"]
            },
            "hi": {
                "greeting": "आइए! ताज़ी सब्ज़ियाँ और फल हैं। आपको क्या चाहिए?",
                "phonetic": "Aaiye! Taazi sabziyaan aur phal hain. Aapko kya chaahiye?",
                "translation": "Welcome! We have fresh vegetables and fruits. What would you like?",
                "hints": ["टमाटर कितने रुपये किलो हैं? (How much per kilo for tomatoes?)", "थोड़ा कम कीजिए (Please lower the price a little)"],
                "expected": ["किलो", "कितना", "सब्ज़ी", "फल", "चाहिए", "दाम"]
            },
            "en": {
                "greeting": "Welcome to the market! Everything is fresh today. What can I pack for you?",
                "phonetic": "Welcome to the market! Everything is fresh today. What can I pack for you?",
                "translation": "Welcome to the market! Everything is fresh today. What can I pack for you?",
                "hints": ["How much are the fresh oranges per kilo?", "Could you give me a small discount?"],
                "expected": ["kilo", "price", "fresh", "discount", "apples", "oranges", "cost"]
            }
        }
    },
    "introduction": {
        "name": "Meeting a New Friend",
        "icon": "👋",
        "description": "Introduce yourself, share where you are from, and exchange hobbies.",
        "cefr_target": "A1",
        "prompts": {
            "kn": {
                "greeting": "ನಮಸ್ಕಾರ! ನನ್ನ ಹೆಸರು ಆನಂದ್. ನಿಮ್ಮನ್ನು ಭೇಟಿ ಮಾಡಿದ್ದು ತುಂಬಾ ಸಂತೋಷವಾಯಿತು. ನಿಮ್ಮ ಹೆಸರೇನು?",
                "phonetic": "Namaskara! Nanna hesaru Anand. Nimmannu bheti maadiddu tumba santoshavayitu. Nimma hesarenu?",
                "translation": "Hello! My name is Anand. Very glad to meet you. What is your name?",
                "hints": ["ನನ್ನ ಹೆಸರು... (My name is...)", "ನಾನು ಬೆಂಗಳೂರಿನಿಂದ ಬಂದಿದ್ದೇನೆ (I am from Bengaluru)"],
                "expected": ["ಹೆಸರು", "ನಾನು", "ಊರು", "ಸಂತೋಷ", "ನೀವು"]
            },
            "te": {
                "greeting": "నమస్కారం! నా పేరు ఆనంద్. మిమ్మల్ని కలవడం చాలా సంతోషంగా ఉంది. మీ పేరు ఏమిటి?",
                "phonetic": "Namaskaram! Naa peru Anand. Mimmalni kalavadam chaala santoshamga undi. Mee peru emiti?",
                "translation": "Hello! My name is Anand. Very glad to meet you. What is your name?",
                "hints": ["నా పేరు... (My name is...)", "నేను హైదరాబాద్ నుండి వచ్చాను (I came from Hyderabad)"],
                "expected": ["పేరు", "నేను", "సంతోషం", "ఊరు", "మీరు"]
            },
            "mr": {
                "greeting": "नमस्कार! माझे नाव आनंद आहे. आपल्याला भेटून खूप आनंद झाला. आपले नाव काय?",
                "phonetic": "Namaskar! Maajhe naav Anand aahe. Aaplyala bhetun khoop aanand zhaala. Aaple naav kaay?",
                "translation": "Hello! My name is Anand. Great pleasure meeting you. What is your name?",
                "hints": ["माझे नाव... आहे (My name is...)", "मी पुण्यात राहतो (I live in Pune)"],
                "expected": ["नाव", "मी", "आनंद", "राहतो", "आपण"]
            },
            "hi": {
                "greeting": "नमस्ते! मेरा नाम आनंद है। आपसे मिलकर बहुत खुशी हुई। आपका नाम क्या है?",
                "phonetic": "Namaste! Mera naam Anand hai. Aapse milkar bahut khushi hui. Aapka naam kya hai?",
                "translation": "Hello! My name is Anand. Very nice meeting you. What is your name?",
                "hints": ["मेरा नाम... है (My name is...)", "मैं दिल्ली से हूँ (I am from Delhi)"],
                "expected": ["नाम", "मेरा", "खुशी", "कहाँ", "आप"]
            },
            "en": {
                "greeting": "Hi there! My name is Alex. It's a real pleasure to meet you. What is your name?",
                "phonetic": "Hi there! My name is Alex. It's a real pleasure to meet you. What is your name?",
                "translation": "Hi there! My name is Alex. It's a real pleasure to meet you. What is your name?",
                "hints": ["My name is..., nice to meet you too", "I recently moved here from Mumbai"],
                "expected": ["name", "meet", "from", "nice", "hello", "pleasure"]
            }
        }
    }
}

@router.get("/scenarios", response_model=List[schemas.ConversationScenarioItem])
@router.get("/scenarios/", response_model=List[schemas.ConversationScenarioItem])
def get_conversation_scenarios():
    items = []
    for k, v in SCENARIOS.items():
        items.append(schemas.ConversationScenarioItem(
            id=k,
            name=v["name"],
            icon=v["icon"],
            description=v["description"],
            cefr_target=v["cefr_target"],
            context_prompt=v["name"]
        ))
    return items

@router.post("/start", response_model=schemas.ConversationStartResponse)
@router.post("/start/", response_model=schemas.ConversationStartResponse)
def start_conversation(
    req: schemas.ConversationStartRequest,
    current_learner: models.Learner = Depends(dependencies.get_current_learner_or_fallback),
    db: Session = Depends(database.get_db)
):
    gamification.recharge_hearts_by_time(current_learner, db)
    
    # Determine target language
    lang_id = req.target_language_id or current_learner.target_language_id
    lang = db.query(models.Language).filter(models.Language.id == lang_id).first()
    lang_code = lang.code if lang else "kn"

    pref_lang_code = current_learner.preferred_language.code if current_learner.preferred_language else "en"
    
    scenario_key = req.scenario if req.scenario in SCENARIOS else "restaurant"
    scenario_data = SCENARIOS[scenario_key]
    prompt_entry = scenario_data["prompts"].get(lang_code, scenario_data["prompts"]["en"])

    # Create new session record
    session = models.ConversationSession(
        learner_id=current_learner.id,
        scenario=scenario_key,
        language_id=lang_id,
        cefr_target=current_learner.cefr_level or "A1",
        grammar_score=0.0,
        pronunciation_score=0.0,
        vocabulary_score=0.0,
        total_turns=1,
        transcript_json=json.dumps([{
            "sender": "ai",
            "text": prompt_entry["greeting"],
            "phonetic": prompt_entry["phonetic"],
            "translation": prompt_entry["translation"]
        }]),
        is_completed=False
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return schemas.ConversationStartResponse(
        session_id=session.id,
        scenario=scenario_key,
        scenario_name=scenario_data["name"],
        target_language_code=lang_code,
        interface_language_code=pref_lang_code,
        ai_message=prompt_entry["greeting"],
        ai_audio_text=prompt_entry["greeting"],
        phonetic=prompt_entry["phonetic"],
        translation=prompt_entry["translation"],
        context_hints=prompt_entry["hints"],
        expected_phrases=prompt_entry["expected"]
    )

@router.post("/respond", response_model=schemas.ConversationRespondResponse)
@router.post("/respond/", response_model=schemas.ConversationRespondResponse)
def respond_conversation(
    req: schemas.ConversationRespondRequest,
    current_learner: models.Learner = Depends(dependencies.get_current_learner_or_fallback),
    db: Session = Depends(database.get_db)
):
    try:
        session_id_val = req.session_id if isinstance(req.session_id, uuid.UUID) else uuid.UUID(str(req.session_id))
    except Exception:
        session_id_val = req.session_id

    session = db.query(models.ConversationSession).filter(
        models.ConversationSession.id == session_id_val,
        models.ConversationSession.learner_id == current_learner.id
    ).first()

    if not session:
        # Fallback: get latest active session for current learner
        session = db.query(models.ConversationSession).filter(
            models.ConversationSession.learner_id == current_learner.id,
            models.ConversationSession.is_completed == False
        ).order_by(models.ConversationSession.created_at.desc()).first()

    if not session:
        # Auto-create fallback session so user response never fails
        lang_id = current_learner.target_language_id or current_learner.preferred_language_id
        session = models.ConversationSession(
            learner_id=current_learner.id,
            scenario="restaurant",
            language_id=lang_id,
            cefr_target=current_learner.cefr_level or "A1",
            grammar_score=0.0,
            pronunciation_score=0.0,
            vocabulary_score=0.0,
            total_turns=1,
            transcript_json=json.dumps([]),
            is_completed=False
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    lang = db.query(models.Language).filter(models.Language.id == session.language_id).first()
    lang_code = lang.code if lang else "kn"
    scenario_data = SCENARIOS.get(session.scenario, SCENARIOS["restaurant"])

    try:
        transcript = json.loads(session.transcript_json) if session.transcript_json else []
    except Exception:
        transcript = []

    user_text = req.user_transcript.strip() if req.user_transcript else "Hello"

    # Intelligent Heuristic Evaluation of Learner's response
    expected_words = scenario_data["prompts"].get(lang_code, {}).get("expected", [])
    matched_words = [w for w in expected_words if w.lower() in user_text.lower()]
    
    turn_score = 70.0
    if len(matched_words) > 0:
        turn_score += min(30.0, len(matched_words) * 15.0)
    if len(user_text.split()) >= 3:
        turn_score = min(100.0, turn_score + 10.0)

    # Contextual feedback generation
    grammar_correction = None
    pronunciation_tips = []
    vocab_suggestions = []

    if len(user_text.split()) < 2:
        grammar_correction = f"Try speaking a complete sentence next time for better conversational fluency."
    
    if lang_code == "kn":
        pronunciation_tips = ["Emphasize soft retroflex consonants like 'ಳ' and aspirated 'ಖ, ಘ' clearly."]
        vocab_suggestions = ["ಧನ್ಯವಾದಗಳು (Thank you)", "ಖಂಡಿತವಾಗಿ (Certainly)", "ಸ್ವಲ್ಪ ನಿಧಾನವಾಗಿ (A little slower)"]
        replies = [
            ("ತುಂಬಾ ಒಳ್ಳೆಯ ಮಾತು! ನಾನು ಇದನ್ನು ಈಗಲೇ ಸಿದ್ಧಪಡಿಸುತ್ತೇನೆ. ಬೇರೇನಾದರೂ ಬೇಕೇ?", "Tumba olleya maatu! Naanu idannu eegale siddhapadisuttene. Berenadaru beke?", "Very good! I will prepare this right away. Would you like anything else?"),
            ("ಖಂಡಿತವಾಗಿ, ನಿಮ್ಮ ಆದೇಶವನ್ನು ಸ್ವೀಕರಿಸಲಾಗಿದೆ. ಇನ್ನೇನು ಸಹಾಯ ಬೇಕು?", "Khanditavaagi, nimma aadeshavannu sweekarisalaagide. Innenhu sahaaya beku?", "Certainly, your order has been placed. Any other assistance needed?"),
            ("ಧನ್ಯವಾದಗಳು! ನೀವು ನಮ್ಮಲ್ಲಿಗೆ ಬಂದಿದ್ದು ತುಂಬಾ ಖುಷಿಯಾಯಿತು.", "Dhanyavaadagalu! Neevu nammallige bandiddu tumba khushiyaayitu.", "Thank you! Very glad you visited us today.")
        ]
    elif lang_code == "te":
        pronunciation_tips = ["Pay attention to elongated vowels like 'ఆ' vs short 'అ'."]
        vocab_suggestions = ["ధన్యవాదాలు (Thank you)", "ఖచ్చితంగా (Definitely)", "తప్పకుండా (Sure)"]
        replies = [
            ("చాలా మంచిది! నేను వెంటనే సిద్ధం చేస్తాను. ఇంకేమైనా కావాలా?", "Chaala manchidi! Nenu ventane siddham chestaanu. Inkemaina kaavaala?", "Very good! I will prepare it immediately. Anything else?"),
            ("ఖచ్చితంగా! మీ ఆర్డర్ తీసుకున్నాము.", "Kachchitanga! Mee order theesukunnaamu.", "Certainly! We have taken your order.")
        ]
    elif lang_code == "mr":
        pronunciation_tips = ["Keep your nasal sounds clear in words like 'आहेत'."]
        vocab_suggestions = ["धन्यवाद (Thank you)", "नक्कीच (Certainly)", "आणखी काही (Anything else)"]
        replies = [
            ("खूप छान! मी लगेच घेऊन येतो. आणखी काही हवे का?", "Khoop chhaan! Mee lagech gheun yeto. Aankhi kaahi have kaa?", "Wonderful! I will bring it shortly. Anything else?"),
            ("नक्कीच! आपले काम लगेच पूर्ण होईल.", "Nakkich! Aaple kaam lagech poorna hoil.", "Certainly! Your request will be fulfilled.")
        ]
    elif lang_code == "hi":
        pronunciation_tips = ["Ensure distinction between voiced and unvoiced aspirated sounds."]
        vocab_suggestions = ["धन्यवाद (Thank you)", "ज़रूर (Sure)", "और कुछ? (Anything else?)"]
        replies = [
            ("बहुत बढ़िया! मैं इसे अभी तैयार करवाता हूँ। क्या आपको कुछ और भी चाहिए?", "Bahut badhiya! Main ise abhi taiyaar karvaata hoon. Kya aapko kuch aur bhi chaahiye?", "Great! I'll get this ready right away. Do you need anything else?"),
            ("बिल्कुल, आपका आदेश लिख लिया गया है।", "Bilkul, aapka aadesh likh liya gaya hai.", "Certainly, your order has been noted.")
        ]
    else: # English
        pronunciation_tips = ["Keep your sentence rhythm natural with connected speech."]
        vocab_suggestions = ["Certainly", "Could you recommend", "I appreciate your help"]
        replies = [
            ("Splendid choice! I'll get that prepared right away for you. Would you like anything else?", "Splendid choice!", "Splendid choice! Would you like anything else?"),
            ("Certainly! Is there anything else I can help you with today?", "Certainly!", "Certainly! Anything else?")
        ]

    turn_num = max(1, session.total_turns or 1)
    reply_idx = (turn_num - 1) % len(replies)
    next_reply = replies[reply_idx]

    transcript.append({"sender": "user", "text": user_text, "score": turn_score})
    transcript.append({"sender": "ai", "text": next_reply[0], "phonetic": next_reply[1], "translation": next_reply[2]})

    session.total_turns += 1
    session.transcript_json = json.dumps(transcript)
    session.grammar_score = (session.grammar_score + turn_score) / 2 if session.grammar_score > 0 else turn_score
    session.pronunciation_score = (session.pronunciation_score + 88.0) / 2 if session.pronunciation_score > 0 else 88.0
    session.vocabulary_score = (session.vocabulary_score + (90.0 if matched_words else 75.0)) / 2
    db.commit()

    return schemas.ConversationRespondResponse(
        session_id=session.id,
        target_language_code=lang_code,
        ai_reply=next_reply[0],
        ai_audio_text=next_reply[0],
        phonetic=next_reply[1],
        translation=next_reply[2],
        grammar_correction=grammar_correction,
        pronunciation_tips=pronunciation_tips,
        vocabulary_suggestions=vocab_suggestions,
        current_turn=session.total_turns,
        turn_score=turn_score
    )

@router.post("/end", response_model=schemas.ConversationEndResponse)
@router.post("/end/", response_model=schemas.ConversationEndResponse)
def end_conversation(
    req: schemas.ConversationEndRequest,
    current_learner: models.Learner = Depends(dependencies.get_current_learner_or_fallback),
    db: Session = Depends(database.get_db)
):
    session = db.query(models.ConversationSession).filter(
        models.ConversationSession.id == req.session_id,
        models.ConversationSession.learner_id == current_learner.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Conversation session not found")

    session.is_completed = True
    composite = round((session.grammar_score + session.pronunciation_score + session.vocabulary_score) / 3, 1)
    if composite == 0.0:
        composite = 82.5

    xp_earned = 35 + min(15, session.total_turns * 5)
    gems_earned = 15

    gamification.award_xp_and_gems(current_learner, xp=xp_earned, gems=gems_earned, db=db)
    gamification.update_streak(current_learner, db=db)

    db.commit()

    transcript = json.loads(session.transcript_json) if session.transcript_json else []

    return schemas.ConversationEndResponse(
        session_id=session.id,
        composite_score=composite,
        grammar_score=round(session.grammar_score, 1) or 85.0,
        pronunciation_score=round(session.pronunciation_score, 1) or 88.0,
        vocabulary_score=round(session.vocabulary_score, 1) or 80.0,
        total_turns=session.total_turns,
        xp_earned=xp_earned,
        gems_earned=gems_earned,
        transcript=transcript
    )
