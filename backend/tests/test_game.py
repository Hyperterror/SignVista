"""Tests for game endpoints."""

from tests.conftest import make_fake_frame


def test_game_start(client):
    """Starting a game should return gameId and first challenge."""
    response = client.post("/api/game/start", json={
        "sessionId": "game-test-1",
        "duration": 30,
    })
    assert response.status_code == 200
    data = response.json()
    assert "gameId" in data
    assert "currentChallenge" in data
    assert data["duration"] == 30
    assert data["totalChallenges"] > 0


def test_game_attempt(client):
    """Game attempt should return score and streak info."""
    # Start game
    start = client.post("/api/game/start", json={
        "sessionId": "game-test-2",
        "duration": 30,
    })
    game_id = start.json()["gameId"]

    # Make attempt
    response = client.post("/api/game/attempt", json={
        "sessionId": "game-test-2",
        "gameId": game_id,
        "frame": make_fake_frame(),
    })
    assert response.status_code == 200
    data = response.json()
    assert "score" in data
    assert "streak" in data
    assert "multiplier" in data
    assert "currentChallenge" in data
    assert "wordsCompleted" in data


def test_game_result(client):
    """Game result should return final stats and badges."""
    # Start game
    start = client.post("/api/game/start", json={
        "sessionId": "game-test-3",
        "duration": 30,
    })
    game_id = start.json()["gameId"]

    # Make a couple attempts
    for _ in range(3):
        client.post("/api/game/attempt", json={
            "sessionId": "game-test-3",
            "gameId": game_id,
            "frame": make_fake_frame(),
        })

    # Get results
    response = client.get(f"/api/game/result/game-test-3/{game_id}")
    assert response.status_code == 200
    data = response.json()
    assert "score" in data
    assert "badges" in data
    assert "accuracy" in data
    assert "streak_best" in data
    assert data["gameId"] == game_id


def test_game_invalid_game_id(client):
    """Attempt with invalid gameId should 404."""
    response = client.post("/api/game/attempt", json={
        "sessionId": "game-test-4",
        "gameId": "nonexistent",
        "frame": make_fake_frame(),
    })
    assert response.status_code == 404
