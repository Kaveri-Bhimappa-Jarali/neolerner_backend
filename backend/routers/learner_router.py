from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import schemas, models, database, dependencies, gamification

router = APIRouter(prefix="/api/learners", tags=["learners"])

@router.get("/me", response_model=schemas.LearnerResponse)
@router.get("/me/", response_model=schemas.LearnerResponse)
def read_users_me(
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    # Perform time-based heart recharge
    gamification.recharge_hearts_by_time(current_learner, db)
    return current_learner

@router.put("/me", response_model=schemas.LearnerResponse)
@router.put("/me/", response_model=schemas.LearnerResponse)
def update_user_me(
    learner_update: schemas.LearnerUpdate, 
    current_learner: models.Learner = Depends(dependencies.get_current_learner), 
    db: Session = Depends(database.get_db)
):
    gamification.recharge_hearts_by_time(current_learner, db)
    
    if "full_name" in learner_update.model_fields_set and learner_update.full_name and learner_update.full_name.strip():
        current_learner.full_name = learner_update.full_name.strip()
    if "age" in learner_update.model_fields_set and learner_update.age is not None:
        current_learner.age = learner_update.age
    if "preferred_language_id" in learner_update.model_fields_set and learner_update.preferred_language_id is not None:
        current_learner.preferred_language_id = learner_update.preferred_language_id
    if "target_language_id" in learner_update.model_fields_set and learner_update.target_language_id is not None:
        current_learner.target_language_id = learner_update.target_language_id
    if "preferred_language_code" in learner_update.model_fields_set and learner_update.preferred_language_code:
        from sqlalchemy import func
        p_lang = db.query(models.Language).filter(func.lower(models.Language.code) == learner_update.preferred_language_code.lower()).first()
        if p_lang:
            current_learner.preferred_language_id = p_lang.id
    if "target_language_code" in learner_update.model_fields_set and learner_update.target_language_code:
        from sqlalchemy import func
        t_lang = db.query(models.Language).filter(func.lower(models.Language.code) == learner_update.target_language_code.lower()).first()
        if t_lang:
            current_learner.target_language_id = t_lang.id
    if "proficiency_level" in learner_update.model_fields_set and learner_update.proficiency_level is not None:
        current_learner.proficiency_level = learner_update.proficiency_level
    if "learning_goal" in learner_update.model_fields_set and learner_update.learning_goal is not None:
        current_learner.learning_goal = learner_update.learning_goal
    if "prior_knowledge" in learner_update.model_fields_set and learner_update.prior_knowledge is not None:
        current_learner.prior_knowledge = learner_update.prior_knowledge
    if "cefr_level" in learner_update.model_fields_set and learner_update.cefr_level is not None:
        current_learner.cefr_level = learner_update.cefr_level
    if "daily_minutes_goal" in learner_update.model_fields_set and learner_update.daily_minutes_goal is not None:
        current_learner.daily_minutes_goal = learner_update.daily_minutes_goal
    if "has_completed_placement_test" in learner_update.model_fields_set and learner_update.has_completed_placement_test is not None:
        current_learner.has_completed_placement_test = learner_update.has_completed_placement_test
    if "placement_score" in learner_update.model_fields_set and learner_update.placement_score is not None:
        current_learner.placement_score = learner_update.placement_score

    db.commit()
    db.refresh(current_learner)
    return current_learner

@router.post("/shop/buy", response_model=schemas.LearnerResponse)
@router.post("/shop/buy/", response_model=schemas.LearnerResponse)
def buy_shop_item(
    purchase: schemas.ShopPurchase,
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    gamification.recharge_hearts_by_time(current_learner, db)
    
    item = purchase.item_name
    if item == "streak_freeze":
        cost = 200
        if current_learner.gems < cost:
            raise HTTPException(status_code=400, detail="Not enough gems")
        current_learner.gems -= cost
        current_learner.streak_freeze_count += 1
    elif item == "heart_refill":
        cost = 150
        if current_learner.gems < cost:
            raise HTTPException(status_code=400, detail="Not enough gems")
        if current_learner.hearts >= 5:
            raise HTTPException(status_code=400, detail="Hearts already full")
        current_learner.gems -= cost
        current_learner.hearts = 5
    elif item == "double_or_nothing":
        cost = 50
        if current_learner.gems < cost:
            raise HTTPException(status_code=400, detail="Not enough gems")
        if current_learner.double_or_nothing_active:
            raise HTTPException(status_code=400, detail="Double or Nothing already active")
        current_learner.gems -= cost
        current_learner.double_or_nothing_active = True
        current_learner.double_or_nothing_streak = 0
    else:
        raise HTTPException(status_code=400, detail="Invalid shop item")
        
    db.commit()
    db.refresh(current_learner)
    return current_learner

@router.post("/practice", response_model=schemas.LearnerResponse)
@router.post("/practice/", response_model=schemas.LearnerResponse)
def practice_for_heart(
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    gamification.recharge_hearts_by_time(current_learner, db)
    
    if current_learner.hearts >= 5:
        raise HTTPException(status_code=400, detail="Hearts already full")
        
    current_learner.hearts += 1
    # Award 5 XP for practicing
    gamification.award_xp_and_gems(current_learner, xp=5, gems=0, db=db)
    gamification.update_streak(current_learner, db=db)
    
    db.commit()
    db.refresh(current_learner)
    return current_learner

@router.get("/leaderboard")
@router.get("/leaderboard/")
def get_leaderboard(
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    gamification.recharge_hearts_by_time(current_learner, db)
    
    # Generate 9 simulated players whose XP is relative to the user's XP
    simulated_users = [
        {"name": "DuoOwl 🦉", "xp": max(25, current_learner.xp + 150), "is_simulated": True},
        {"name": "PolyglotPro 🌍", "xp": max(20, current_learner.xp + 85), "is_simulated": True},
        {"name": "LingoChamp 🏆", "xp": max(15, current_learner.xp + 35), "is_simulated": True},
        {"name": "WordWizard 🧙‍♂️", "xp": max(10, current_learner.xp - 10), "is_simulated": True},
        {"name": "BookWorm 🐛", "xp": max(5, current_learner.xp - 30), "is_simulated": True},
        {"name": "GamerLingo 🎮", "xp": max(2, current_learner.xp - 65), "is_simulated": True},
        {"name": "SmartyPants 🤓", "xp": max(1, current_learner.xp - 100), "is_simulated": True},
        {"name": "StudyBud 📝", "xp": max(0, current_learner.xp - 160), "is_simulated": True},
        {"name": "DuoFanatic 💫", "xp": max(0, current_learner.xp - 220), "is_simulated": True},
    ]
    
    # Add current user
    user_entry = {"name": current_learner.full_name + " (You)", "xp": current_learner.xp, "is_simulated": False}
    all_entries = simulated_users + [user_entry]
    
    # Sort by XP descending
    all_entries.sort(key=lambda x: x["xp"], reverse=True)
    
    # Attach ranks
    leaderboard = []
    for idx, entry in enumerate(all_entries):
        leaderboard.append({
            "rank": idx + 1,
            "name": entry["name"],
            "xp": entry["xp"],
            "is_user": not entry["is_simulated"]
        })
        
    return {
        "league": "Gold League",
        "days_remaining": 3,
        "leaderboard": leaderboard
    }

@router.get("/achievements")
@router.get("/achievements/")
def get_achievements(
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    gamification.recharge_hearts_by_time(current_learner, db)
    
    # Calculate some metrics
    lessons_completed = db.query(models.LearningProgress).filter(
        models.LearningProgress.learner_id == current_learner.id,
        models.LearningProgress.status == models.ProgressStatus.completed
    ).count()
    
    perfect_quizzes = db.query(models.AssessmentResult).filter(
        models.AssessmentResult.learner_id == current_learner.id,
        models.AssessmentResult.score == 100.0
    ).count()
    
    # Define achievements with tiers
    # Wildfire (streak)
    streak = current_learner.streak
    wildfire = {
        "id": "ach_wildfire",
        "name": "Wildfire 🔥",
        "description": "Maintain a daily learning streak.",
        "progress": streak,
        "tiers": [
            {"target": 3, "label": "Bronze", "unlocked": streak >= 3},
            {"target": 7, "label": "Silver", "unlocked": streak >= 7},
            {"target": 14, "label": "Gold", "unlocked": streak >= 14}
        ]
    }
    
    # Scholar (lessons completed)
    scholar = {
        "id": "ach_scholar",
        "name": "Scholar 🎓",
        "description": "Complete structured literacy lessons.",
        "progress": lessons_completed,
        "tiers": [
            {"target": 1, "label": "Bronze", "unlocked": lessons_completed >= 1},
            {"target": 5, "label": "Silver", "unlocked": lessons_completed >= 5},
            {"target": 10, "label": "Gold", "unlocked": lessons_completed >= 10}
        ]
    }
    
    # Champion (perfect quizzes)
    champion = {
        "id": "ach_champion",
        "name": "Champion 🏆",
        "description": "Score 100% on lesson quizzes.",
        "progress": perfect_quizzes,
        "tiers": [
            {"target": 1, "label": "Bronze", "unlocked": perfect_quizzes >= 1},
            {"target": 3, "label": "Silver", "unlocked": perfect_quizzes >= 3},
            {"target": 5, "label": "Gold", "unlocked": perfect_quizzes >= 5}
        ]
    }
    
    # Gem Collector
    # We don't have cumulative gems, so let's use current gems as a proxy or just award based on current gems
    gems = current_learner.gems
    gem_collector = {
        "id": "ach_gem_collector",
        "name": "Gem Collector 💎",
        "description": "Collect virtual gems.",
        "progress": gems,
        "tiers": [
            {"target": 100, "label": "Bronze", "unlocked": gems >= 100},
            {"target": 500, "label": "Silver", "unlocked": gems >= 500},
            {"target": 1000, "label": "Gold", "unlocked": gems >= 1000}
        ]
    }
    
    return [wildfire, scholar, champion, gem_collector]

@router.delete("/me")
@router.delete("/me/")
def delete_account_me(
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    """
    Explicit user account deletion endpoint.
    Permanently deletes the authenticated learner account and commits the deletion to the persistent database.
    """
    try:
        db.delete(current_learner)
        db.commit()
        return {
            "status": "success",
            "message": "User account and all associated learner records have been permanently deleted."
        }
    except Exception as e:
        db.rollback()
        print(f"[ERROR /api/learners/me DELETE]: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete account: {str(e)}"
        )
