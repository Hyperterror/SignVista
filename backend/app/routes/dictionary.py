"""
SignVista — Dictionary Route

GET /api/dictionary
GET /api/dictionary/{word}

Ayush: Use this for the browsable ISL dictionary.
       Supports filtering by category, difficulty, and search term.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Set

from app.schemas import DictionaryResponse, DictionaryEntry
from ml.sign_demos import SIGN_DEMOS
from ml.vocabulary import WORD_DISPLAY, is_valid_word

router = APIRouter(prefix="/api", tags=["Dictionary"])


@router.get("/dictionary", response_model=DictionaryResponse)
async def get_dictionary(
    category: Optional[str] = Query(None, description="Filter by category (e.g., greetings, common)"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty (easy, medium, hard)"),
    search: Optional[str] = Query(None, description="Search by word name")
):
    """
    Get all reachable words in the ISL dictionary with metadata.
    """
    entries = []
    categories: Set[str] = set()
    difficulties: Set[str] = set()

    for word_key, demo in SIGN_DEMOS.items():
        categories.add(demo.get("category", "common"))
        difficulties.add(demo.get("difficulty", "easy"))
        
        # Filter logic
        if category and demo.get("category") != category:
            continue
        if difficulty and demo.get("difficulty") != difficulty:
            continue
        if search and search.lower() not in word_key.lower():
            continue
            
        entries.append(DictionaryEntry(
            word=word_key,
            display_name=WORD_DISPLAY.get(word_key, word_key),
            hindi_name=demo.get("hindi_name", ""),
            category=demo.get("category", "common"),
            difficulty=demo.get("difficulty", "easy"),
            gif_url=demo.get("gif_url", ""),
            description=demo.get("description", ""),
            tips=demo.get("tips", [])
        ))

    return DictionaryResponse(
        total=len(entries),
        categories=sorted(list(categories)),
        difficulties=sorted(list(difficulties)),
        words=entries
    )


@router.get("/dictionary/{word}", response_model=DictionaryEntry)
async def get_dictionary_entry(word: str):
    """
    Get full metadata for a single word.
    """
    word_key = word.lower()
    demo = SIGN_DEMOS.get(word_key)
    
    if not demo:
        raise HTTPException(status_code=404, detail=f"Word '{word}' not found in dictionary")
        
    return DictionaryEntry(
        word=word_key,
        display_name=WORD_DISPLAY.get(word_key, word_key),
        hindi_name=demo.get("hindi_name", ""),
        category=demo.get("category", "common"),
        difficulty=demo.get("difficulty", "easy"),
        gif_url=demo.get("gif_url", ""),
        description=demo.get("description", ""),
        tips=demo.get("tips", [])
    )
