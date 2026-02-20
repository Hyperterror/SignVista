"""Tests for stats and vocabulary endpoints."""


def test_vocabulary_returns_words(client):
    """Vocabulary endpoint should return word list."""
    response = client.get("/api/vocabulary")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 15
    assert len(data["words"]) == 15
    # Check first word structure
    word = data["words"][0]
    assert "word" in word
    assert "display_name" in word
    assert "priority" in word
    assert "index" in word


def test_stats_empty_session(client):
    """Stats for new session should return empty but valid structure."""
    response = client.get("/api/stats/empty-session")
    assert response.status_code == 200
    data = response.json()
    assert data["sessionId"] == "empty-session"
    assert data["total_attempts"] == 0
    assert data["words_practiced"] == 0
    assert data["overall_proficiency"] == 0.0


def test_stats_missing_session_id(client):
    """Stats with whitespace-only sessionId should return 400."""
    response = client.get("/api/stats/ ")
    assert response.status_code == 400


def test_vocabulary_word_order(client):
    """Core words (priority 1) should come before extended (priority 2)."""
    response = client.get("/api/vocabulary")
    words = response.json()["words"]
    priorities = [w["priority"] for w in words]
    # Core words first, then extended
    assert priorities == sorted(priorities)
