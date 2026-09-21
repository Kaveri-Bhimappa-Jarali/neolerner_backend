import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
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

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Seed initial languages and courses
try:
    db_session = SessionLocal()
    seed_initial_database(db_session)
    db_session.close()
except Exception as err:
    print(f"[WARN] Database seeding warning: {err}")

app = FastAPI(title="Literacy Assistance API & Backend Portal")

@app.on_event("startup")
def startup_event():
    try:
        db = SessionLocal()
        seed_initial_database(db)
        db.close()
    except Exception as e:
        print(f"[WARN] Startup seed exception: {e}")

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
