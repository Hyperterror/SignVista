"""
Tests for Phase 2 — Profile, Text-to-Sign, Sign Demos, AR Landmarks
"""

import pytest


# ─── Profile Tests ────────────────────────────────────────────────

class TestProfile:

    def test_create_profile(self, client):
        """Create a profile with all fields."""
        response = client.post("/api/profile", json={
            "sessionId": "test-profile-1",
            "name": "Ravi Kumar",
            "email": "ravi@example.com",
            "phone": "+91 9876543210",
            "preferred_language": "en",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Ravi Kumar"
        assert data["email"] == "ravi@example.com"
        assert data["preferred_language"] == "en"
        assert "Welcome" in data["welcome_message"]
        assert "Ravi Kumar" in data["welcome_message"]
        assert len(data["welcome_sign_data"]) > 0

    def test_create_profile_hindi(self, client):
        """Profile with Hindi preference gets Hindi welcome."""
        response = client.post("/api/profile", json={
            "sessionId": "test-profile-hi",
            "name": "रवि",
            "email": "ravi@example.com",
            "preferred_language": "hi",
        })
        assert response.status_code == 200
        data = response.json()
        assert "स्वागत" in data["welcome_message"]

    def test_get_profile(self, client):
        """Create then retrieve a profile."""
        client.post("/api/profile", json={
            "sessionId": "test-profile-get",
            "name": "Test User",
            "email": "test@example.com",
            "preferred_language": "en",
        })
        response = client.get("/api/profile/test-profile-get")
        assert response.status_code == 200
        assert response.json()["name"] == "Test User"

    def test_get_profile_not_found(self, client):
        """Getting a non-existent profile returns 404."""
        response = client.get("/api/profile/nonexistent-user")
        assert response.status_code == 404

    def test_create_profile_missing_name(self, client):
        """Profile without name should fail validation."""
        response = client.post("/api/profile", json={
            "sessionId": "test-no-name",
            "name": "",
            "email": "test@example.com",
        })
        assert response.status_code == 422  # Pydantic validation error

    def test_create_profile_invalid_email(self, client):
        """Profile with invalid email should return 400."""
        response = client.post("/api/profile", json={
            "sessionId": "test-bad-email",
            "name": "Test",
            "email": "not-an-email",
        })
        assert response.status_code == 400


# ─── Text to Sign Tests ──────────────────────────────────────────

class TestTextToSign:

    def test_text_to_sign_english(self, client):
        """Convert English text to sign data."""
        response = client.post("/api/text-to-sign", json={
            "text": "Hello, how are you?",
            "language": "en",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["original_text"] == "Hello, how are you?"
        assert data["matched_words"] > 0
        # Should find "hello" and "how_are_you" at minimum
        word_keys = [w["word"] for w in data["words"]]
        assert "hello" in word_keys

    def test_text_to_sign_hindi(self, client):
        """Convert Hindi text to sign data."""
        response = client.post("/api/text-to-sign", json={
            "text": "नमस्ते, पानी",
            "language": "hi",
        })
        assert response.status_code == 200
        data = response.json()
        word_keys = [w["word"] for w in data["words"]]
        assert "hello" in word_keys  # नमस्ते → hello
        assert "water" in word_keys  # पानी → water

    def test_text_to_sign_synonyms(self, client):
        """Synonyms should map to vocabulary words."""
        response = client.post("/api/text-to-sign", json={
            "text": "thanks buddy",
            "language": "en",
        })
        assert response.status_code == 200
        data = response.json()
        word_keys = [w["word"] for w in data["words"]]
        assert "thank_you" in word_keys  # thanks → thank_you
        assert "friend" in word_keys     # buddy → friend

    def test_text_to_sign_with_gif_urls(self, client):
        """Response should include GIF URLs for matched words."""
        response = client.post("/api/text-to-sign", json={
            "text": "water please",
            "language": "en",
        })
        data = response.json()
        for word_data in data["words"]:
            if word_data["found"]:
                assert word_data["gif_url"] != ""
                assert word_data["description"] != ""

    def test_text_to_sign_empty(self, client):
        """Empty text should return 400."""
        response = client.post("/api/text-to-sign", json={
            "text": "",
            "language": "en",
        })
        assert response.status_code == 422  # Pydantic min_length validation

    def test_text_to_sign_no_matches(self, client):
        """Text with no vocabulary matches returns empty words list."""
        response = client.post("/api/text-to-sign", json={
            "text": "xyzabc qwerty",
            "language": "en",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["matched_words"] == 0


# ─── Sign Demo Tests ─────────────────────────────────────────────

class TestSignDemo:

    def test_get_sign_demo(self, client):
        """Get sign demo for a valid word."""
        response = client.get("/api/signs/hello")
        assert response.status_code == 200
        data = response.json()
        assert data["word"] == "hello"
        assert data["gif_url"] != ""
        assert data["description"] != ""
        assert len(data["tips"]) > 0

    def test_get_sign_demo_not_found(self, client):
        """Invalid word returns 404."""
        response = client.get("/api/signs/xyzabc")
        assert response.status_code == 404

    def test_sign_demo_has_difficulty(self, client):
        """Sign demo should include difficulty level."""
        response = client.get("/api/signs/how_are_you")
        data = response.json()
        assert data["difficulty"] in ("easy", "medium", "hard")
        assert data["category"] != ""


# ─── AR Landmarks Tests ──────────────────────────────────────────

class TestARLandmarks:

    def test_ar_landmarks_valid(self, client, fake_frame):
        """AR landmarks should return pose data."""
        response = client.post("/api/ar/landmarks", json={
            "sessionId": "test-ar-1",
            "frame": fake_frame,
        })
        assert response.status_code == 200
        data = response.json()
        assert "pose_landmarks" in data
        assert "left_hand_landmarks" in data
        assert "right_hand_landmarks" in data
        assert "face_detected" in data
        assert "gesture_hint" in data

    def test_ar_landmarks_missing_session(self, client, fake_frame):
        """Missing session ID should return 400."""
        response = client.post("/api/ar/landmarks", json={
            "sessionId": "",
            "frame": fake_frame,
        })
        assert response.status_code == 400

    def test_ar_landmarks_invalid_frame(self, client):
        """Invalid base64 frame should return 400."""
        response = client.post("/api/ar/landmarks", json={
            "sessionId": "test-ar-2",
            "frame": "not-valid-base64!!!",
        })
        assert response.status_code == 400
