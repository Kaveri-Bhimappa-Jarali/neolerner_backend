# LinguaLearn — Development Rules & Architecture Decisions

This document outlines the architecture, coding standards, and development rules for **LinguaLearn**, a gamified language-learning platform.

---

## 1. Technology Stack

* **Frontend**: React (Vite SPA), CSS Variables + Tailwind Utility classes, Lucide icons, HTML5 Web Speech API (SpeechRecognition & SpeechSynthesis).
* **Backend**: FastAPI (Python), SQLAlchemy ORM, Uvicorn server.
* **Database**: SQLite (absolute path resolution to `backend/literacy.db` to prevent path collisions).
* **Authentication**: OAuth2 Password Bearer with JWT tokens.
* **Validation**: Pydantic v2 (backend schemas), React-controlled forms.

---

## 2. Architecture & Design Principles

### Reusable Lesson Engine
* Supports seven exercise types: `multiple_choice`, `translation`, `word_order`, `listening`, `speaking`, `match_pairs`, and `fill_in_the_blank`.
* Exercises are rendered dynamically based on type.
* Browser Web Speech APIs are leveraged for audio playback (`SpeechSynthesis`) and speech input (`SpeechRecognition`), with graceful default fallback for unsupported environments.

### Spaced Repetition (SRS)
* Employs a simplified SM-2 (SuperMemo-2) algorithm.
* Tracks `interval` (days), `ease_factor`, and `repetitions` for each vocab word.
* Prioritizes review items where the next review date is in the past.

### Gamification & State Consistency
* Streaks, XP, Gems, and Hearts updates are validated and calculated **server-side** to prevent client tampering.
* The frontend context updates user state on login, registration, and whenever a lesson/practice session is completed.

---

## 3. Directory Structure

```
Literacy-Assistance/
├── backend/
│   ├── database.py              # SQLite connection config
│   ├── models.py                # SQLAlchemy DB models
│   ├── schemas.py               # Pydantic validation schemas
│   ├── main.py                  # FastAPI entry point
│   ├── auth.py                  # Hashing & JWT utility functions
│   ├── gamification.py          # Streaks, XP, & Gems engine
│   ├── srs.py                   # Spaced repetition logic
│   └── routers/                 # API endpoint routers
│       ├── auth_router.py
│       ├── course_router.py
│       ├── progress_router.py
│       ├── learner_router.py
│       └── review_router.py     # SRS and mistake review routes
├── frontend/
│   ├── src/
│   │   ├── components/          # Reusable UI widgets
│   │   │   ├── Auth/            # Register, Login, Onboarding
│   │   │   ├── Dashboard/       # Quests, Leaderboard
│   │   │   ├── Lessons/         # Lesson Engine, Practice
│   │   │   ├── Profile/         # Stats, Achievements
│   │   │   └── Review/          # Spaced Repetition, Mistakes
│   │   └── utils/               # Translations & Audio utilities
└── AGENTS.md                    # This rules file
```

---

## 4. Coding & Security Rules

1. **Controlled Components**: Every React form input and select tag must be a controlled component bound to React state.
2. **Absolute DB Paths**: The database URL must always resolve to an absolute path targeting `backend/literacy.db`.
3. **No Secrets in Code**: Secrets and keys must be loaded from `.env` environment variables.
4. **Data Integrity**: Never store plain-text passwords. Use bcrypt/argon2 hashing.
5. **FastAPI Slash Mapping**: Always register routes with both trailing and non-trailing slashes (or empty routes) to avoid CORS redirect failures.
6. **Graceful Fallbacks**: Audio playback and voice recognition must check availability and fallback silently to standard text-matching without breaking the quiz flow.
