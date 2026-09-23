from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import schemas, models, database, dependencies, gamification

router = APIRouter(prefix="/api/leagues", tags=["leagues"])

LEAGUE_TIERS = [
    {"tier": models.LeagueTier.Bronze, "name": "Bronze League", "color": "#cd7f32", "icon": "🥉"},
    {"tier": models.LeagueTier.Silver, "name": "Silver League", "color": "#c0c0c0", "icon": "🥈"},
    {"tier": models.LeagueTier.Gold, "name": "Gold League", "color": "#ffd700", "icon": "🥇"},
    {"tier": models.LeagueTier.Sapphire, "name": "Sapphire League", "color": "#0f52ba", "icon": "🔷"},
    {"tier": models.LeagueTier.Ruby, "name": "Ruby League", "color": "#e0115f", "icon": "♦️"},
    {"tier": models.LeagueTier.Emerald, "name": "Emerald League", "color": "#50c878", "icon": "❇️"},
    {"tier": models.LeagueTier.Amethyst, "name": "Amethyst League", "color": "#9966cc", "icon": "🔮"},
    {"tier": models.LeagueTier.Pearl, "name": "Pearl League", "color": "#eae0c8", "icon": "⚪"},
    {"tier": models.LeagueTier.Obsidian, "name": "Obsidian League", "color": "#2c2c2c", "icon": "🖤"},
    {"tier": models.LeagueTier.Diamond, "name": "Diamond League", "color": "#b9f2ff", "icon": "💎"}
]

@router.get("/current", response_model=schemas.LeagueStandingsResponse)
def get_current_league(
    current_learner: models.Learner = Depends(dependencies.get_current_learner),
    db: Session = Depends(database.get_db)
):
    gamification.recharge_hearts_by_time(current_learner, db)

    # Determine user's current tier
    user_tier = current_learner.league_tier or models.LeagueTier.Gold
    tier_idx = 2
    for idx, t in enumerate(LEAGUE_TIERS):
        if t["tier"] == user_tier:
            tier_idx = idx
            break

    current_tier_info = LEAGUE_TIERS[tier_idx]

    # Calculate days left until Sunday
    now = datetime.utcnow()
    days_left = 7 - now.isoweekday()
    if days_left <= 0:
        days_left = 1

    # Generate 19 realistic competitors around user's weekly XP
    user_xp = current_learner.xp
    competitors = [
        {"name": "DuoOwl 🦉", "xp_offset": 280, "avatar": "🦉"},
        {"name": "Ananya K. 🇮🇳", "xp_offset": 195, "avatar": "👩"},
        {"name": "PolyglotPro 🌍", "xp_offset": 140, "avatar": "🌍"},
        {"name": "Kiran Rao ⚡", "xp_offset": 90, "avatar": "👨"},
        {"name": "LingoChamp 🏆", "xp_offset": 45, "avatar": "🏆"},
        {"name": "Siddharth M. 📚", "xp_offset": 20, "avatar": "👨‍🎓"},
        {"name": "Pooja Hegde 🌸", "xp_offset": -15, "avatar": "👩‍💼"},
        {"name": "WordWizard 🧙‍♂️", "xp_offset": -35, "avatar": "🧙‍♂️"},
        {"name": "Ramesh Kumar ☕", "xp_offset": -55, "avatar": "👨"},
        {"name": "GamerLingo 🎮", "xp_offset": -80, "avatar": "🎮"},
        {"name": "Sneha Joshi 🎨", "xp_offset": -110, "avatar": "🎨"},
        {"name": "Vikram Seth 📖", "xp_offset": -135, "avatar": "📖"},
        {"name": "SmartyPants 🤓", "xp_offset": -160, "avatar": "🤓"},
        {"name": "Deepa Nair 🌴", "xp_offset": -190, "avatar": "🌴"},
        {"name": "StudyBud 📝", "xp_offset": -220, "avatar": "📝"},
        {"name": "Manoj Patil 🚜", "xp_offset": -250, "avatar": "🚜"},
        {"name": "DuoFanatic 💫", "xp_offset": -280, "avatar": "💫"},
        {"name": "Bhavya G. 🪔", "xp_offset": -310, "avatar": "🪔"},
        {"name": "NoviceLearner 🌱", "xp_offset": -350, "avatar": "🌱"}
    ]

    members_list = []
    for comp in competitors:
        members_list.append({
            "name": comp["name"],
            "xp": max(5, user_xp + comp["xp_offset"]),
            "avatar": comp["avatar"],
            "is_user": False
        })

    # Add user
    members_list.append({
        "name": f"{current_learner.full_name} (You)",
        "xp": user_xp,
        "avatar": "⭐",
        "is_user": True
    })

    # Sort descending by XP
    members_list.sort(key=lambda m: m["xp"], reverse=True)

    user_rank = 1
    for idx, m in enumerate(members_list):
        m["rank"] = idx + 1
        if m["is_user"]:
            user_rank = idx + 1

    return schemas.LeagueStandingsResponse(
        tier=current_tier_info["tier"],
        tier_name=current_tier_info["name"],
        tier_index=tier_idx,
        user_rank=user_rank,
        user_weekly_xp=user_xp,
        days_remaining=days_left,
        promotion_zone=5,
        demotion_zone=5,
        members=members_list
    )
