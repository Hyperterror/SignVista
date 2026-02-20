"""
Tests for Phase 3 — Learning & Gamified Dashboard
"""

import pytest
from app.session_store import get_session, ACHIEVEMENT_DEFINITIONS


class TestPhase3:

    def test_dictionary_all(self, client):
        """Test fetching the whole dictionary."""
        response = client.get("/api/dictionary")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 15
        assert len(data["categories"]) > 0
        assert "hello" in [w["word"] for w in data["words"]]

    def test_dictionary_search(self, client):
        """Test dictionary search functionality."""
        response = client.get("/api/dictionary?search=hel")
        assert response.status_code == 200
        data = response.json()
        assert any("hello" in w["word"] for w in data["words"])
        assert all("hel" in w["word"].lower() for w in data["words"])

    def test_dictionary_filter(self, client):
        """Test dictionary category filtering."""
        response = client.get("/api/dictionary?category=greetings")
        assert response.status_code == 200
        data = response.json()
        assert all(w["category"] == "greetings" for w in data["words"])

    def test_proficiency_tracking(self, client, fake_frame):
        """Test proficiency increases after successful learn attempt."""
        session_id = "test-prof-1"
        
        # 1. Check initial proficiency (0)
        response = client.get(f"/api/progress/{session_id}")
        assert response.status_code == 200
        assert response.json()["overall_proficiency"] == 0.0
        
        # 2. Mock a CORRECT learn attempt
        # Since we use real ML if loaded, we might need to mock predict_from_raw_frame
        # But for this test, let's assume session manipulation is safer for logic verification
        session = get_session(session_id)
        session.learn.record_attempt("hello", "hello", 0.95, session)
        
        # 3. Check updated proficiency
        response = client.get(f"/api/progress/{session_id}")
        data = response.json()
        assert data["overall_proficiency"] > 0
        assert data["words_practiced"] == 1
        
        # Check detail
        hello_detail = next(w for w in data["word_details"] if w["word"] == "hello")
        assert hello_detail["proficiency"] == 100.0
        assert hello_detail["mastery_tier"] == "Master"

    def test_learning_path(self, client):
        """Test that learning path suggests words."""
        session_id = "test-path-1"
        response = client.get(f"/api/progress/{session_id}/next")
        assert response.status_code == 200
        data = response.json()
        assert len(data["suggested_words"]) == 3

    def test_xp_and_leveling(self, client):
        """Test XP award and level up."""
        session_id = "test-xp-1"
        session = get_session(session_id)
        
        # Award 200 XP (should reach Level 2)
        session.award_xp(200, "Test Reward")
        assert session.level == 2
        
        # Check dashboard
        response = client.get(f"/api/dashboard/{session_id}")
        data = response.json()
        assert data["xp_info"]["level"] == 2
        assert data["xp_info"]["current_xp"] == 200
        
    def test_achievements_unlock(self, client):
        """Test achievement unlocking."""
        session_id = "test-ach-1"
        session = get_session(session_id)
        
        # Lock check
        response = client.get(f"/api/achievements/{session_id}")
        assert response.json()["total_unlocked"] == 0
        
        # Unlock "First Sign" via learn attempt
        session.learn.record_attempt("hello", "hello", 0.9, session)
        
        # Verify unlock
        response = client.get(f"/api/achievements/{session_id}")
        data = response.json()
        assert data["total_unlocked"] >= 1
        assert any(a["id"] == "first_sign" and a["unlocked"] for a in data["achievements"])

    def test_history_timeline(self, client):
        """Test activity history logging."""
        session_id = "test-hist-1"
        session = get_session(session_id)
        
        session.add_activity("custom_event", {"msg": "hello"})
        
        response = client.get(f"/api/history/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["activities"]) > 0
        assert data["activities"][0]["type"] == "custom_event"

    def test_dashboard_aggregated(self, client):
        """Test full dashboard response."""
        session_id = "test-dash-full"
        response = client.get(f"/api/dashboard/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert "xp_info" in data
        assert "recent_activity" in data
        assert "suggested_next_words" in data
        assert data["total_achievements"] == 12
