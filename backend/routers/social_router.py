from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import schemas, models, database, dependencies, gamification

router = APIRouter(prefix="/api/friends", tags=["friends_social"])

@router.get("", response_model=List[schemas.FriendUserResponse])
@router.get("/", response_model=List[schemas.FriendUserResponse])
def get_friends(
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    # Find all friendships involving current learner
    friendships = db.query(models.Friendship).filter(
        (models.Friendship.requester_id == current_learner.id) |
        (models.Friendship.receiver_id == current_learner.id)
    ).all()

    result = []
    seen_ids = set()

    for f in friendships:
        friend_learner = f.receiver if f.requester_id == current_learner.id else f.requester
        if friend_learner.id in seen_ids:
            continue
        seen_ids.add(friend_learner.id)
        result.append(schemas.FriendUserResponse(
            id=friend_learner.id,
            full_name=friend_learner.full_name,
            email=friend_learner.email,
            xp=friend_learner.xp,
            streak=friend_learner.streak,
            avatar_initial=friend_learner.full_name[0].upper() if friend_learner.full_name else "F",
            friendship_status=f.status.value,
            friend_streak=f.streak_count
        ))

    # If user has no friends yet, let's provide 3 simulated study buddies for rich UI interaction
    if len(result) == 0:
        simulated_buddies = [
            {"name": "Priya Sharma 🌟", "email": "priya.sharma@lingolearn.in", "xp": current_learner.xp + 140, "streak": max(1, current_learner.streak + 2), "friend_streak": 4},
            {"name": "Rahul Verma 🚀", "email": "rahul.verma@lingolearn.in", "xp": max(20, current_learner.xp - 40), "streak": max(1, current_learner.streak), "friend_streak": 2},
            {"name": "Aarav Patel 💡", "email": "aarav.patel@lingolearn.in", "xp": current_learner.xp + 85, "streak": max(1, current_learner.streak + 1), "friend_streak": 5}
        ]
        for b in simulated_buddies:
            result.append(schemas.FriendUserResponse(
                id=UUID("11111111-1111-1111-1111-111111111111"),
                full_name=b["name"],
                email=b["email"],
                xp=b["xp"],
                streak=b["streak"],
                avatar_initial=b["name"][0],
                friendship_status="accepted",
                friend_streak=b["friend_streak"]
            ))

    return result

@router.post("/action")
def friend_action(
    req: schemas.FriendRequestAction,
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    if req.action == "send":
        target = None
        if req.email:
            target = db.query(models.Learner).filter(models.Learner.email == req.email.strip().lower()).first()
        elif req.friend_id:
            target = db.query(models.Learner).filter(models.Learner.id == req.friend_id).first()

        if not target:
            raise HTTPException(status_code=404, detail="User with this email not found")
        if target.id == current_learner.id:
            raise HTTPException(status_code=400, detail="You cannot friend yourself")

        existing = db.query(models.Friendship).filter(
            ((models.Friendship.requester_id == current_learner.id) & (models.Friendship.receiver_id == target.id)) |
            ((models.Friendship.requester_id == target.id) & (models.Friendship.receiver_id == current_learner.id))
        ).first()

        if existing:
            return {"message": f"Friendship status is already {existing.status.value}"}

        new_f = models.Friendship(
            requester_id=current_learner.id,
            receiver_id=target.id,
            status=models.FriendshipStatus.accepted, # Auto-accept for smooth demo
            streak_count=1
        )
        db.add(new_f)
        db.commit()
        return {"message": f"Connected with {target.full_name}!"}

    return {"message": "Action completed"}

@router.get("/quest", response_model=schemas.FriendQuestStatusResponse)
def get_friend_quest(
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    target_xp = 2000
    my_contrib = min(1200, current_learner.xp)
    friend_contrib = 650
    combined = my_contrib + friend_contrib
    is_completed = combined >= target_xp

    # Calculate days left until Sunday midnight
    now = datetime.utcnow()
    days_left = 7 - now.isoweekday()
    if days_left <= 0:
        days_left = 1

    return schemas.FriendQuestStatusResponse(
        has_active_quest=True,
        target_xp=target_xp,
        combined_xp=combined,
        my_xp=my_contrib,
        friend_xp=friend_contrib,
        friend_name="Priya Sharma",
        gem_reward=100,
        days_left=days_left,
        is_completed=is_completed,
        claimed=False
    )

@router.post("/quest/claim")
def claim_friend_quest(
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    # Award 100 gems
    gamification.award_xp_and_gems(current_learner, xp=50, gems=100, db=db)
    db.commit()
    return {"message": "100 Gems claimed successfully!", "gems": current_learner.gems}
