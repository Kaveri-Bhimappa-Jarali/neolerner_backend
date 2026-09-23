import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
import models, schemas

DEFAULT_PROFICIENCY_BANDS = [
    {"min": 0.0, "max": 29.9, "level": "A1", "title": "Beginner / Foundations"},
    {"min": 30.0, "max": 59.9, "level": "A2", "title": "Elementary"},
    {"min": 60.0, "max": 79.9, "level": "B1", "title": "Intermediate"},
    {"min": 80.0, "max": 99.9, "level": "B2", "title": "Upper Intermediate"},
    {"min": 100.0, "max": 120.0, "level": "C1", "title": "Advanced Mastery"}
]

DEFAULT_ENGINE_WEIGHTS = {
    "level_weight": 0.40,
    "skill_weight": 0.25,
    "goal_weight": 0.20,
    "prerequisite_weight": 0.10,
    "difficulty_weight": 0.05
}

CEFR_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]

# Goal mapping synonyms / related domains
GOAL_AFFINITY_MAP = {
    "conversation": ["conversation", "daily-life", "speaking", "listening", "travel", "career", "academic", "writing", "reading"],
    "career": ["career", "academic", "writing", "professional", "exams", "conversation"],
    "travel": ["travel", "conversation", "daily-life", "speaking"],
    "academic": ["academic", "reading", "writing", "exams", "career", "conversation"],
    "exams": ["exams", "academic", "grammar", "reading", "writing"],
    "reading": ["reading", "academic", "vocabulary"],
    "writing": ["writing", "academic", "grammar", "career"],
    "daily-life": ["daily-life", "conversation", "travel"]
}

class CourseRecommendationEngine:
    """
    Dedicated Adaptive Recommendation Engine for NeoLearner.
    Calculates multi-factor recommendation match scores based on:
      1. Level Match (40%)
      2. Weak-Skill Inverse Priority Match (25%)
      3. Goal Match (20%)
      4. Prerequisites Check (10%)
      5. Difficulty Match (5%)
    Also determines starting topic/unit placement & generates 'Why am I seeing this?' justifications.
    """

    def __init__(self, bands: Optional[List[Dict[str, Any]]] = None, weights: Optional[Dict[str, float]] = None):
        self.bands = bands if bands is not None else DEFAULT_PROFICIENCY_BANDS
        self.weights = weights if weights is not None else DEFAULT_ENGINE_WEIGHTS

    def score_to_cefr(self, score: float) -> str:
        """Converts raw score into CEFR level using configurable bands."""
        score_val = max(0.0, min(120.0, float(score)))
        for b in self.bands:
            if b["min"] <= score_val <= b["max"]:
                return b["level"]
        if score_val >= 100.0:
            return "C1"
        return "A1"

    def get_cefr_index(self, level_str: str) -> int:
        clean = (level_str or "A1").upper().strip()
        if clean in CEFR_ORDER:
            return CEFR_ORDER.index(clean)
        if "A1" in clean: return 0
        if "A2" in clean: return 1
        if "B1" in clean: return 2
        if "B2" in clean: return 3
        if "C1" in clean: return 4
        if "C2" in clean: return 5
        return 0

    def calculate_level_match(self, learner_cefr: str, course_cefr: str) -> Tuple[float, bool, Optional[str]]:
        learner_idx = self.get_cefr_index(learner_cefr)
        course_idx = self.get_cefr_index(course_cefr)
        diff = course_idx - learner_idx

        if diff == 0:
            return 100.0, False, None
        elif diff == -1:
            return 85.0, False, None  # 1 level below (e.g. B2 course for C1 learner)
        elif diff == -2:
            return 75.0, False, None  # 2 levels below (e.g. B2 course for C2 learner)
        elif diff == -3:
            return 60.0, False, None  # 3 levels below (e.g. B1 course for C2 learner)
        elif diff == -4:
            return 45.0, False, None
        elif diff <= -5:
            return 30.0, False, None  # 5+ levels below (e.g. A1 course for C2 learner)
        elif diff == 1:
            return 55.0, False, None  # Stretch course 1 level above
        else:
            # 2+ levels above: Course locked
            lock_msg = f"Requires CEFR {course_cefr} proficiency (your current level is {learner_cefr})."
            return 0.0, True, lock_msg

    def calculate_weak_skill_match(self, skill_breakdown: Dict[str, float], course_skills: List[str]) -> Tuple[float, List[str]]:
        """
        Inverse Priority: Skills where the learner has LOWER scores receive HIGHER priority.
        """
        if not course_skills:
            return 50.0, []

        target_weak_skills = []
        total_points = 0.0
        
        for skill in course_skills:
            s_clean = skill.lower().strip()
            score = float(skill_breakdown.get(s_clean, 65.0))
            # Inverse weighting: Lower score -> higher inverse weight
            inverse_score = max(0.0, 100.0 - score)
            total_points += inverse_score
            if score < 60.0:
                target_weak_skills.append(s_clean)

        avg_inverse = total_points / len(course_skills)
        # Normalize: 0 to 100
        match_score = min(100.0, max(20.0, avg_inverse * 1.5))
        return match_score, target_weak_skills

    def calculate_goal_match(self, learner_goal: str, course_goals: List[str]) -> float:
        if not course_goals:
            return 60.0
        
        l_goal = (learner_goal or "conversation").lower().strip()
        c_goals = [g.lower().strip() for g in course_goals]

        if l_goal in c_goals:
            return 100.0

        # Check related goals
        affinities = GOAL_AFFINITY_MAP.get(l_goal, [l_goal])
        for aff in affinities:
            if aff in c_goals:
                return 80.0

        return 35.0

    def calculate_prerequisite_match(self, learner_id: uuid.UUID, prerequisites: List[str], db: Session) -> Tuple[float, bool, Optional[str]]:
        if not prerequisites:
            return 100.0, True, None

        # Check completed courses for learner
        completed_course_ids = set()
        progress_records = db.query(models.LearningProgress).filter(
            models.LearningProgress.learner_id == learner_id,
            models.LearningProgress.percentage_completed >= 100.0
        ).all()

        for pr in progress_records:
            if pr.lesson and pr.lesson.topic and pr.lesson.topic.course_id:
                completed_course_ids.add(str(pr.lesson.topic.course_id))

        missing = []
        for req in prerequisites:
            req_str = str(req)
            if req_str not in completed_course_ids:
                missing.append(req_str)

        if not missing:
            return 100.0, True, None
        else:
            return 0.0, False, f"Requires completion of prerequisite course ({len(missing)} remaining)."

    def calculate_starting_unit(
        self,
        learner_id: uuid.UUID,
        course: models.Course,
        overall_score: float,
        skill_breakdown: Dict[str, float],
        db: Session
    ) -> Tuple[int, Optional[uuid.UUID], Optional[str], int]:
        """
        Determines starting topic/unit placement based on learner score & skill mastery.
        """
        topics = course.topics or []
        if not topics:
            return 1, None, None, 0

        # Sort topics by order
        sorted_topics = sorted(topics, key=lambda t: t.order)
        total_topics = len(sorted_topics)

        # Check existing progress per topic
        topic_mastery = {}
        for t in sorted_topics:
            lessons = t.lessons or []
            if not lessons:
                topic_mastery[t.id] = 0.0
                continue
            completed_count = db.query(models.LearningProgress).filter(
                models.LearningProgress.learner_id == learner_id,
                models.LearningProgress.lesson_id.in_([l.id for l in lessons]),
                models.LearningProgress.status == models.ProgressStatus.completed
            ).count()
            topic_mastery[t.id] = (completed_count / len(lessons)) * 100.0

        # Skip topics if learner already completed them or if diagnostic score is very high for course band
        skipped_count = 0
        starting_topic = sorted_topics[0]

        # If overall score is high and user tested out
        course_cefr = course.cefr_level or "A1"
        learner_cefr = self.score_to_cefr(overall_score)

        if learner_cefr == course_cefr and overall_score >= 70.0 and total_topics >= 3:
            # Skip first 1-2 foundational topics if mastery is high
            skip_target = 2 if (overall_score >= 85.0 and total_topics >= 4) else 1
            skipped_count = skip_target
            starting_topic = sorted_topics[min(skipped_count, total_topics - 1)]
        else:
            # Find first unmastered topic
            for idx, t in enumerate(sorted_topics):
                if topic_mastery.get(t.id, 0.0) < 100.0:
                    starting_topic = t
                    skipped_count = idx
                    break

        return (skipped_count + 1), starting_topic.id, starting_topic.title, skipped_count

    def generate_reasons(
        self,
        level_score: float,
        skill_score: float,
        goal_score: float,
        prereq_cleared: bool,
        learner_cefr: str,
        course: models.Course,
        target_weak_skills: List[str],
        learner_goal: str,
        starting_topic_index: int,
        skipped_count: int
    ) -> List[schemas.RecommendationReasonItem]:
        reasons = []

        course_cefr = course.cefr_level or "A1"

        # Level match reason
        if level_score >= 90.0:
            reasons.append(schemas.RecommendationReasonItem(
                text=f"✓ Perfect match for your current {learner_cefr} level.",
                reason_type="level_match"
            ))
        elif level_score >= 65.0:
            reasons.append(schemas.RecommendationReasonItem(
                text=f"✓ Appropriate level review building on your {learner_cefr} foundation.",
                reason_type="level_match"
            ))

        # Goal match reason
        if goal_score >= 80.0:
            reasons.append(schemas.RecommendationReasonItem(
                text=f"✓ Directly matches your selected '{learner_goal.capitalize()}' goal.",
                reason_type="goal_match"
            ))

        # Weak skill target reason
        if target_weak_skills:
            skill_names = ", ".join([s.capitalize() for s in target_weak_skills[:2]])
            reasons.append(schemas.RecommendationReasonItem(
                text=f"✓ Targeted booster to improve your weakest skill: {skill_names}.",
                reason_type="weak_skill_target"
            ))

        # Prerequisites unlocked
        if prereq_cleared:
            reasons.append(schemas.RecommendationReasonItem(
                text="✓ All prerequisites unlocked based on your prior learning.",
                reason_type="prerequisite_unlocked"
            ))

        # Starting unit placement
        reasons.append(schemas.RecommendationReasonItem(
            text=f"📍 Recommended starting point: Unit {starting_topic_index} (Matched to CEFR {course.cefr_level}).",
            reason_type="starting_unit"
        ))

        return reasons

    def rank_courses_for_learner(
        self,
        learner: models.Learner,
        db: Session
    ) -> schemas.CourseRecommendationResponse:
        """
        Ranks all published courses in the learner's target language using the recommendation algorithm.
        """
        # Determine learner metrics
        overall_score = float(learner.placement_score or learner.predicted_proficiency_score or 50.0)
        learner_cefr = learner.cefr_level or self.score_to_cefr(overall_score)
        learner_goal = learner.learning_goal or "conversation"

        # Extract skill breakdown
        skill_breakdown = {"vocabulary": 60.0, "grammar": 60.0, "reading": 60.0, "listening": 60.0, "speaking": 60.0, "writing": 60.0}
        strengths = []
        weaknesses = []

        latest_result = db.query(models.AssessmentResult).filter(
            models.AssessmentResult.learner_id == learner.id
        ).order_by(models.AssessmentResult.completed_at.desc()).first()

        if latest_result:
            if latest_result.skill_breakdown:
                try:
                    parsed = json.loads(latest_result.skill_breakdown) if isinstance(latest_result.skill_breakdown, str) else latest_result.skill_breakdown
                    skill_breakdown.update({k.lower(): float(v) for k, v in parsed.items()})
                except Exception:
                    pass
            if latest_result.strengths:
                try:
                    strengths = json.loads(latest_result.strengths) if isinstance(latest_result.strengths, str) else latest_result.strengths
                except Exception:
                    pass
            if latest_result.weak_areas:
                try:
                    weaknesses = json.loads(latest_result.weak_areas) if isinstance(latest_result.weak_areas, str) else latest_result.weak_areas
                except Exception:
                    pass

        # If weak_areas empty, calculate from skill_breakdown
        if not weaknesses:
            sorted_skills = sorted(skill_breakdown.items(), key=lambda x: x[1])
            weaknesses = [k.capitalize() for k, v in sorted_skills[:2]]
            strengths = [k.capitalize() for k, v in sorted_skills[-2:]]

        # Fetch courses matching learner target language (or all courses if target language not set)
        query = db.query(models.Course).filter(models.Course.is_published == True)
        if learner.target_language_id:
            query = query.filter(models.Course.language_id == learner.target_language_id)

        courses = query.all()

        # Engine Weights
        w_level = self.weights.get("level_weight", 0.40)
        w_skill = self.weights.get("skill_weight", 0.25)
        w_goal = self.weights.get("goal_weight", 0.20)
        w_prereq = self.weights.get("prerequisite_weight", 0.10)
        w_diff = self.weights.get("difficulty_weight", 0.05)

        ranked_items: List[schemas.CourseRecommendationItem] = []

        for c in courses:
            # Parse course JSON metadata
            c_skills = json.loads(c.skills_json) if c.skills_json else ["vocabulary", "grammar"]
            c_goals = json.loads(c.goals_json) if c.goals_json else ["conversation"]
            c_prereqs = json.loads(c.prerequisites_json) if c.prerequisites_json else []

            # 1. Level Match
            level_score, level_locked, level_lock_reason = self.calculate_level_match(learner_cefr, c.cefr_level or "A1")

            # 2. Skill Match
            skill_score, target_weak_skills = self.calculate_weak_skill_match(skill_breakdown, c_skills)

            # 3. Goal Match
            goal_score = self.calculate_goal_match(learner_goal, c_goals)

            # 4. Prerequisite Match
            prereq_score, prereq_cleared, prereq_lock_reason = self.calculate_prerequisite_match(learner.id, c_prereqs, db)

            # 5. Difficulty Match
            c_level_str = c.level.value.lower() if hasattr(c.level, 'value') else str(c.level or "beginner").lower()
            learner_level_str = learner.proficiency_level.value.lower() if hasattr(learner.proficiency_level, 'value') else str(learner.proficiency_level or "beginner").lower()
            diff_score = 100.0 if c_level_str == learner_level_str else 70.0

            # Composite match calculation (0 - 100)
            composite_match = (
                (level_score * w_level) +
                (skill_score * w_skill) +
                (goal_score * w_goal) +
                (prereq_score * w_prereq) +
                (diff_score * w_diff)
            )

            is_locked = level_locked or not prereq_cleared
            lock_reason = level_lock_reason or prereq_lock_reason

            # Starting Unit Placement
            start_idx, start_id, start_title, skipped_count = self.calculate_starting_unit(
                learner.id, c, overall_score, skill_breakdown, db
            )

            # Reasons
            reasons = self.generate_reasons(
                level_score, skill_score, goal_score, prereq_cleared,
                learner_cefr, c, target_weak_skills, learner_goal, start_idx, skipped_count
            )

            # Determine type
            rec_type = "primary"
            if is_locked:
                rec_type = "locked"
            elif target_weak_skills and composite_match < 90.0:
                rec_type = "skill_booster"
            elif level_score < 70.0 and composite_match >= 50.0:
                rec_type = "optional_challenge"

            item = schemas.CourseRecommendationItem(
                course_id=c.id,
                title=c.title,
                description=c.description,
                cefr_level=c.cefr_level or "A1",
                recommendation_type=rec_type,
                match_score=round(composite_match, 1),
                is_locked=is_locked,
                lock_reason=lock_reason,
                reasons=reasons,
                starting_topic_index=start_idx,
                starting_topic_id=start_id,
                starting_topic_title=start_title,
                skipped_topics_count=skipped_count,
                skills_covered=c_skills,
                target_goals=c_goals
            )
            ranked_items.append(item)

        # Sort descending by match score
        ranked_items.sort(key=lambda x: (not x.is_locked, x.match_score), reverse=True)

        # Categorize into primary, boosters, and challenges
        primary_rec = None
        skill_boosters = []
        optional_challenges = []

        unlocked_items = [i for i in ranked_items if not i.is_locked]
        if unlocked_items:
            # Set top item as PRIMARY
            unlocked_items[0].recommendation_type = "primary"
            primary_rec = unlocked_items[0]

            for item in unlocked_items[1:]:
                if any(w.lower() in [s.lower() for s in item.skills_covered] for w in weaknesses):
                    item.recommendation_type = "skill_booster"
                    skill_boosters.append(item)
                else:
                    item.recommendation_type = "optional_challenge"
                    optional_challenges.append(item)

        return schemas.CourseRecommendationResponse(
            learner_overall_score=overall_score,
            learner_cefr_level=learner_cefr,
            learner_goal=learner_goal,
            skill_breakdown=skill_breakdown,
            strengths=strengths,
            weaknesses=weaknesses,
            primary_recommendation=primary_rec,
            skill_boosters=skill_boosters[:3],
            optional_challenges=optional_challenges[:3],
            all_ranked_courses=ranked_items
        )


# Singleton instance
default_recommendation_engine = CourseRecommendationEngine()
