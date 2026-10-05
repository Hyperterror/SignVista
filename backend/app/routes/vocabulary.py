"""
SignVista — Vocabulary Route

GET /api/vocabulary
Returns the full word list available for learning, practice, and game modes.

Ayush: Use this to populate word dropdowns and game challenge pools.
"""

from fastapi import APIRouter

from app.schemas import VocabularyResponse, WordInfo
from ml.inference import get_recognizable_words
from ml.vocabulary import DETECTION_VOCAB, TRANSLATION_VOCAB, VOCABULARY

router = APIRouter(prefix="/api", tags=["Vocabulary"])


@router.get("/vocabulary", response_model=VocabularyResponse)
def get_vocabulary():
    """
    Get all available ISL words.

    Returns word list with display names, priority tiers, and model indices.

    Ayush calls: GET /api/vocabulary

    Response:
    ```json
    {
        "total": 15,
        "words": [
            {"word": "hello", "display_name": "Hello", "priority": 1, "index": 0},
            {"word": "thank_you", "display_name": "Thank You", "priority": 1, "index": 1},
            ...
        ]
    }
    ```
    """
    recognizable = {w.lower() for w in get_recognizable_words()}
    words = [
        WordInfo(
            word=v["word"],
            display_name=v["display_name"],
            priority=v["priority"],
            index=v["index"],
            recognizable=v["word"].lower() in recognizable,
        )
        for v in VOCABULARY
    ]
    # Static letters/digits the loaded models can recognize
    known = {w.word for w in words}
    for v in DETECTION_VOCAB + TRANSLATION_VOCAB:
        if v["word"] in known or v["word"].lower() not in recognizable:
            continue
        known.add(v["word"])
        words.append(WordInfo(word=v["word"], display_name=v["display_name"],
                              priority=v["priority"], index=v["index"], recognizable=True))

    return VocabularyResponse(total=len(words), words=words)
