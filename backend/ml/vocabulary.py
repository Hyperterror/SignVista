"""
SignVista ML Vocabulary

Central word list & label mapping used by both ML inference and API routes.
Supports module-specific vocabularies for ISL Unified Project integration:
- Detection Module: 35 classes (1-9, A-Z)
- Recognition Module: 3 classes (Hello, How are you, Thank you)
- Translation Module: 10 classes (G, I, K, O, P, S, U, V, X, Y)
"""

import json
import os
from typing import Dict, List, Optional


# ─── Core Vocabulary (must match model training labels) ────────────

VOCABULARY: List[Dict] = [
    # Priority 1 — Core words (Matched with integrated model)
    {"word": "hello",        "display_name": "Hello",        "priority": 1, "index": 0},
    {"word": "how_are_you",  "display_name": "How Are You",  "priority": 1, "index": 1},
    {"word": "thank_you",    "display_name": "Thank You",    "priority": 1, "index": 2},

    # Priority 2 — Other words (indices will need matching later)
    {"word": "help",         "display_name": "Help",         "priority": 1, "index": 3},
    {"word": "water",        "display_name": "Water",        "priority": 1, "index": 4},
    {"word": "food",         "display_name": "Food",         "priority": 1, "index": 5},
    {"word": "yes",          "display_name": "Yes",          "priority": 1, "index": 6},
    {"word": "no",           "display_name": "No",           "priority": 1, "index": 7},
    {"word": "good",         "display_name": "Good",         "priority": 1, "index": 8},
    {"word": "bad",          "display_name": "Bad",          "priority": 1, "index": 9},
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


# ─── Module-Specific Vocabularies ────────────────────────────────

# Detection Module: 35 classes (1-9, A-Z)
DETECTION_VOCAB: List[Dict] = [
    # Numbers 1-9
    {"module": "detection", "index": 0, "word": "1", "display_name": "1", "priority": 2, "category": "number"},
    {"module": "detection", "index": 1, "word": "2", "display_name": "2", "priority": 2, "category": "number"},
    {"module": "detection", "index": 2, "word": "3", "display_name": "3", "priority": 2, "category": "number"},
    {"module": "detection", "index": 3, "word": "4", "display_name": "4", "priority": 2, "category": "number"},
    {"module": "detection", "index": 4, "word": "5", "display_name": "5", "priority": 2, "category": "number"},
    {"module": "detection", "index": 5, "word": "6", "display_name": "6", "priority": 2, "category": "number"},
    {"module": "detection", "index": 6, "word": "7", "display_name": "7", "priority": 2, "category": "number"},
    {"module": "detection", "index": 7, "word": "8", "display_name": "8", "priority": 2, "category": "number"},
    {"module": "detection", "index": 8, "word": "9", "display_name": "9", "priority": 2, "category": "number"},
    # Letters A-Z
    {"module": "detection", "index": 9, "word": "A", "display_name": "A", "priority": 2, "category": "letter"},
    {"module": "detection", "index": 10, "word": "B", "display_name": "B", "priority": 2, "category": "letter"},
    {"module": "detection", "index": 11, "word": "C", "display_name": "C", "priority": 2, "category": "letter"},
    {"module": "detection", "index": 12, "word": "D", "display_name": "D", "priority": 2, "category": "letter"},
    {"module": "detection", "index": 13, "word": "E", "display_name": "E", "priority": 2, "category": "letter"},
    {"module": "detection", "index": 14, "word": "F", "display_name": "F", "priority": 2, "category": "letter"},
    {"module": "detection", "index": 15, "word": "G", "display_name": "G", "priority": 2, "category": "letter"},
    {"module": "detection", "index": 16, "word": "H", "display_name": "H", "priority": 2, "category": "letter"},
    {"module": "detection", "index": 17, "word": "I", "display_name": "I", "priority": 2, "category": "letter"},
    {"module": "detection", "index": 18, "word": "J", "display_name": "J", "priority": 2, "category": "letter"},
    {"module": "detection", "index": 19, "word": "K", "display_name": "K", "priority": 2, "category": "letter"},
    {"module": "detection", "index": 20, "word": "L", "display_name": "L", "priority": 2, "category": "letter"},
    {"module": "detection", "index": 21, "word": "M", "display_name": "M", "priority": 2, "category": "letter"},
    {"module": "detection", "index": 22, "word": "N", "display_name": "N", "priority": 2, "category": "letter"},
    {"module": "detection", "index": 23, "word": "O", "display_name": "O", "priority": 2, "category": "letter"},
    {"module": "detection", "index": 24, "word": "P", "display_name": "P", "priority": 2, "category": "letter"},
    {"module": "detection", "index": 25, "word": "Q", "display_name": "Q", "priority": 2, "category": "letter"},
    {"module": "detection", "index": 26, "word": "R", "display_name": "R", "priority": 2, "category": "letter"},
    {"module": "detection", "index": 27, "word": "S", "display_name": "S", "priority": 2, "category": "letter"},
    {"module": "detection", "index": 28, "word": "T", "display_name": "T", "priority": 2, "category": "letter"},
    {"module": "detection", "index": 29, "word": "U", "display_name": "U", "priority": 2, "category": "letter"},
    {"module": "detection", "index": 30, "word": "V", "display_name": "V", "priority": 2, "category": "letter"},
    {"module": "detection", "index": 31, "word": "W", "display_name": "W", "priority": 2, "category": "letter"},
    {"module": "detection", "index": 32, "word": "X", "display_name": "X", "priority": 2, "category": "letter"},
    {"module": "detection", "index": 33, "word": "Y", "display_name": "Y", "priority": 2, "category": "letter"},
    {"module": "detection", "index": 34, "word": "Z", "display_name": "Z", "priority": 2, "category": "letter"},
]

# Recognition Module: 3 classes (Hello, How are you, Thank you)
RECOGNITION_VOCAB: List[Dict] = [
    {"module": "recognition", "index": 0, "word": "hello", "display_name": "Hello", "priority": 1, "category": "word"},
    {"module": "recognition", "index": 1, "word": "how_are_you", "display_name": "How Are You", "priority": 1, "category": "phrase"},
    {"module": "recognition", "index": 2, "word": "thank_you", "display_name": "Thank You", "priority": 1, "category": "phrase"},
]

# Translation Module: 10 classes (G, I, K, O, P, S, U, V, X, Y)
# Loaded from translation_classes.json
TRANSLATION_VOCAB: List[Dict] = []


def _load_translation_vocab() -> None:
    """Load translation vocabulary from translation_classes.json."""
    global TRANSLATION_VOCAB
    
    config_path = os.path.join("../ISL-Unified-Project", "config", "translation_classes.json")
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                translation_classes = json.load(f)
            
            TRANSLATION_VOCAB = [
                {
                    "module": "translation",
                    "index": int(idx),
                    "word": letter,
                    "display_name": letter,
                    "priority": 3,
                    "category": "letter"
                }
                for idx, letter in translation_classes.items()
            ]
        else:
            # Fallback to hardcoded values if file not found
            TRANSLATION_VOCAB = [
                {"module": "translation", "index": 0, "word": "G", "display_name": "G", "priority": 3, "category": "letter"},
                {"module": "translation", "index": 1, "word": "I", "display_name": "I", "priority": 3, "category": "letter"},
                {"module": "translation", "index": 2, "word": "K", "display_name": "K", "priority": 3, "category": "letter"},
                {"module": "translation", "index": 3, "word": "O", "display_name": "O", "priority": 3, "category": "letter"},
                {"module": "translation", "index": 4, "word": "P", "display_name": "P", "priority": 3, "category": "letter"},
                {"module": "translation", "index": 5, "word": "S", "display_name": "S", "priority": 3, "category": "letter"},
                {"module": "translation", "index": 6, "word": "U", "display_name": "U", "priority": 3, "category": "letter"},
                {"module": "translation", "index": 7, "word": "V", "display_name": "V", "priority": 3, "category": "letter"},
                {"module": "translation", "index": 8, "word": "X", "display_name": "X", "priority": 3, "category": "letter"},
                {"module": "translation", "index": 9, "word": "Y", "display_name": "Y", "priority": 3, "category": "letter"},
            ]
    except Exception as e:
        # Fallback to hardcoded values on any error
        TRANSLATION_VOCAB = [
            {"module": "translation", "index": 0, "word": "G", "display_name": "G", "priority": 3, "category": "letter"},
            {"module": "translation", "index": 1, "word": "I", "display_name": "I", "priority": 3, "category": "letter"},
            {"module": "translation", "index": 2, "word": "K", "display_name": "K", "priority": 3, "category": "letter"},
            {"module": "translation", "index": 3, "word": "O", "display_name": "O", "priority": 3, "category": "letter"},
            {"module": "translation", "index": 4, "word": "P", "display_name": "P", "priority": 3, "category": "letter"},
            {"module": "translation", "index": 5, "word": "S", "display_name": "S", "priority": 3, "category": "letter"},
            {"module": "translation", "index": 6, "word": "U", "display_name": "U", "priority": 3, "category": "letter"},
            {"module": "translation", "index": 7, "word": "V", "display_name": "V", "priority": 3, "category": "letter"},
            {"module": "translation", "index": 8, "word": "X", "display_name": "X", "priority": 3, "category": "letter"},
            {"module": "translation", "index": 9, "word": "Y", "display_name": "Y", "priority": 3, "category": "letter"},
        ]


# Load translation vocabulary on module import
_load_translation_vocab()


# ─── Module Registry ──────────────────────────────────────────────

# Registry of module vocabularies
_MODULE_VOCABULARIES: Dict[str, List[Dict]] = {
    "detection": DETECTION_VOCAB,
    "recognition": RECOGNITION_VOCAB,
    "translation": TRANSLATION_VOCAB,
}

# Module-specific index to word mappings
_MODULE_INDEX_TO_WORD: Dict[str, Dict[int, str]] = {
    module: {entry["index"]: entry["word"] for entry in vocab}
    for module, vocab in _MODULE_VOCABULARIES.items()
}

# Module-specific word to display name mappings
_MODULE_WORD_DISPLAY: Dict[str, Dict[str, str]] = {
    module: {entry["word"]: entry["display_name"] for entry in vocab}
    for module, vocab in _MODULE_VOCABULARIES.items()
}


# ─── Module-Specific Functions ───────────────────────────────────

def register_module_vocabulary(module_name: str, vocab: List[Dict]) -> None:
    """
    Register vocabulary for a module.
    
    Args:
        module_name: Name of the module (e.g., "detection", "recognition", "translation")
        vocab: List of vocabulary entries with keys: module, index, word, display_name, priority, category
    """
    _MODULE_VOCABULARIES[module_name] = vocab
    _MODULE_INDEX_TO_WORD[module_name] = {entry["index"]: entry["word"] for entry in vocab}
    _MODULE_WORD_DISPLAY[module_name] = {entry["word"]: entry["display_name"] for entry in vocab}


def get_word_by_module_index(module_name: str, index: int) -> str:
    """
    Get word from module-specific index.
    
    Args:
        module_name: Name of the module
        index: Class index from the module's model output
        
    Returns:
        Word string corresponding to the index, or "unknown" if not found
    """
    if module_name not in _MODULE_INDEX_TO_WORD:
        return "unknown"
    return _MODULE_INDEX_TO_WORD[module_name].get(index, "unknown")


def get_display_name(word: str, module_name: Optional[str] = None) -> str:
    """
    Get display name for a word.
    
    Args:
        word: Word string
        module_name: Optional module name to search in specific module vocabulary
        
    Returns:
        Display name for the word
    """
    # If module specified, search in that module first
    if module_name and module_name in _MODULE_WORD_DISPLAY:
        if word in _MODULE_WORD_DISPLAY[module_name]:
            return _MODULE_WORD_DISPLAY[module_name][word]
    
    # Search in all module vocabularies
    for module_vocab in _MODULE_WORD_DISPLAY.values():
        if word in module_vocab:
            return module_vocab[word]
    
    # Fallback to legacy vocabulary
    if word in WORD_DISPLAY:
        return WORD_DISPLAY[word]
    
    # Default: capitalize the word
    return word.replace("_", " ").title()


def get_unified_vocabulary() -> List[Dict]:
    """
    Get merged vocabulary from all modules.
    
    Returns:
        List of all vocabulary entries from all modules, with duplicates resolved by priority
    """
    unified = []
    seen_words = {}
    
    # Collect all entries from all modules
    all_entries = []
    for module_name, vocab in _MODULE_VOCABULARIES.items():
        all_entries.extend(vocab)
    
    # Sort by priority (lower number = higher priority)
    all_entries.sort(key=lambda x: x.get("priority", 999))
    
    # Add entries, keeping only the highest priority version of each word
    for entry in all_entries:
        word = entry["word"]
        if word not in seen_words:
            unified.append(entry)
            seen_words[word] = entry["module"]
    
    return unified


def resolve_vocabulary_conflict(word: str, modules: List[str]) -> str:
    """
    Handle same word from different modules by selecting the highest priority source.
    
    Args:
        word: The word that appears in multiple modules
        modules: List of module names where the word appears
        
    Returns:
        The module name with highest priority for this word
    """
    if not modules:
        return ""
    
    # Find the entry with lowest priority number (highest priority)
    best_module = modules[0]
    best_priority = 999
    
    for module_name in modules:
        if module_name in _MODULE_VOCABULARIES:
            for entry in _MODULE_VOCABULARIES[module_name]:
                if entry["word"] == word:
                    priority = entry.get("priority", 999)
                    if priority < best_priority:
                        best_priority = priority
                        best_module = module_name
                    break
    
    return best_module
