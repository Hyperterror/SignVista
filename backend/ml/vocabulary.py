"""
SignVista ML Vocabulary

Central word list & label mapping used by both ML inference and API routes.
Ishit: Update VOCABULARY to match your trained model's label order.
"""

from typing import Dict, List


# ─── Core Vocabulary (must match model training labels) ────────────

VOCABULARY: List[Dict] = [
    # Priority 1 — Core 10 words
    {"word": "hello",        "display_name": "Hello",        "priority": 1, "index": 0},
    {"word": "thank_you",    "display_name": "Thank You",    "priority": 1, "index": 1},
    {"word": "how_are_you",  "display_name": "How Are You",  "priority": 1, "index": 2},
    {"word": "help",         "display_name": "Help",         "priority": 1, "index": 3},
    {"word": "water",        "display_name": "Water",        "priority": 1, "index": 4},
    {"word": "food",         "display_name": "Food",         "priority": 1, "index": 5},
    {"word": "yes",          "display_name": "Yes",          "priority": 1, "index": 6},
    {"word": "no",           "display_name": "No",           "priority": 1, "index": 7},
    {"word": "good",         "display_name": "Good",         "priority": 1, "index": 8},
    {"word": "bad",          "display_name": "Bad",          "priority": 1, "index": 9},

    # Priority 2 — Extended 5 words
    {"word": "sorry",        "display_name": "Sorry",        "priority": 2, "index": 10},
    {"word": "please",       "display_name": "Please",       "priority": 2, "index": 11},
    {"word": "name",         "display_name": "Name",         "priority": 2, "index": 12},
    {"word": "family",       "display_name": "Family",       "priority": 2, "index": 13},
    {"word": "friend",       "display_name": "Friend",       "priority": 2, "index": 14},
]


# ─── Lookup Helpers ───────────────────────────────────────────────

# Index → word string
INDEX_TO_WORD: Dict[int, str] = {v["index"]: v["word"] for v in VOCABULARY}

# Word string → index
WORD_TO_INDEX: Dict[str, int] = {v["word"]: v["index"] for v in VOCABULARY}

# Word string → display name
WORD_DISPLAY: Dict[str, str] = {v["word"]: v["display_name"] for v in VOCABULARY}

# All word strings
WORD_LIST: List[str] = [v["word"] for v in VOCABULARY]

# Number of classes
NUM_CLASSES: int = len(VOCABULARY)


def get_word_by_index(index: int) -> str:
    """Get word string from model output index."""
    return INDEX_TO_WORD.get(index, "unknown")


def get_index_by_word(word: str) -> int:
    """Get model label index from word string."""
    return WORD_TO_INDEX.get(word.lower(), -1)


def is_valid_word(word: str) -> bool:
    """Check if a word is in the vocabulary."""
    return word.lower() in WORD_TO_INDEX
