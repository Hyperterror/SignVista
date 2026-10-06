"""
Tests for Phase 2 — Profile, Text-to-Sign, Sign Demos, AR Landmarks
"""



# ─── Profile Tests ────────────────────────────────────────────────

class TestProfile:

    def test_update_profile(self, auth_client):
        response = auth_client.post("/api/profile", json={
            "name": "Ravi Kumar",
            "email": "Ravi@Example.com",
            "phone": "+91 98765 00001",
            "preferred_language": "en",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Ravi Kumar"
        assert data["email"] == "ravi@example.com"
        assert data["phone"] == "+919876500001"
        assert "Ravi Kumar" in data["welcome_message"]
        assert len(data["welcome_sign_data"]) > 0

    def test_phone_change_keeps_session_valid(self, auth_client):
        """Tokens are bound to user_id, so changing the phone must not log the user out."""
        auth_client.post("/api/profile", json={"name": "A", "email": "a1@example.com", "phone": "9123456780"})
        assert auth_client.get("/api/auth/me").status_code == 200

    def test_update_profile_hindi(self, auth_client):
        response = auth_client.post("/api/profile", json={
            "name": "रवि", "email": "ravi.hi@example.com", "preferred_language": "hi",
        })
        assert response.status_code == 200
        assert "स्वागत" in response.json()["welcome_message"]

    def test_get_profile(self, auth_client):
        response = auth_client.get(f"/api/profile/{auth_client.user_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Test User"

    def test_get_other_profile_forbidden(self, auth_client):
        assert auth_client.get("/api/profile/nonexistent-user").status_code == 403

    def test_update_profile_missing_name(self, auth_client):
        response = auth_client.post("/api/profile", json={"name": "", "email": "test@example.com"})
        assert response.status_code == 422

    def test_update_profile_invalid_email(self, auth_client):
        response = auth_client.post("/api/profile", json={"name": "Test", "email": "not-an-email"})
        assert response.status_code == 422

    def test_duplicate_phone_rejected(self, client):
        from tests.conftest import register
        other = register(client, name="Other")
        me = register(client, name="Me")  # client is now logged in as "Me"
        response = client.post("/api/profile", json={"name": "Me", "email": "me2@example.com", "phone": other["phone"]})
        assert response.status_code == 400
        assert me["sessionId"] != other["sessionId"]


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
                # gif_url is empty until the media file is added under backend/static
                assert isinstance(word_data["gif_url"], str)
                assert word_data["description"] != ""

    def test_text_to_sign_empty(self, client):
        """Empty text should return 400."""
        response = client.post("/api/text-to-sign", json={
            "text": "",
            "language": "en",
        })
        assert response.status_code == 422  # Pydantic min_length validation

    def test_text_to_sign_unknown_words_are_fingerspelled(self, client):
        """Unknown English words fall back to finger-spelling letter by letter."""
        data = client.post("/api/text-to-sign", json={"text": "xyz", "language": "en"}).json()
        assert [w["word"] for w in data["words"]] == ["x", "y", "z"]

    def test_text_to_sign_multiword_phrase(self, client):
        data = client.post("/api/text-to-sign", json={"text": "How are you?", "language": "en"}).json()
        assert [w["word"] for w in data["words"]] == ["how_are_you"]

    def test_text_to_sign_unknown_hindi_not_spelled_in_english(self, client):
        data = client.post("/api/text-to-sign", json={"text": "किताब", "language": "hi"}).json()
        assert data["matched_words"] == 0
        assert data["unmatched_words"] == ["किताब"]


# ─── Sign Demo Tests ─────────────────────────────────────────────

class TestSignDemo:

    def test_get_sign_demo(self, client):
        """Get sign demo for a valid word."""
        response = client.get("/api/signs/hello")
        assert response.status_code == 200
        data = response.json()
        assert data["word"] == "hello"
        assert isinstance(data["gif_url"], str)
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

    def test_ar_landmarks_requires_auth(self, client, fake_frame):
        assert client.post("/api/ar/landmarks", json={"frame": fake_frame}).status_code == 401

    def test_ar_landmarks_valid(self, auth_client, fake_frame):
        response = auth_client.post("/api/ar/landmarks", json={"frame": fake_frame})
        assert response.status_code == 200
        data = response.json()
        assert {"pose_landmarks", "left_hand_landmarks", "right_hand_landmarks",
                "face_detected", "gesture_hint", "prediction"} <= data.keys()

    def test_ar_landmarks_foreign_session(self, auth_client, fake_frame):
        response = auth_client.post("/api/ar/landmarks", json={"sessionId": "other", "frame": fake_frame})
        assert response.status_code == 403

    def test_ar_landmarks_invalid_frame(self, auth_client):
        response = auth_client.post("/api/ar/landmarks", json={"frame": "not-valid-base64!!!"})
        assert response.status_code == 400
