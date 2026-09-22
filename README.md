# Literacy Assistance Platform 📚

A comprehensive full-stack literacy and language learning web application built with **FastAPI** (Python) and **React** (Vite). Features structured course modules, interactive phonics exercises, automated quiz scoring, personalized recommendations, and a visual backend database admin portal.

---

## 🌟 Features

- **11 Core Database Entities**: Fully modeled relational architecture covering Learners, Languages, Courses, Topics, Lessons, Assessments, Questions, Answers, Assessment Results, Learning Progress, and Recommendations.
- **Visual Backend Portal (`http://localhost:8000/`)**: Live database inspector served directly by FastAPI with real-time row searching, schema statistics, and CRUD management.
- **Student Frontend Application (`http://localhost:5173/`)**: Sleek dark-mode interface for exploring courses, reading lessons, taking interactive quizzes, and tracking learner progress.
- **Automated Quiz Engine**: Instant score calculation, passing thresholds, answer feedback explanations, and database result recording.
- **RESTful API**: OpenAPI (Swagger) documentation available at `/docs`.

---

## 🏗️ Technology Stack

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy, Pydantic v2, SQLite / PostgreSQL, Uvicorn, Passlib, Python-JOSE.
- **Frontend**: React 19, Vite, React Router v7, Lucide Icons, Vanilla CSS Design Tokens.

---

## 📁 Repository Structure

```
Literacy-Assistance/
├── backend/
│   ├── database.py             # SQLAlchemy engine & session setup
│   ├── models.py               # 11 SQLAlchemy Database Models & Enums
│   ├── schemas.py              # Pydantic validation & response schemas
│   ├── dependencies.py         # Auth & session dependencies
│   ├── main.py                 # FastAPI application & router bindings
│   ├── verify_db.py            # Integration test suite for DB entities
│   ├── routers/                # API router modules
│   │   ├── auth_router.py
│   │   ├── learner_router.py
│   │   ├── language_router.py
│   │   ├── course_router.py
│   │   ├── assessment_router.py
│   │   ├── progress_router.py
│   │   ├── recommendation_router.py
│   │   └── admin_router.py
│   └── templates/
│       └── index.html          # Backend visual Web UI portal
├── frontend/
│   ├── src/
│   │   ├── components/         # Course, Lesson, Quiz, Dashboard components
│   │   ├── context/            # AuthContext provider
│   │   ├── api/                # Axios instance
│   │   ├── App.jsx             # Main router configuration
│   │   └── index.css           # Design tokens & styling
│   ├── public/                 # Public assets
│   └── package.json            # Node.js dependencies
├── seed.py                     # Initial database seeding script
├── docker-compose.yml          # Docker composition config
└── README.md                   # Project documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ & npm

### 2. Backend Setup
```bash
# Navigate to project directory
cd Literacy-Assistance

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Run automated database verification tests
python backend/verify_db.py

# Seed database with sample courses & records
python seed.py

# Start FastAPI server
cd backend
python -m uvicorn main:app --reload --port 8000
```
- **Backend Admin Portal**: Open `http://localhost:8000/` in browser.
- **OpenAPI Swagger Docs**: Open `http://localhost:8000/docs` in browser.

### 3. Frontend Setup
```bash
# In a new terminal, navigate to frontend/
cd frontend

# Install npm dependencies
npm install

# Start Vite development server
npm run dev
```
- Open `http://localhost:5173` in your browser.

---

## 🗄️ Database Entity Schema (11 Entities)

1. **Learner**: User profile, preferences, proficiency level.
2. **Language**: System supported languages (English, Spanish, French, German, Japanese).
3. **Course**: Educational course structured by target language and level.
4. **Topic**: Modular sections within a course.
5. **Lesson**: Learning units with markdown content and estimated duration.
6. **Assessment**: Lesson quiz/test with pass percentage threshold.
7. **Question**: Assessment questions (multiple choice, fill-in-blank, true/false).
8. **Answer**: Answer choices with correctness flags & feedback explanations.
9. **Assessment Result**: Scores and completion status for learner attempts.
10. **Learning Progress**: Tracks lesson completion status per learner.
11. **Recommendation**: Personalized course suggestions generated for learners.

---

## 🧪 Verification & Testing

Run automated database verification across all 11 entities:
```bash
python backend/verify_db.py
```
Output:
```
=== Starting Database Entity Verification ===
[OK] 1. Tables created successfully.
[OK] 2. Language entity verified.
[OK] 3. Learner entity verified.
[OK] 4. Course entity verified.
[OK] 5. Topic entity verified.
[OK] 6. Lesson entity verified.
[OK] 7. Assessment entity verified.
[OK] 8. Question entity verified.
[OK] 9. Answer entity verified.
[OK] 10. AssessmentResult entity verified.
[OK] 11. LearningProgress entity verified.
[OK] 12. Recommendation entity verified.
[OK] 13. Hierarchical relationship tree navigation verified.
=== ALL 11 ENTITIES VERIFIED SUCCESSFULLY ===
```

Build production frontend bundle:
```bash
cd frontend
npm run build
```

---

## 📄 License
This project is licensed under the MIT License.
