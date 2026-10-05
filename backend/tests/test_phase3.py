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

    def test_proficiency_tracking(self, auth_client):
        uid = auth_client.user_id
        assert auth_client.get(f"/api/progress/{uid}").json()["overall_proficiency"] == 0.0

        session = get_session(uid)
        session.learn.record_attempt("hello", "hello", 0.95, session)

        data = auth_client.get(f"/api/progress/{uid}").json()
        assert data["overall_proficiency"] > 0
        assert data["words_practiced"] == 1
        hello = next(w for w in data["word_details"] if w["word"] == "hello")
        assert hello["proficiency"] == 100.0
        assert hello["mastery_tier"] == "Master"

    def test_progress_persists_across_restart(self, auth_client):
        """Learning precision, XP and achievements survive the in-memory session being dropped."""
        from app.session_store import clear_session
        uid = auth_client.user_id
        session = get_session(uid)
        session.learn.record_attempt("hello", "hello", 0.95, session)
        xp = session.total_xp
        clear_session(uid)

        reloaded = get_session(uid)
        assert reloaded.learn.word_stats["hello"]["correct"] == 1
        assert reloaded.total_xp == xp
        assert "first_sign" in reloaded.unlocked_achievements
        assert reloaded.current_streak == 1

    def test_learning_path(self, auth_client):
        response = auth_client.get(f"/api/progress/{auth_client.user_id}/next")
        assert response.status_code == 200
        assert len(response.json()["suggested_words"]) == 3

    def test_xp_and_leveling(self, auth_client):
        uid = auth_client.user_id
        session = get_session(uid)
        session.award_xp(200, "Test Reward")
        assert session.level == 2

        data = auth_client.get(f"/api/dashboard/{uid}").json()
        assert data["xp_info"]["level"] == 2
        assert data["xp_info"]["current_xp"] == 200

        notes = auth_client.get(f"/api/notifications/{uid}").json()
        assert any("Level" in n["message"] for n in notes["notifications"])

    def test_achievements_unlock(self, auth_client):
        uid = auth_client.user_id
        session = get_session(uid)
        assert auth_client.get(f"/api/achievements/{uid}").json()["total_unlocked"] == 0

        session.learn.record_attempt("hello", "hello", 0.9, session)

        data = auth_client.get(f"/api/achievements/{uid}").json()
        first = next(a for a in data["achievements"] if a["id"] == "first_sign")
        assert first["unlocked"] and first["unlocked_at"]

    def test_history_timeline(self, auth_client):
        uid = auth_client.user_id
        get_session(uid).add_activity("custom_event", {"msg": "hello"}, xp_earned=5)

        data = auth_client.get(f"/api/history/{uid}").json()
        assert data["activities"][0]["type"] == "custom_event"
        assert data["activities"][0]["xp_earned"] == 5

    def test_dashboard_aggregated(self, auth_client):
        data = auth_client.get(f"/api/dashboard/{auth_client.user_id}").json()
        assert {"xp_info", "recent_activity", "suggested_next_words", "longest_streak"} <= data.keys()
        assert data["total_achievements"] == len(ACHIEVEMENT_DEFINITIONS)

    def test_dashboard_other_user_forbidden(self, auth_client):
        assert auth_client.get("/api/dashboard/someone-else").status_code == 403
