import os
import sys

# Ensure backend directory is in sys.path for direct uvicorn execution from root or backend directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi import FastAPI, Depends, Request
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

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://localhost:4173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:4173",
        "https://neolearner-frontend.vercel.app",
        "https://neolearner-frontend-git-main-kaverijarali22-3383s-projects.vercel.app"
    ],
    allow_origin_regex=r"https?://.*(vercel\.app|render\.com|localhost|127\.0\.0\.1).*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HEALTH_METHODS = ["GET", "HEAD", "OPTIONS"]

@app.api_route("/", methods=HEALTH_METHODS)
@app.api_route("/health", methods=HEALTH_METHODS, include_in_schema=False)
@app.api_route("/api/health", methods=HEALTH_METHODS, include_in_schema=False)
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
    total_learners = db.query(models.Learner).count()
    languages = db.query(models.Language).all()
    courses_count = db.query(models.Course).count()
    topics_count = db.query(models.Topic).count()
    lessons_count = db.query(models.Lesson).count()
    assessments_count = db.query(models.Assessment).count()
    questions_count = db.query(models.Question).count()
    vocabulary_count = db.query(models.Vocabulary).count()
    achievements_count = db.query(models.AchievementDefinition).count()
    stories_count = db.query(models.Story).count()
    adventures_count = db.query(models.Adventure).count()
    
    return {
        "project_name": "LinguaLearn — Intelligent Literacy & Language Assistance Platform",
        "stats": {
            "total_learners": total_learners,
            "supported_languages": len(languages),
            "courses_count": courses_count
        }
    }


TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "templates", "index.html")


@app.get("/admin", response_class=HTMLResponse)
def read_backend_portal():
    if os.path.exists(TEMPLATE_PATH):
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Literacy Assistance Backend UI Portal</h1>"
