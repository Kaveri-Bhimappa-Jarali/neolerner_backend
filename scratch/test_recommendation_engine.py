import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import json
import uuid
from fastapi.testclient import TestClient
from main import app
from recommendation_engine import CourseRecommendationEngine, DEFAULT_PROFICIENCY_BANDS

client = TestClient(app)

def run_recommendation_tests():
    print("==================================================")
    print("   ADAPTIVE COURSE RECOMMENDATION ENGINE TEST SUITE")
    print("==================================================")

    # 1. Test Score-to-Level Mapping
    print("\n[1/6] Testing Configurable Score-to-Level Band Mapping...")
    engine = CourseRecommendationEngine()
    assert engine.score_to_cefr(15.0) == "A1", f"Expected A1, got {engine.score_to_cefr(15.0)}"
    assert engine.score_to_cefr(45.0) == "A2", f"Expected A2, got {engine.score_to_cefr(45.0)}"
    assert engine.score_to_cefr(68.0) == "B1", f"Expected B1, got {engine.score_to_cefr(68.0)}"
    assert engine.score_to_cefr(88.0) == "B2", f"Expected B2, got {engine.score_to_cefr(88.0)}"
    assert engine.score_to_cefr(105.0) == "C1", f"Expected C1, got {engine.score_to_cefr(105.0)}"
    print("  -> Score-to-Level Mapping verified 100%: 15->A1, 45->A2, 68->B1, 88->B2, 105->C1.")

    # 2. Test Weak-Skill Inverse Priority Logic
    print("\n[2/6] Testing Weak-Skill Inverse Priority Weighting...")
    # Uneven learner profile: Vocab=82, Reading=79, Grammar=70, Speaking=51, Listening=46
    skills_profile = {"vocabulary": 82.0, "reading": 79.0, "grammar": 70.0, "speaking": 51.0, "listening": 46.0}
    
    listening_course_skills = ["listening", "speaking"]
    vocab_course_skills = ["vocabulary", "reading"]

    listening_score, weak_list1 = engine.calculate_weak_skill_match(skills_profile, listening_course_skills)
    vocab_score, weak_list2 = engine.calculate_weak_skill_match(skills_profile, vocab_course_skills)

    print(f"  -> Listening Course Inverse Priority Match Score: {listening_score:.1f}% (Targets weak: {weak_list1})")
    print(f"  -> Vocabulary Course Inverse Priority Match Score: {vocab_score:.1f}%")
    assert listening_score > vocab_score, "Listening course must score higher than vocabulary course when listening is weak!"
    print("  -> Weak-Skill Inverse Priority verified: Weakest skill (Listening=46%) correctly prioritized over strong skill (Vocab=82%).")

    # 3. Test Goal Matching
    print("\n[3/6] Testing Goal Matching...")
    career_score = engine.calculate_goal_match("career", ["career", "professional"])
    travel_score = engine.calculate_goal_match("career", ["travel", "sightseeing"])
    print(f"  -> Match score for 'career' goal with Career course: {career_score}%")
    print(f"  -> Match score for 'career' goal with Travel course: {travel_score}%")
    assert career_score > travel_score, "Career goal must match career course higher than travel course!"

    # 4. Authenticate Demo User & Test API /api/learning/recommendations
    print("\n[4/6] Testing API Endpoint /api/learning/recommendations...")
    login_res = client.post("/api/auth/login", data={"username": "kaverijarali98@gmail.com", "password": "Kaveri@123"})
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    rec_res = client.get("/api/learning/recommendations", headers=headers)
    assert rec_res.status_code == 200, f"Get recommendations failed: {rec_res.text}"
    rec_data = rec_res.json()
    
    print(f"  -> Learner CEFR Level: {rec_data['learner_cefr_level']}")
    print(f"  -> Learner Goal: {rec_data['learner_goal']}")
    print(f"  -> Weaknesses: {rec_data['weaknesses']}")
    
    primary = rec_data.get("primary_recommendation")
    assert primary is not None, "Primary recommendation must be returned!"
    print(f"  -> Primary Path: '{primary['title']}' ({primary['match_score']}% Match)")
    print(f"     Recommended Starting Unit: Unit {primary['starting_topic_index']} ({primary['skipped_topics_count']} topics skipped)")
    print(f"     Reasons: {[r['text'] for r in primary['reasons']]}")

    # 5. Test Configurable Bands API GET & PUT /api/recommendations/bands
    print("\n[5/6] Testing Admin Configurable Bands API...")
    bands_res = client.get("/api/recommendations/bands", headers=headers)
    assert bands_res.status_code == 200
    bands_data = bands_res.json()
    print(f"  -> Retrieved {len(bands_data['bands'])} bands & weights: {bands_data['weights']}")

    put_res = client.put("/api/recommendations/bands", json={
        "weights": {"level_weight": 0.45, "skill_weight": 0.25, "goal_weight": 0.15, "prerequisite_weight": 0.10, "difficulty_weight": 0.05}
    }, headers=headers)
    assert put_res.status_code == 200
    assert put_res.json()["weights"]["level_weight"] == 0.45
    print("  -> Engine weights updated successfully via API.")

    # 6. Test Re-evaluation API POST /api/recommendations/reevaluate
    print("\n[6/6] Testing Dynamic Re-evaluation API...")
    reeval_res = client.post("/api/recommendations/reevaluate", headers=headers)
    assert reeval_res.status_code == 200
    print(f"  -> Dynamic re-evaluation completed successfully. Total ranked courses: {len(reeval_res.json()['all_ranked_courses'])}")

    print("\n==================================================")
    print("   ADAPTIVE RECOMMENDATION ENGINE TEST 100% PASSED! ")
    print("==================================================")

if __name__ == "__main__":
    run_recommendation_tests()
