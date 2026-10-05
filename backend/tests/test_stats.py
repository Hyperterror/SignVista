"""Tests for stats and vocabulary endpoints."""


def test_vocabulary_returns_words(client):
    response = client.get("/api/vocabulary")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == len(data["words"]) >= 10
    word = data["words"][0]
    assert {"word", "display_name", "priority", "index", "recognizable"} <= word.keys()


def test_vocabulary_flags_recognizable_words(client):
    words = {w["word"]: w for w in client.get("/api/vocabulary").json()["words"]}
    # The word-level LSTM knows hello / how_are_you / thank_you
    assert words["hello"]["recognizable"] is True
    # No model can recognize "water" yet
    assert words["water"]["recognizable"] is False


def test_stats_empty_session(auth_client):
    response = auth_client.get(f"/api/stats/{auth_client.user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["sessionId"] == auth_client.user_id
    assert data["total_attempts"] == 0
    assert data["words_practiced"] == 0
    assert data["overall_proficiency"] == 0.0


def test_stats_other_user_forbidden(auth_client):
    assert auth_client.get("/api/stats/someone-else").status_code == 403


def test_stats_requires_auth(client):
    assert client.get("/api/stats/anyone").status_code == 401


def test_vocabulary_word_order(client):
    priorities = [w["priority"] for w in client.get("/api/vocabulary").json()["words"]]
    assert priorities == sorted(priorities)
