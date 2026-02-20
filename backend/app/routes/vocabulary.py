"""
SignVista — Vocabulary Route

GET /api/vocabulary
Returns the full word list available for learning, practice, and game modes.

Ayush: Use this to populate word dropdowns and game challenge pools.
"""

from fastapi import APIRouter

from app.schemas import VocabularyResponse, WordInfo
from ml.vocabulary import VOCABULARY

router = APIRouter(prefix="/api", tags=["Vocabulary"])


@router.get("/vocabulary", response_model=VocabularyResponse)
async def get_vocabulary():
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
    words = [
        WordInfo(
            word=v["word"],
            display_name=v["display_name"],
            priority=v["priority"],
            index=v["index"],
        )
        for v in VOCABULARY
    ]

    return VocabularyResponse(total=len(words), words=words)
