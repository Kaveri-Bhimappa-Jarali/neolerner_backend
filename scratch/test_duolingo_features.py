import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import json
import uuid
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def run_tests():
    print("==================================================")
    print("   NEOLEARNER DUOLINGO PARITY FEATURES TEST SUITE ")
    print("==================================================")

    # 1. Login with demo user
    print("\n[1/8] Authenticating demo user (kaverijarali98@gmail.com)...")
    login_res = client.post("/api/auth/login", data={"username": "kaverijarali98@gmail.com", "password": "Kaveri@123"})
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("  -> Auth token acquired successfully.")

    # 2. AI Conversation Lab
    print("\n[2/8] Testing AI Conversation Lab...")
    scenarios_res = client.get("/api/conversation/scenarios", headers=headers)
    assert scenarios_res.status_code == 200, f"Scenarios failed: {scenarios_res.text}"
    scenarios = scenarios_res.json()
    print(f"  -> Retrieved {len(scenarios)} roleplay scenarios: {[s['id'] for s in scenarios[:4]]}...")
    
    start_res = client.post("/api/conversation/start", json={"scenario": "restaurant"}, headers=headers)
    assert start_res.status_code == 200, f"Start conversation failed: {start_res.text}"
    conv_data = start_res.json()
    session_id = conv_data["session_id"]
    print(f"  -> Conversation session started: {session_id}")
    print(f"  -> AI Tutor opening line: {conv_data['ai_message']}")

    # Send a turn
    msg_res = client.post("/api/conversation/respond", json={
        "session_id": session_id,
        "user_transcript": "ನನಗೆ ಒಂದು ದೋಸೆ ಮತ್ತು ಕಾಫಿ ಕೊಡಿ"
    }, headers=headers)
    assert msg_res.status_code == 200, f"Send message failed: {msg_res.text}"
    turn_data = msg_res.json()
    print(f"  -> AI Reply: {turn_data['ai_reply']}")
    print(f"  -> Phonetics: {turn_data.get('phonetic')}")
    print(f"  -> Grammar correction: {turn_data.get('grammar_correction')}")
    print(f"  -> Turn score: {turn_data.get('turn_score')}")

    # End conversation
    end_res = client.post("/api/conversation/end", json={"session_id": session_id}, headers=headers)
    assert end_res.status_code == 200
    end_data = end_res.json()
    print(f"  -> Session ended! Composite Score: {end_data['composite_score']}%, +{end_data['xp_earned']} XP")

    # 3. Interactive Stories Engine
    print("\n[3/8] Testing Interactive Stories...")
    stories_res = client.get("/api/stories/?lang_code=kn", headers=headers)
    assert stories_res.status_code == 200, f"Stories list failed: {stories_res.text}"
    stories = stories_res.json()
    print(f"  -> Found {len(stories)} stories for Kannada.")
    assert len(stories) > 0
    first_story = stories[0]
    print(f"  -> Story 1: '{first_story['title']}'")

    story_detail = client.get(f"/api/stories/{first_story['id']}", headers=headers)
    assert story_detail.status_code == 200
    detail_data = story_detail.json()
    print(f"  -> Story loaded: {len(detail_data['scenes'])} scenes, {len(detail_data['exercises'])} checkpoint exercises")
    
    complete_story = client.post(f"/api/stories/{first_story['id']}/complete", json={"score": 100}, headers=headers)
    assert complete_story.status_code == 200
    comp_data = complete_story.json()
    print(f"  -> Story completed! Awarded: +{comp_data['xp_earned']} XP, +{comp_data['gems_earned']} Gems")

    # 4. Branching Adventures
    print("\n[4/8] Testing Branching Adventures...")
    adventures_res = client.get("/api/adventures/?lang_code=kn", headers=headers)
    assert adventures_res.status_code == 200, f"Adventures list failed: {adventures_res.text}"
    adventures = adventures_res.json()
    print(f"  -> Found {len(adventures)} adventures.")
    first_adv = adventures[0]
    print(f"  -> Adventure 1: '{first_adv['title']}'")

    # Execute step in adventure
    step_res = client.post(f"/api/adventures/{first_adv['id']}/step", json={
        "step_key": "start",
        "chosen_index": 0
    }, headers=headers)
    assert step_res.status_code == 200
    step_data = step_res.json()
    print(f"  -> Adventure step progressed: next='{step_data['next_step_key']}', feedback='{step_data['narrative_feedback']}', +{step_data['xp_earned']} XP")

    # 5. Practice Hub (12 Modes + Visual Flashcards)
    print("\n[5/8] Testing Practice Hub Overview...")
    ph_res = client.get("/api/practice-hub/overview", headers=headers)
    assert ph_res.status_code == 200, f"Practice hub failed: {ph_res.text}"
    ph_data = ph_res.json()
    print(f"  -> 12 Modes available: {len(ph_data['modes'])} workout cards loaded.")
    print(f"  -> Active Boost: {ph_data.get('active_boost')}")
    print(f"  -> Due SRS Vocab: {ph_data['due_srs_count']}, Mistakes: {ph_data['mistakes_count']}, Deck size: {ph_data['flashcards_deck_size']}")

    # 6. Social & Friends Quest
    print("\n[6/8] Testing Social, Friends, and Friends Quest...")
    friends_res = client.get("/api/friends/", headers=headers)
    assert friends_res.status_code == 200
    friends = friends_res.json()
    print(f"  -> Friends retrieved: {len(friends)} friends (e.g. {friends[0]['full_name']})")

    quest_res = client.get("/api/friends/quest", headers=headers)
    assert quest_res.status_code == 200
    quest_data = quest_res.json()
    print(f"  -> Friends Quest with {quest_data['friend_name']}: Goal={quest_data['target_xp']} XP, Combined={quest_data['combined_xp']} XP")

    # 7. 10-Tier Leagues Ladder
    print("\n[7/8] Testing 10-Tier Leagues Ladder...")
    current_league = client.get("/api/leagues/current", headers=headers)
    assert current_league.status_code == 200
    cl_data = current_league.json()
    print(f"  -> Current Tier: {cl_data['tier_name']} (Index {cl_data['tier_index']}), Standings: {len(cl_data['members'])} learners, Days left: {cl_data['days_remaining']}")

    # 8. Explain My Answer & Unit Guidebooks
    print("\n[8/8] Testing Explain My Answer (AI) & Unit Guidebooks...")
    explain_res = client.post("/api/ai/explain-mistake", json={
        "question_text": "Choose the correct translation of 'water' in Kannada.",
        "user_answer_text": "ಹಾಲು (milk)",
        "correct_answer_text": "ನೀರು (water)"
    }, headers=headers)
    assert explain_res.status_code == 200, f"Explain failed: {explain_res.text}"
    exp = explain_res.json()
    print(f"  -> AI Pedagogical Breakdown:")
    print(f"     Grammar rule: {exp.get('grammar_rule')}")
    print(f"     Contrast: {exp.get('contrast_examples')}")
    print(f"     Memory Tip: {exp.get('memory_tip')}")

    # Unit Guidebook
    courses_res = client.get("/api/courses/")
    assert courses_res.status_code == 200
    courses = courses_res.json()
    if len(courses) > 0 and len(courses[0].get("topics", [])) > 0:
        topic_id = courses[0]["topics"][0]["id"]
        gb_res = client.get(f"/api/guidebooks/topic/{topic_id}", headers=headers)
        assert gb_res.status_code == 200
        gb_data = gb_res.json()
        print(f"  -> Unit Guidebook loaded for topic '{gb_data.get('topic_title')}': {len(gb_data.get('key_phrases', []))} key phrases, test-out available.")

    print("\n==================================================")
    print("   ALL 8 DUOLINGO PARITY FEATURES VERIFIED 100%!  ")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
