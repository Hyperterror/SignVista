"""Tests for game endpoints."""

from tests.conftest import make_fake_frame


def _start(c, duration=30):
    resp = c.post("/api/game/start", json={"duration": duration})
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_game_requires_auth(client):
    assert client.post("/api/game/start", json={"duration": 30}).status_code == 401


def test_game_start(auth_client):
    data = _start(auth_client)
    assert data["gameId"]
    assert data["currentChallenge"]
    assert data["duration"] == 30
    assert data["totalChallenges"] > 0


def test_game_duration_is_bounded(auth_client):
    assert auth_client.post("/api/game/start", json={"duration": -5}).status_code == 422
    assert auth_client.post("/api/game/start", json={"duration": 100000}).status_code == 422


def test_game_challenges_are_recognizable(auth_client):
    from app.session_store import get_session
    from ml.inference import get_recognizable_words

    game_id = _start(auth_client)["gameId"]
    game = get_session(auth_client.user_id).get_game(game_id)
    recognizable = {w.lower() for w in get_recognizable_words()}
    assert all(c.lower() in recognizable for c in game.challenges)


def test_game_attempt(auth_client):
    game_id = _start(auth_client)["gameId"]
    response = auth_client.post("/api/game/attempt", json={"gameId": game_id, "frame": make_fake_frame()})
    assert response.status_code == 200
    data = response.json()
    assert {"score", "streak", "multiplier", "currentChallenge", "wordsCompleted", "timeRemaining", "isActive"} <= data.keys()
    # A frame with nobody in it is not an attempt and earns nothing
    assert data["score"] == 0 and data["correct"] is False


def test_game_result_is_idempotent(auth_client):
    """Fetching results repeatedly must not award XP or history more than once."""
    game_id = _start(auth_client)["gameId"]
    uid = auth_client.user_id

    first = auth_client.get(f"/api/game/result/{uid}/{game_id}")
    assert first.status_code == 200
    assert {"score", "badges", "accuracy", "streak_best"} <= first.json().keys()
    xp_after_first = auth_client.get(f"/api/dashboard/{uid}").json()["xp_info"]["current_xp"]

    for _ in range(5):
        assert auth_client.get(f"/api/game/result/{uid}/{game_id}").status_code == 200
    dashboard = auth_client.get(f"/api/dashboard/{uid}").json()
    assert dashboard["xp_info"]["current_xp"] == xp_after_first

    history = auth_client.get(f"/api/history/{uid}?type=game_completed").json()["activities"]
    assert len(history) == 1


def test_game_attempt_after_result_is_rejected(auth_client):
    game_id = _start(auth_client)["gameId"]
    auth_client.get(f"/api/game/result/{auth_client.user_id}/{game_id}")
    response = auth_client.post("/api/game/attempt", json={"gameId": game_id, "frame": make_fake_frame()})
    assert response.status_code == 409


def test_game_invalid_game_id(auth_client):
    response = auth_client.post("/api/game/attempt", json={"gameId": "nonexistent", "frame": make_fake_frame()})
    assert response.status_code == 404


def test_game_result_other_user_forbidden(auth_client):
    game_id = _start(auth_client)["gameId"]
    assert auth_client.get(f"/api/game/result/someone-else/{game_id}").status_code == 403
