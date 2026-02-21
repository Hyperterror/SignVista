"""Tests for vocabulary manager multi-module support."""

import pytest
from ml.vocabulary import (
    get_word_by_module_index,
    get_display_name,
    get_unified_vocabulary,
    resolve_vocabulary_conflict,
    register_module_vocabulary,
    DETECTION_VOCAB,
    RECOGNITION_VOCAB,
    TRANSLATION_VOCAB,
)


class TestVocabularyManager:
    """Test vocabulary manager functionality."""

    def test_detection_vocab_size(self):
        """Detection vocabulary should have 35 classes (1-9, A-Z)."""
        assert len(DETECTION_VOCAB) == 35

    def test_recognition_vocab_size(self):
        """Recognition vocabulary should have 3 classes."""
        assert len(RECOGNITION_VOCAB) == 3

    def test_translation_vocab_size(self):
        """Translation vocabulary should have 10 classes."""
        assert len(TRANSLATION_VOCAB) == 10

    def test_get_word_by_module_index_detection(self):
        """Should map detection indices to words correctly."""
        # Test number
        assert get_word_by_module_index("detection", 0) == "1"
        # Test letter
        assert get_word_by_module_index("detection", 9) == "A"
        assert get_word_by_module_index("detection", 34) == "Z"

    def test_get_word_by_module_index_recognition(self):
        """Should map recognition indices to words correctly."""
        assert get_word_by_module_index("recognition", 0) == "hello"
        assert get_word_by_module_index("recognition", 1) == "how_are_you"
        assert get_word_by_module_index("recognition", 2) == "thank_you"

    def test_get_word_by_module_index_translation(self):
        """Should map translation indices to words correctly."""
        # Translation vocab has 10 classes: G, I, K, O, P, S, U, V, X, Y
        word = get_word_by_module_index("translation", 0)
        assert word in ["G", "I", "K", "O", "P", "S", "U", "V", "X", "Y"]

    def test_get_word_by_module_index_invalid(self):
        """Should return 'unknown' for invalid indices."""
        assert get_word_by_module_index("detection", 999) == "unknown"
        assert get_word_by_module_index("invalid_module", 0) == "unknown"

    def test_get_display_name_detection(self):
        """Should get display names for detection words."""
        assert get_display_name("A", "detection") == "A"
        assert get_display_name("1", "detection") == "1"

    def test_get_display_name_recognition(self):
        """Should get display names for recognition words."""
        assert get_display_name("hello", "recognition") == "Hello"
        assert get_display_name("how_are_you", "recognition") == "How Are You"

    def test_get_display_name_fallback(self):
        """Should fallback to title case for unknown words."""
        display = get_display_name("unknown_word")
        assert display == "Unknown Word"

    def test_get_unified_vocabulary(self):
        """Should merge vocabularies from all modules."""
        unified = get_unified_vocabulary()
        
        # Should have entries from all modules
        assert len(unified) > 0
        
        # Should contain detection and recognition entries
        # Note: Translation entries may not appear if all their words
        # are duplicates with higher priority modules (detection has A-Z)
        modules = {entry["module"] for entry in unified}
        assert "detection" in modules
        assert "recognition" in modules
        
        # Verify we have a reasonable number of entries
        # Detection: 35, Recognition: 3, some overlap with translation
        assert len(unified) >= 35

    def test_unified_vocabulary_no_duplicates(self):
        """Unified vocabulary should not have duplicate words."""
        unified = get_unified_vocabulary()
        words = [entry["word"] for entry in unified]
        
        # Check for duplicates
        assert len(words) == len(set(words)), "Unified vocabulary has duplicate words"

    def test_resolve_vocabulary_conflict(self):
        """Should resolve conflicts by priority."""
        # Recognition has priority 1, detection has priority 2
        # If both have "hello", recognition should win
        result = resolve_vocabulary_conflict("hello", ["detection", "recognition"])
        assert result == "recognition"

    def test_register_module_vocabulary(self):
        """Should allow registering new module vocabularies."""
        test_vocab = [
            {"module": "test", "index": 0, "word": "test_word", "display_name": "Test Word", "priority": 5, "category": "test"}
        ]
        
        register_module_vocabulary("test", test_vocab)
        
        # Should be able to retrieve the word
        assert get_word_by_module_index("test", 0) == "test_word"
        assert get_display_name("test_word", "test") == "Test Word"

    def test_detection_vocab_structure(self):
        """Detection vocabulary entries should have required fields."""
        for entry in DETECTION_VOCAB:
            assert "module" in entry
            assert "index" in entry
            assert "word" in entry
            assert "display_name" in entry
            assert "priority" in entry
            assert "category" in entry
            assert entry["module"] == "detection"

    def test_recognition_vocab_structure(self):
        """Recognition vocabulary entries should have required fields."""
        for entry in RECOGNITION_VOCAB:
            assert "module" in entry
            assert "index" in entry
            assert "word" in entry
            assert "display_name" in entry
            assert "priority" in entry
            assert "category" in entry
            assert entry["module"] == "recognition"

    def test_translation_vocab_structure(self):
        """Translation vocabulary entries should have required fields."""
        for entry in TRANSLATION_VOCAB:
            assert "module" in entry
            assert "index" in entry
            assert "word" in entry
            assert "display_name" in entry
            assert "priority" in entry
            assert "category" in entry
            assert entry["module"] == "translation"

    def test_detection_vocab_indices_sequential(self):
        """Detection vocabulary indices should be sequential from 0 to 34."""
        indices = sorted([entry["index"] for entry in DETECTION_VOCAB])
        assert indices == list(range(35))

    def test_recognition_vocab_indices_sequential(self):
        """Recognition vocabulary indices should be sequential from 0 to 2."""
        indices = sorted([entry["index"] for entry in RECOGNITION_VOCAB])
        assert indices == list(range(3))

    def test_translation_vocab_indices_sequential(self):
        """Translation vocabulary indices should be sequential from 0 to 9."""
        indices = sorted([entry["index"] for entry in TRANSLATION_VOCAB])
        assert indices == list(range(10))
