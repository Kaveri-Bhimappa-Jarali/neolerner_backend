import datetime
from sqlalchemy.orm import Session
import models

def check_and_reset_daily_xp(learner: models.Learner, db: Session):
    """
    Resets the learner's daily_xp_earned to 0 if we are on a new calendar day.
    """
    if learner.last_active_date:
        now = datetime.datetime.utcnow()
        today_date = now.date()
        last_active_local = learner.last_active_date.date()
        if today_date != last_active_local:
            learner.daily_xp_earned = 0
            db.commit()

def recharge_hearts_by_time(learner: models.Learner, db: Session) -> bool:
    """
    Recharges 1 heart every 4 hours, up to the maximum of 5 hearts.
    Also checks and resets daily XP if it is a new day.
    Returns True if database was modified, False otherwise.
    """
    check_and_reset_daily_xp(learner, db)
    
    if learner.hearts >= 5:
        learner.last_heart_recharge = datetime.datetime.utcnow()
        return False

    now = datetime.datetime.utcnow()
    last_recharge = learner.last_heart_recharge or learner.created_at or now
    
    elapsed_seconds = (now - last_recharge).total_seconds()
    # 4 hours = 14400 seconds
    hearts_to_add = int(elapsed_seconds // 14400)
    
    if hearts_to_add > 0:
        new_hearts = min(5, learner.hearts + hearts_to_add)
        # Shift last recharge forward by actual recharged chunks
        used_seconds = hearts_to_add * 14400
        learner.last_heart_recharge = last_recharge + datetime.timedelta(seconds=used_seconds)
        learner.hearts = new_hearts
        db.commit()
        return True
        
    return False

def update_streak(learner: models.Learner, db: Session) -> dict:
    """
    Updates the streak based on activity date.
    Returns a status dict: {"streak_updated": bool, "streak": int, "streak_frozen": bool}
    """
    now = datetime.datetime.utcnow()
    # Normalize dates to calendar dates (YYYY-MM-DD) for streak calculation
    today_date = now.date()
    
    if learner.last_active_date is None:
        learner.streak = 1
        learner.last_active_date = now
        # Double or nothing progress
        if learner.double_or_nothing_active:
            learner.double_or_nothing_streak = 1
        db.commit()
        return {"streak_updated": True, "streak": 1, "streak_frozen": False}
        
    # last_active_date can be offset-aware or naive. Let's make it naive.
    last_active_local = learner.last_active_date.date()
    delta = (today_date - last_active_local).days
    
    status = {"streak_updated": False, "streak": learner.streak, "streak_frozen": False}
    
    if delta == 0:
        # Already active today, no streak update needed
        return status
    elif delta == 1:
        # Consecutive day!
        learner.streak += 1
        learner.last_active_date = now
        status["streak_updated"] = True
        status["streak"] = learner.streak
        
        # Track double or nothing streak
        if learner.double_or_nothing_active:
            learner.double_or_nothing_streak += 1
            if learner.double_or_nothing_streak >= 7:
                # Earn 100 gems (bet 50, double is 100)
                learner.gems += 100
                learner.double_or_nothing_active = False
                learner.double_or_nothing_streak = 0
                
        db.commit()
    else:
        # Streak broken (delta > 1)
        if learner.streak_freeze_count > 0:
            # Consume a streak freeze!
            learner.streak_freeze_count -= 1
            # Maintain the streak but set active date to today
            learner.last_active_date = now
            status["streak_frozen"] = True
            status["streak_updated"] = True
            db.commit()
        else:
            # Reset streak
            learner.streak = 1
            learner.last_active_date = now
            if learner.double_or_nothing_active:
                learner.double_or_nothing_streak = 1
            status["streak_updated"] = True
            status["streak"] = 1
            db.commit()
            
    return status

def award_xp_and_gems(learner: models.Learner, xp: int, gems: int, db: Session):
    """
    Awards XP and Gems to a learner, updates daily XP earnings, and rewards daily goal completions.
    """
    # Make sure hearts recharge checks (and daily XP resets) are made
    recharge_hearts_by_time(learner, db)
    
    # Award XP and general gems
    learner.xp += xp
    learner.gems += gems
    
    # Update daily XP earnings
    learner.daily_xp_earned += xp
    
    # Check daily goal completion
    if learner.daily_xp_earned >= learner.daily_xp_goal:
        now = datetime.datetime.utcnow()
        today_date = now.date()
        
        goal_already_completed_today = False
        if learner.last_goal_completed_date:
            goal_already_completed_today = (learner.last_goal_completed_date.date() == today_date)
            
        if not goal_already_completed_today:
            learner.last_goal_completed_date = now
            learner.gems += 10  # Reward 10 gems for completing the daily goal
            
    db.commit()
    db.refresh(learner)
    check_and_trigger_achievements(learner, db)

def check_and_trigger_achievements(learner: models.Learner, db: Session):
    """
    Evaluates learner milestones (lessons, XP, streaks, pronunciation, quizzes)
    and unlocks corresponding AchievementDefinition records.
    """
    try:
        definitions = db.query(models.AchievementDefinition).all()
        if not definitions:
            return

        completed_lessons = db.query(models.LearningProgress).filter(
            models.LearningProgress.learner_id == learner.id,
            models.LearningProgress.status == models.ProgressStatus.completed
        ).count()

        speaking_attempts = db.query(models.PronunciationAttempt).filter(
            models.PronunciationAttempt.learner_id == learner.id,
            models.PronunciationAttempt.overall_score >= 60.0
        ).count()

        for defn in definitions:
            prog = 0
            if defn.category == "lessons":
                prog = completed_lessons
            elif defn.category == "streak":
                prog = learner.streak
            elif defn.category == "speaking":
                prog = speaking_attempts
            elif defn.category == "xp":
                prog = learner.xp
            elif defn.category == "milestones":
                prog = 1 if learner.has_completed_placement_test else 0
            else:
                prog = completed_lessons

            user_ach = db.query(models.LearnerAchievement).filter(
                models.LearnerAchievement.learner_id == learner.id,
                models.LearnerAchievement.achievement_id == defn.id
            ).first()

            is_unlocked = prog >= defn.threshold
            if not user_ach:
                user_ach = models.LearnerAchievement(
                    id=models.uuid.uuid4(),
                    learner_id=learner.id,
                    achievement_id=defn.id,
                    progress=prog,
                    is_unlocked=is_unlocked,
                    unlocked_at=datetime.datetime.utcnow() if is_unlocked else None
                )
                db.add(user_ach)
            else:
                user_ach.progress = prog
                if is_unlocked and not user_ach.is_unlocked:
                    user_ach.is_unlocked = True
                    user_ach.unlocked_at = datetime.datetime.utcnow()

        db.commit()
    except Exception as e:
        print(f"[WARN] Achievement trigger warning: {e}")

