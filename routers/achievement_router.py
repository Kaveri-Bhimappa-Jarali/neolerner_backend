from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import schemas, models, database, dependencies, gamification

router = APIRouter(prefix="/api/achievements", tags=["achievements"])

@router.get("/me", response_model=List[schemas.AchievementResponse])
@router.get("/me/", response_model=List[schemas.AchievementResponse])
def get_my_achievements(
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    """
    Gamification & Achievement System:
    Evaluates current learner metrics, updates unlocked states, and returns full list of badges.
    """
    gamification.check_and_trigger_achievements(current_learner, db)

    definitions = db.query(models.AchievementDefinition).all()
    user_achievements = {
        ua.achievement_id: ua
        for ua in db.query(models.LearnerAchievement).filter(
            models.LearnerAchievement.learner_id == current_learner.id
        ).all()
    }

    res = []
    for defn in definitions:
        user_ach = user_achievements.get(defn.id)
        prog = user_ach.progress if user_ach else 0
        unlocked = user_ach.is_unlocked if user_ach else (prog >= defn.threshold)
        unlocked_at = user_ach.unlocked_at if user_ach else None

        res.append(schemas.AchievementResponse(
            id=defn.id,
            code=defn.code,
            name=defn.name,
            description=defn.description,
            icon=defn.icon,
            category=defn.category,
            threshold=defn.threshold,
            xp_reward=defn.xp_reward,
            gem_reward=defn.gem_reward,
            progress=prog,
            is_unlocked=unlocked,
            unlocked_at=unlocked_at
        ))
    return res

@router.post("/claim/{code}")
def claim_achievement_reward(
    code: str,
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    """
    Claims XP and Gem rewards for an unlocked achievement badge.
    """
    defn = db.query(models.AchievementDefinition).filter(models.AchievementDefinition.code == code).first()
    if not defn:
        raise HTTPException(status_code=404, detail="Achievement not found")

    user_ach = db.query(models.LearnerAchievement).filter(
        models.LearnerAchievement.learner_id == current_learner.id,
        models.LearnerAchievement.achievement_id == defn.id
    ).first()

    if not user_ach or not user_ach.is_unlocked:
        raise HTTPException(status_code=400, detail="Achievement is not unlocked yet")

    gamification.award_xp_and_gems(current_learner, defn.xp_reward, defn.gem_reward, db)
    return {
        "message": f"Claimed reward for {defn.name}!",
        "xp_earned": defn.xp_reward,
        "gems_earned": defn.gem_reward
    }
