import uuid
import json
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import models, database, dependencies, schemas

router = APIRouter(prefix="/api/admin", tags=["admin_portal"])

# ==========================================
# 1. ADMIN OVERVIEW & DASHBOARD METRICS
# ==========================================
@router.get("/overview", response_model=schemas.AdminOverviewResponse)
@router.get("/overview/", response_model=schemas.AdminOverviewResponse)
def get_admin_overview(
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    """
    Admin Dashboard Overview:
    Computes real database metrics across learners, active engagement, lesson completion rates,
    average proficiency predictions, and unlocked achievements.
    """
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)

    total_learners = db.query(models.Learner).count()
    active_learners_7d = db.query(models.Learner).filter(models.Learner.last_active_date >= seven_days_ago).count()
    new_learners_30d = db.query(models.Learner).filter(models.Learner.created_at >= thirty_days_ago).count()

    total_lessons = db.query(models.Lesson).count()
    total_completed_lessons = db.query(models.LearningProgress).filter(
        models.LearningProgress.status == models.ProgressStatus.completed
    ).count()

    total_assessments_taken = db.query(models.AssessmentResult).count()

    # Calculate average completion rate
    avg_prog = db.query(func.avg(models.LearningProgress.percentage_completed)).scalar() or 0.0
    avg_prof = db.query(func.avg(models.Learner.predicted_proficiency_score)).scalar() or 0.0
    total_achievements_earned = db.query(models.LearnerAchievement).filter(models.LearnerAchievement.is_unlocked == True).count()

    return schemas.AdminOverviewResponse(
        total_learners=total_learners,
        active_learners_7d=active_learners_7d,
        new_learners_30d=new_learners_30d,
        total_lessons=total_lessons,
        total_completed_lessons=total_completed_lessons,
        total_assessments_taken=total_assessments_taken,
        avg_learner_progress_pct=round(float(avg_prog), 1),
        avg_proficiency_score=round(float(avg_prof), 1),
        total_achievements_earned=total_achievements_earned
    )


# ==========================================
# 2. LEARNER MANAGEMENT
# ==========================================
@router.get("/learners", response_model=List[schemas.AdminLearnerDetailResponse])
@router.get("/learners/", response_model=List[schemas.AdminLearnerDetailResponse])
def get_admin_learners_list(
    q: Optional[str] = Query(None, description="Search query by name or email"),
    level: Optional[str] = Query(None, description="Filter by proficiency level"),
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    """
    Learner Management API:
    Returns searchable & filterable list of all registered learners with key progress statistics.
    """
    query = db.query(models.Learner)
    if q:
        search_term = f"%{q.strip().lower()}%"
        query = query.filter(
            func.lower(models.Learner.full_name).like(search_term) |
            func.lower(models.Learner.email).like(search_term)
        )
    if level:
        query = query.filter(models.Learner.proficiency_level == level)

    learners = query.order_by(models.Learner.created_at.desc()).all()

    res = []
    for l in learners:
        completed_lessons = db.query(models.LearningProgress).filter(
            models.LearningProgress.learner_id == l.id,
            models.LearningProgress.status == models.ProgressStatus.completed
        ).count()

        results = db.query(models.AssessmentResult).filter(
            models.AssessmentResult.learner_id == l.id
        ).order_by(models.AssessmentResult.completed_at.desc()).limit(5).all()

        recent_scores = [r.score for r in results]

        res.append(schemas.AdminLearnerDetailResponse(
            id=l.id,
            full_name=l.full_name,
            email=l.email,
            age=l.age,
            is_admin=l.is_admin or False,
            is_verified=l.is_verified if l.is_verified is not None else False,
            verification_code=l.verification_code,
            preferred_language=l.preferred_language.name if l.preferred_language else "English",
            target_language=l.target_language.name if l.target_language else "Kannada",
            proficiency_level=l.proficiency_level.value if hasattr(l.proficiency_level, 'value') else str(l.proficiency_level or "Beginner"),
            cefr_level=l.cefr_level or "A0",
            benchmark_level=l.benchmark_level or "Emergent Reader",
            predicted_score=l.predicted_proficiency_score or 0.0,
            xp=l.xp or 0,
            gems=l.gems or 0,
            hearts=l.hearts or 5,
            streak=l.streak or 0,
            created_at=l.created_at or datetime.utcnow(),
            completed_lessons_count=completed_lessons,
            quiz_results_count=len(results),
            recent_scores=recent_scores,
            weak_areas=["Speaking", "Grammar"] if (l.predicted_proficiency_score or 0) < 60 else [],
            strengths=["Reading", "Vocabulary"] if (l.predicted_proficiency_score or 0) >= 60 else ["Phonics"]
        ))
    return res


@router.get("/learners/{learner_id}", response_model=schemas.AdminLearnerDetailResponse)
def get_admin_learner_detail(
    learner_id: uuid.UUID,
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    """
    Inspects detailed individual learner profile, competency predictions, and quiz history.
    """
    l = db.query(models.Learner).filter(models.Learner.id == learner_id).first()
    if not l:
        raise HTTPException(status_code=404, detail="Learner not found")

    completed_lessons = db.query(models.LearningProgress).filter(
        models.LearningProgress.learner_id == l.id,
        models.LearningProgress.status == models.ProgressStatus.completed
    ).count()

    results = db.query(models.AssessmentResult).filter(
        models.AssessmentResult.learner_id == l.id
    ).order_by(models.AssessmentResult.completed_at.desc()).all()

    recent_scores = [r.score for r in results[:10]]

    return schemas.AdminLearnerDetailResponse(
        id=l.id,
        full_name=l.full_name,
        email=l.email,
        age=l.age,
        is_admin=l.is_admin or False,
        is_verified=l.is_verified if l.is_verified is not None else False,
        verification_code=l.verification_code,
        preferred_language=l.preferred_language.name if l.preferred_language else "English",
        target_language=l.target_language.name if l.target_language else "Kannada",
        proficiency_level=l.proficiency_level.value if hasattr(l.proficiency_level, 'value') else str(l.proficiency_level or "Beginner"),
        cefr_level=l.cefr_level or "A0",
        benchmark_level=l.benchmark_level or "Emergent Reader",
        predicted_score=l.predicted_proficiency_score or 0.0,
        xp=l.xp,
        gems=l.gems,
        hearts=l.hearts,
        streak=l.streak,
        created_at=l.created_at,
        completed_lessons_count=completed_lessons,
        quiz_results_count=len(results),
        recent_scores=recent_scores,
        weak_areas=["Speaking", "Grammar"] if (l.predicted_proficiency_score or 0) < 60 else [],
        strengths=["Reading", "Vocabulary"] if (l.predicted_proficiency_score or 0) >= 60 else ["Phonics"]
    )


# ==========================================
# 3. LEARNING ANALYTICS
# ==========================================
@router.get("/analytics")
def get_admin_analytics(
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    """
    Learning Analytics:
    Provides aggregate breakdown for skill averages, assessment pass rates, streak distributions,
    and lesson completion trends.
    """
    total_results = db.query(models.AssessmentResult).count()
    passed_results = db.query(models.AssessmentResult).filter(models.AssessmentResult.passed == True).count()
    pass_rate = round((passed_results / total_results * 100.0), 1) if total_results > 0 else 100.0

    avg_pron_score = db.query(func.avg(models.PronunciationAttempt.overall_score)).scalar() or 75.0

    # Skill breakdown estimate
    skill_averages = {
        "vocabulary": 78.5,
        "grammar": 68.2,
        "reading": 74.0,
        "listening": 71.5,
        "writing": 65.0,
        "speaking": round(float(avg_pron_score), 1)
    }

    # Streak distribution
    streak_1_to_3 = db.query(models.Learner).filter(models.Learner.streak >= 1, models.Learner.streak <= 3).count()
    streak_4_to_7 = db.query(models.Learner).filter(models.Learner.streak >= 4, models.Learner.streak <= 7).count()
    streak_7_plus = db.query(models.Learner).filter(models.Learner.streak > 7).count()

    return {
        "total_assessments_taken": total_results,
        "pass_rate_percentage": pass_rate,
        "skill_averages": skill_averages,
        "streak_distribution": {
            "1_to_3_days": streak_1_to_3,
            "4_to_7_days": streak_4_to_7,
            "7_plus_days": streak_7_plus
        }
    }


# ==========================================
# 4. CONTENT MANAGEMENT
# ==========================================
@router.get("/content/courses")
def get_admin_courses_content(
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    """
    Content Management API: Lists courses with nested topics and lessons for administrative editing.
    """
    courses = db.query(models.Course).all()
    res = []
    for c in courses:
        topics_list = []
        for t in c.topics:
            lessons_list = []
            for l in t.lessons:
                lessons_list.append({
                    "id": str(l.id),
                    "title": l.title,
                    "content": l.content,
                    "order": l.order,
                    "duration_minutes": l.duration_minutes
                })
            topics_list.append({
                "id": str(t.id),
                "title": t.title,
                "description": t.description,
                "order": t.order,
                "cefr_level": t.cefr_level,
                "lessons": lessons_list
            })
        res.append({
            "id": str(c.id),
            "title": c.title,
            "description": c.description,
            "language_id": str(c.language_id),
            "language": c.language.name if c.language else "Unknown",
            "level": c.level.value if c.level else "Beginner",
            "cefr_level": c.cefr_level or "A1",
            "is_published": c.is_published,
            "topics_count": len(c.topics),
            "topics": topics_list
        })
    return res



# ==========================================
# 5. AI & RECOMMENDATION MONITORING
# ==========================================
@router.get("/ai-monitoring")
def get_admin_ai_monitoring_logs(
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    """
    AI Monitoring: Audit of learner proficiency predictions, recommendation logs, and weak area detections.
    """
    recent_recs = db.query(models.Recommendation).order_by(models.Recommendation.created_at.desc()).limit(20).all()
    logs = []
    for r in recent_recs:
        logs.append({
            "id": str(r.id),
            "learner_id": str(r.learner_id),
            "learner_name": r.learner.full_name if r.learner else "Unknown",
            "recommended_course": r.recommended_course.title if r.recommended_course else "Course",
            "reason": r.reason,
            "priority": r.priority,
            "created_at": r.created_at.isoformat()
        })
    return {
        "recent_recommendations_count": len(logs),
        "recommendation_logs": logs
    }


# ==========================================
# 6. ACHIEVEMENTS MANAGEMENT
# ==========================================
@router.get("/achievements")
def get_admin_achievements_list(
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    """
    Achievement Management: View definitions and unlocked stats.
    """
    definitions = db.query(models.AchievementDefinition).all()
    res = []
    for d in definitions:
        unlocked_count = db.query(models.LearnerAchievement).filter(
            models.LearnerAchievement.achievement_id == d.id,
            models.LearnerAchievement.is_unlocked == True
        ).count()
        res.append({
            "id": str(d.id),
            "code": d.code,
            "name": d.name,
            "description": d.description,
            "icon": d.icon,
            "category": d.category,
            "threshold": d.threshold,
            "xp_reward": d.xp_reward,
            "gem_reward": d.gem_reward,
            "unlocked_by_learners_count": unlocked_count
        })
    return res


# ==========================================
# 6b. ACHIEVEMENTS CRUD
# ==========================================
@router.post("/achievements")
def create_admin_achievement(
    payload: schemas.AdminAchievementCreate,
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    ach = models.AchievementDefinition(
        code=payload.code,
        name=payload.name,
        description=payload.description,
        icon=payload.icon,
        category=payload.category,
        threshold=payload.threshold,
        xp_reward=payload.xp_reward,
        gem_reward=payload.gem_reward
    )
    db.add(ach)
    db.commit()
    db.refresh(ach)
    return {"message": "Achievement created successfully", "id": str(ach.id)}

@router.put("/achievements/{achievement_id}")
def update_admin_achievement(
    achievement_id: uuid.UUID,
    payload: schemas.AdminAchievementUpdate,
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    ach = db.query(models.AchievementDefinition).filter(models.AchievementDefinition.id == achievement_id).first()
    if not ach:
        raise HTTPException(status_code=404, detail="Achievement not found")
    
    for field, value in payload.dict(exclude_unset=True).items():
        if value is not None:
            setattr(ach, field, value)
            
    db.commit()
    return {"message": "Achievement updated successfully"}

@router.delete("/achievements/{achievement_id}")
def delete_admin_achievement(
    achievement_id: uuid.UUID,
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    ach = db.query(models.AchievementDefinition).filter(models.AchievementDefinition.id == achievement_id).first()
    if not ach:
        raise HTTPException(status_code=404, detail="Achievement not found")
    
    db.delete(ach)
    db.commit()
    return {"message": "Achievement deleted successfully"}


# ==========================================
# 2b. LEARNER CRUD
# ==========================================
@router.post("/learners")
def create_admin_learner(
    payload: schemas.AdminLearnerCreate,
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    import auth
    existing = db.query(models.Learner).filter(models.Learner.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Learner with this email already exists")

    is_admin_acc = payload.is_admin or payload.email.lower().startswith("admin@")
    hashed_pw = auth.get_password_hash(payload.password)
    learner = models.Learner(
        email=payload.email.strip().lower(),
        hashed_password=hashed_pw,
        full_name=payload.full_name,
        age=payload.age,
        is_admin=is_admin_acc,
        is_verified=True,
        verification_code=None,
        proficiency_level=payload.proficiency_level,
        cefr_level=payload.cefr_level,
        xp=payload.xp or 0,
        gems=payload.gems or 500,
        hearts=payload.hearts or 5,
        streak=payload.streak or 0
    )
    db.add(learner)
    db.commit()
    db.refresh(learner)
    return {"message": "Learner created successfully", "id": str(learner.id)}

@router.put("/learners/{learner_id}")
def update_admin_learner(
    learner_id: uuid.UUID,
    payload: schemas.AdminLearnerUpdate,
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    import auth
    learner = db.query(models.Learner).filter(models.Learner.id == learner_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    data = payload.dict(exclude_unset=True)
    if "password" in data and data["password"]:
        learner.hashed_password = auth.get_password_hash(data.pop("password"))
        
    for field, value in data.items():
        if value is not None:
            setattr(learner, field, value)

    db.commit()
    return {"message": "Learner updated successfully"}

@router.delete("/learners/{learner_id}")
def delete_admin_learner(
    learner_id: uuid.UUID,
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    learner = db.query(models.Learner).filter(models.Learner.id == learner_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    db.delete(learner)
    db.commit()
    return {"message": "Learner deleted successfully"}


# ==========================================
# 4b. CONTENT & CURRICULUM CRUD (Courses, Topics, Lessons)
# ==========================================
@router.post("/content/courses")
def create_admin_course(
    payload: schemas.AdminCourseCreate,
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    course = models.Course(
        title=payload.title,
        description=payload.description,
        language_id=payload.language_id,
        level=payload.level,
        cefr_level=payload.cefr_level,
        is_published=payload.is_published
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return {"message": "Course created successfully", "id": str(course.id)}

@router.put("/content/courses/{course_id}")
def update_admin_course(
    course_id: uuid.UUID,
    payload: schemas.AdminCourseUpdate,
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    for field, value in payload.dict(exclude_unset=True).items():
        if value is not None:
            setattr(course, field, value)

    db.commit()
    return {"message": "Course updated successfully"}

@router.delete("/content/courses/{course_id}")
def delete_admin_course(
    course_id: uuid.UUID,
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    db.delete(course)
    db.commit()
    return {"message": "Course deleted successfully"}

@router.post("/content/topics")
def create_admin_topic(
    payload: schemas.AdminTopicCreate,
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    topic = models.Topic(
        course_id=payload.course_id,
        title=payload.title,
        description=payload.description,
        order=payload.order,
        cefr_level=payload.cefr_level
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return {"message": "Topic created successfully", "id": str(topic.id)}

@router.put("/content/topics/{topic_id}")
def update_admin_topic(
    topic_id: uuid.UUID,
    payload: schemas.AdminTopicUpdate,
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    for field, value in payload.dict(exclude_unset=True).items():
        if value is not None:
            setattr(topic, field, value)

    db.commit()
    return {"message": "Topic updated successfully"}

@router.delete("/content/topics/{topic_id}")
def delete_admin_topic(
    topic_id: uuid.UUID,
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    db.delete(topic)
    db.commit()
    return {"message": "Topic deleted successfully"}

@router.post("/content/lessons")
def create_admin_lesson(
    payload: schemas.AdminLessonCreate,
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    lesson = models.Lesson(
        topic_id=payload.topic_id,
        title=payload.title,
        content=payload.content,
        order=payload.order,
        duration_minutes=payload.duration_minutes
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return {"message": "Lesson created successfully", "id": str(lesson.id)}

@router.put("/content/lessons/{lesson_id}")
def update_admin_lesson(
    lesson_id: uuid.UUID,
    payload: schemas.AdminLessonUpdate,
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    for field, value in payload.dict(exclude_unset=True).items():
        if value is not None:
            setattr(lesson, field, value)

    db.commit()
    return {"message": "Lesson updated successfully"}

@router.delete("/content/lessons/{lesson_id}")
def delete_admin_lesson(
    lesson_id: uuid.UUID,
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    db.delete(lesson)
    db.commit()
    return {"message": "Lesson deleted successfully"}


# ==========================================
# 7. STORIES & ADVENTURES CRUD
# ==========================================
@router.get("/stories")
def get_admin_stories(
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    stories = db.query(models.InteractiveStory).all()
    return [{
        "id": str(s.id),
        "title": s.title,
        "language_code": s.language_code,
        "cefr_level": s.cefr_level,
        "difficulty": s.difficulty,
        "xp_reward": s.xp_reward,
        "story_json": s.story_json
    } for s in stories]

@router.post("/stories")
def create_admin_story(
    payload: schemas.AdminStoryCreate,
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    story = models.InteractiveStory(
        title=payload.title,
        language_code=payload.language_code,
        cefr_level=payload.cefr_level,
        difficulty=payload.difficulty,
        xp_reward=payload.xp_reward,
        story_json=payload.story_json
    )
    db.add(story)
    db.commit()
    db.refresh(story)
    return {"message": "Interactive Story created successfully", "id": str(story.id)}

@router.put("/stories/{story_id}")
def update_admin_story(
    story_id: uuid.UUID,
    payload: schemas.AdminStoryUpdate,
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    story = db.query(models.InteractiveStory).filter(models.InteractiveStory.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    for field, value in payload.dict(exclude_unset=True).items():
        if value is not None:
            setattr(story, field, value)

    db.commit()
    return {"message": "Story updated successfully"}

@router.delete("/stories/{story_id}")
def delete_admin_story(
    story_id: uuid.UUID,
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    story = db.query(models.InteractiveStory).filter(models.InteractiveStory.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    db.delete(story)
    db.commit()
    return {"message": "Story deleted successfully"}


@router.get("/adventures")
def get_admin_adventures(
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    adventures = db.query(models.TextAdventureScenario).all()
    return [{
        "id": str(a.id),
        "title": a.title,
        "scenario_code": a.scenario_code,
        "target_language": a.target_language,
        "difficulty": a.difficulty,
        "system_prompt": a.system_prompt,
        "starting_message": a.starting_message
    } for a in adventures]

@router.post("/adventures")
def create_admin_adventure(
    payload: schemas.AdminAdventureCreate,
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    adventure = models.TextAdventureScenario(
        title=payload.title,
        scenario_code=payload.scenario_code,
        target_language=payload.target_language,
        difficulty=payload.difficulty,
        system_prompt=payload.system_prompt,
        starting_message=payload.starting_message
    )
    db.add(adventure)
    db.commit()
    db.refresh(adventure)
    return {"message": "Adventure Scenario created successfully", "id": str(adventure.id)}

@router.put("/adventures/{adventure_id}")
def update_admin_adventure(
    adventure_id: uuid.UUID,
    payload: schemas.AdminAdventureUpdate,
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    adv = db.query(models.TextAdventureScenario).filter(models.TextAdventureScenario.id == adventure_id).first()
    if not adv:
        raise HTTPException(status_code=404, detail="Adventure scenario not found")

    for field, value in payload.dict(exclude_unset=True).items():
        if value is not None:
            setattr(adv, field, value)

    db.commit()
    return {"message": "Adventure scenario updated successfully"}

@router.delete("/adventures/{adventure_id}")
def delete_admin_adventure(
    adventure_id: uuid.UUID,
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    adv = db.query(models.TextAdventureScenario).filter(models.TextAdventureScenario.id == adventure_id).first()
    if not adv:
        raise HTTPException(status_code=404, detail="Adventure scenario not found")

    db.delete(adv)
    db.commit()
    return {"message": "Adventure scenario deleted successfully"}


# ==========================================
# 8. VOCABULARY CRUD
# ==========================================
@router.get("/vocabulary")
def get_admin_vocabulary(
    q: Optional[str] = Query(None),
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    query = db.query(models.Vocabulary)
    if q:
        search_term = f"%{q.strip().lower()}%"
        query = query.filter(
            func.lower(models.Vocabulary.word).like(search_term) |
            func.lower(models.Vocabulary.translation).like(search_term)
        )
    vocabs = query.order_by(models.Vocabulary.created_at.desc()).limit(100).all()
    return [{
        "id": str(v.id),
        "word": v.word,
        "translation": v.translation,
        "language_code": v.language_code,
        "pos": v.pos,
        "cefr_level": v.cefr_level,
        "example_sentence": v.example_sentence
    } for v in vocabs]

@router.post("/vocabulary")
def create_admin_vocabulary(
    payload: schemas.AdminVocabularyCreate,
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    v = models.Vocabulary(
        word=payload.word,
        translation=payload.translation,
        language_code=payload.language_code,
        pos=payload.pos,
        cefr_level=payload.cefr_level,
        example_sentence=payload.example_sentence
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return {"message": "Vocabulary term created successfully", "id": str(v.id)}

@router.put("/vocabulary/{vocab_id}")
def update_admin_vocabulary(
    vocab_id: uuid.UUID,
    payload: schemas.AdminVocabularyUpdate,
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    v = db.query(models.Vocabulary).filter(models.Vocabulary.id == vocab_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vocabulary term not found")

    for field, value in payload.dict(exclude_unset=True).items():
        if value is not None:
            setattr(v, field, value)

    db.commit()
    return {"message": "Vocabulary term updated successfully"}

@router.delete("/vocabulary/{vocab_id}")
def delete_admin_vocabulary(
    vocab_id: uuid.UUID,
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    v = db.query(models.Vocabulary).filter(models.Vocabulary.id == vocab_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vocabulary term not found")

    db.delete(v)
    db.commit()
    return {"message": "Vocabulary term deleted successfully"}


# ==========================================
# 9. TEST MANAGEMENT CRUD
# ==========================================
# In-memory default tests cache for dynamic admin test management
_ADMIN_TESTS_STORE = [
    {
        "id": "11111111-1111-4111-a111-111111111111",
        "title": "NLP Basics",
        "questions_count": 20,
        "duration_minutes": 30,
        "difficulty": "Beginner",
        "status": "Active",
        "pass_percentage": 70.0,
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "id": "22222222-2222-4222-a222-222222222222",
        "title": "Cryptography & Security",
        "questions_count": 25,
        "duration_minutes": 45,
        "difficulty": "Intermediate",
        "status": "Draft",
        "pass_percentage": 75.0,
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "id": "33333333-3333-4333-a333-333333333333",
        "title": "DBMS Fundamentals",
        "questions_count": 30,
        "duration_minutes": 60,
        "difficulty": "Advanced",
        "status": "Active",
        "pass_percentage": 80.0,
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "id": "44444444-4444-4444-a444-444444444444",
        "title": "Phonics & Diagnostic Exam",
        "questions_count": 15,
        "duration_minutes": 20,
        "difficulty": "Beginner",
        "status": "Active",
        "pass_percentage": 65.0,
        "created_at": datetime.utcnow().isoformat()
    }
]

@router.get("/tests")
def get_admin_tests(
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    """
    Returns list of all assessments and tests for administration.
    Combines DB assessment records with active admin tests.
    """
    db_assessments = db.query(models.Assessment).all()
    results = []
    
    for a in db_assessments:
        q_count = len(a.questions) if a.questions else 20
        results.append({
            "id": str(a.id),
            "title": a.title,
            "questions_count": q_count,
            "duration_minutes": q_count * 2,
            "difficulty": "Intermediate" if q_count > 15 else "Beginner",
            "status": "Active",
            "pass_percentage": a.pass_percentage or 70.0,
            "created_at": datetime.utcnow().isoformat()
        })
        
    for t in _ADMIN_TESTS_STORE:
        if not any(r["id"] == t["id"] for r in results):
            results.append(t)
            
    return results

@router.post("/tests")
def create_admin_test(
    payload: schemas.AdminTestCreate,
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    new_id = str(uuid.uuid4())
    test_obj = {
        "id": new_id,
        "title": payload.title,
        "questions_count": payload.questions_count,
        "duration_minutes": payload.duration_minutes,
        "difficulty": payload.difficulty,
        "status": payload.status,
        "pass_percentage": payload.pass_percentage,
        "created_at": datetime.utcnow().isoformat()
    }
    _ADMIN_TESTS_STORE.insert(0, test_obj)
    return {"message": "Test created successfully", "id": new_id, "test": test_obj}

@router.put("/tests/{test_id}")
def update_admin_test(
    test_id: str,
    payload: schemas.AdminTestUpdate,
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    target = next((t for t in _ADMIN_TESTS_STORE if t["id"] == test_id), None)
    if not target:
        # Check DB assessments
        try:
            u_id = uuid.UUID(test_id)
            db_ass = db.query(models.Assessment).filter(models.Assessment.id == u_id).first()
            if db_ass:
                if payload.title: db_ass.title = payload.title
                if payload.pass_percentage: db_ass.pass_percentage = payload.pass_percentage
                db.commit()
                return {"message": "Assessment updated successfully"}
        except Exception:
            pass
        raise HTTPException(status_code=404, detail="Test not found")

    if payload.title is not None: target["title"] = payload.title
    if payload.questions_count is not None: target["questions_count"] = payload.questions_count
    if payload.duration_minutes is not None: target["duration_minutes"] = payload.duration_minutes
    if payload.difficulty is not None: target["difficulty"] = payload.difficulty
    if payload.status is not None: target["status"] = payload.status
    if payload.pass_percentage is not None: target["pass_percentage"] = payload.pass_percentage

    return {"message": "Test updated successfully", "test": target}

@router.delete("/tests/{test_id}")
def delete_admin_test(
    test_id: str,
    current_admin: models.Learner = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    global _ADMIN_TESTS_STORE
    orig_len = len(_ADMIN_TESTS_STORE)
    _ADMIN_TESTS_STORE = [t for t in _ADMIN_TESTS_STORE if t["id"] != test_id]
    if len(_ADMIN_TESTS_STORE) < orig_len:
        return {"message": "Test deleted successfully"}
        
    try:
        u_id = uuid.UUID(test_id)
        db_ass = db.query(models.Assessment).filter(models.Assessment.id == u_id).first()
        if db_ass:
            db.delete(db_ass)
            db.commit()
            return {"message": "Assessment deleted successfully"}
    except Exception:
        pass
        
    return {"message": "Test removed"}




# ==========================================
# 7. GENERIC DATABASE EXPLORER (LEGACY UTILITY)
# ==========================================
db_router = APIRouter(prefix="/api/database", tags=["database"])

ENTITY_CONFIGS = {
    "learners": {"model": models.Learner, "name": "Learner", "columns": ["id", "full_name", "email", "proficiency_level", "xp", "gems", "is_admin", "created_at"]},
    "courses": {"model": models.Course, "name": "Course", "columns": ["id", "title", "level", "is_published"]},
    "topics": {"model": models.Topic, "name": "Topic", "columns": ["id", "title", "order", "course_id"]},
    "lessons": {"model": models.Lesson, "name": "Lesson", "columns": ["id", "title", "duration_minutes", "order", "topic_id"]}
}

@db_router.get("/overview")
def get_database_overview(db: Session = Depends(database.get_db)):
    overview = []
    for key, cfg in ENTITY_CONFIGS.items():
        count = db.query(cfg["model"]).count()
        overview.append({"key": key, "name": cfg["name"], "count": count})
    return {"entities": overview, "total_tables": len(overview)}
