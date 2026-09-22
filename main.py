import os
from fastapi import FastAPI, Depends
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import database
from database import engine, SessionLocal
import models
from seed_data import seed_initial_database
from routers import (
    auth_router,
    learner_router,
    language_router,
    course_router,
    assessment_router,
    progress_router,
    recommendation_router,
    admin_router,
    review_router,
    db_router,
    learning_path_router,
    diagnostic_router,
    conversation_router,
    story_router,
    adventure_router,
    practice_hub_router,
    social_router,
    league_router,
    guidebook_router,
    explain_router,
    speech_router,
    achievement_router,
    report_router
)

app = FastAPI(title="Literacy Assistance API & Backend Portal")

@app.on_event("startup")
def startup_event():
    try:
        database.ensure_tables_created()
    except Exception as e:
        print(f"[WARN] Startup seed exception: {e}")


# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
@app.get("/api/health")
def health_check():
    """Health check endpoint for cloud hosting platforms (Render, Vercel, Railway)."""
    return {"status": "ok", "service": "NeoLearner Backend API"}

# Register Routers
app.include_router(auth_router.router)
app.include_router(learner_router.router)
app.include_router(language_router.router)
app.include_router(course_router.router)
app.include_router(assessment_router.router)
app.include_router(progress_router.router)
app.include_router(recommendation_router.router)
app.include_router(admin_router.router)
app.include_router(review_router.router)
app.include_router(db_router.router)
app.include_router(learning_path_router.router)
app.include_router(diagnostic_router.router)
app.include_router(conversation_router.router)
app.include_router(story_router.router)
app.include_router(adventure_router.router)
app.include_router(practice_hub_router.router)
app.include_router(social_router.router)
app.include_router(league_router.router)
app.include_router(guidebook_router.router)
app.include_router(explain_router.router)
app.include_router(speech_router.router)
app.include_router(achievement_router.router)
app.include_router(report_router.router)

@app.get("/api/insights")
def get_project_insights(db: Session = Depends(database.get_db)):
    """Public API returning project metrics, architectural insights, and platform statistics."""
    total_learners = db.query(models.Learner).count()
    languages = db.query(models.Language).all()
    courses_count = db.query(models.Course).count()
    topics_count = db.query(models.Topic).count()
    lessons_count = db.query(models.Lesson).count()
    assessments_count = db.query(models.Assessment).count()
    questions_count = db.query(models.Question).count()
    vocabulary_count = db.query(models.Vocabulary).count()
    achievements_count = db.query(models.AchievementDefinition).count()
    stories_count = db.query(models.InteractiveStory).count()
    adventures_count = db.query(models.TextAdventureScenario).count()
    
    return {
        "project_name": "LinguaLearn — Intelligent Literacy & Language Assistance Platform",
        "tagline": "Empowering foundational reading, phonics, CEFR proficiency, and gamified multi-lingual education",
        "stats": {
            "total_learners": total_learners,
            "supported_languages": len(languages),
            "courses_count": courses_count,
            "topics_count": topics_count,
            "lessons_count": lessons_count,
            "assessments_count": assessments_count,
            "questions_count": questions_count,
            "vocabulary_words": vocabulary_count,
            "achievements_count": achievements_count,
            "stories_count": stories_count,
            "adventures_count": adventures_count,
            "exercise_types_count": 7
        },
        "languages": [{"name": l.name, "code": l.code, "native_name": l.native_name} for l in languages],
        "exercise_types": [
            {"type": "multiple_choice", "name": "Multiple Choice Quiz"},
            {"type": "translation", "name": "Sentence Translation"},
            {"type": "word_order", "name": "Word Order Unscramble"},
            {"type": "listening", "name": "Audio Listening Comprehension"},
            {"type": "speaking", "name": "Voice Pronunciation Assessment"},
            {"type": "match_pairs", "name": "Vocabulary Matching Pairs"},
            {"type": "fill_in_the_blank", "name": "Fill in the Blank"}
        ],
        "core_innovations": [
            {
                "title": "AI Proficiency Predictor",
                "badge": "Machine Learning",
                "description": "Continuously computes learner CEFR rating (A0 to C1) and predicts benchmark literacy placement."
            },
            {
                "title": "SuperMemo-2 Spaced Repetition (SRS)",
                "badge": "Memory Engine",
                "description": "Calculates optimal review intervals, ease factor multiplier, and repetition counts for vocabulary retention."
            },
            {
                "title": "Server-Side Gamification Engine",
                "badge": "Engagement",
                "description": "Protects XP, Gems, Hearts, Streaks, double-or-nothing wagers, and 10 League Tiers from client manipulation."
            },
            {
                "title": "Web Speech Audio & Pronunciation",
                "badge": "Phonics & Speech",
                "description": "Integrated SpeechRecognition and SpeechSynthesis with real-time fluency scoring and fallback matching."
            },
            {
                "title": "Interactive Stories & AI Adventures",
                "badge": "Immersion",
                "description": "Branching narrative choices and generative AI roleplay scenarios in regional languages."
            },
            {
                "title": "Universal Admin Portal & DB Explorer",
                "badge": "Control & Ops",
                "description": "Live SQLAlchemy database schema visualization and row-level CRUD studio for all database entities."
            }
        ]
    }


TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "templates", "index.html")
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")

if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/app", response_class=HTMLResponse)
    def read_frontend_app():
        index_file = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return "<h1>Frontend Application</h1>"

@app.get("/", response_class=HTMLResponse)
@app.get("/admin", response_class=HTMLResponse)
def read_backend_portal():
    if os.path.exists(TEMPLATE_PATH):
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Literacy Assistance Backend UI Portal</h1>"
