"""
SignVista — Text to Sign Language Route

POST /api/text-to-sign — Convert input text to corresponding ISL sign GIFs
GET  /api/signs/{word}  — Get sign demo data for a single word

This powers both the "Text → Sign" and "Voice → Sign" features.
For voice: Ayush captures speech via Web Speech API → sends text here.

Ayush: Send any text, we'll tokenize it and return matched sign GIFs.
"""

import logging
import re
from typing import List

from fastapi import APIRouter, HTTPException

from app.schemas import (
    TextToSignRequest,
    TextToSignResponse,
    SignWordData,
    SignDemoResponse,
)
from ml.sign_demos import SIGN_DEMOS, get_sign_demo
from ml.vocabulary import WORD_DISPLAY, WORD_TO_INDEX, is_valid_word

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Text-to-Sign"])


# ─── Hindi → English Word Mapping (basic) ─────────────────────────
# For Hindi input, map common Hindi words to their English vocabulary keys

HINDI_TO_ENGLISH = {
    "नमस्ते": "hello",
    "धन्यवाद": "thank_you",
    "शुक्रिया": "thank_you",
    "मदद": "help",
    "सहायता": "help",
    "पानी": "water",
    "जल": "water",
    "खाना": "food",
    "भोजन": "food",
    "हाँ": "yes",
    "हां": "yes",
    "नहीं": "no",
    "अच्छा": "good",
    "बुरा": "bad",
    "खराब": "bad",
    "माफ़": "sorry",
    "माफ": "sorry",
    "कृपया": "please",
    "नाम": "name",
    "परिवार": "family",
    "दोस्त": "friend",
    "मित्र": "friend",
    "कैसे हैं": "how_are_you",
    "कैसे हो": "how_are_you",
}

# Common English synonyms/phrases → vocabulary keys
ENGLISH_SYNONYMS = {
    "hi": "hello",
    "hey": "hello",
    "thanks": "thank_you",
    "thankyou": "thank_you",
    "howdy": "hello",
    "how are you": "how_are_you",
    "how r u": "how_are_you",
    "thirsty": "water",
    "drink": "water",
    "hungry": "food",
    "eat": "food",
    "okay": "yes",
    "ok": "yes",
    "nope": "no",
    "great": "good",
    "nice": "good",
    "terrible": "bad",
    "awful": "bad",
    "excuse me": "sorry",
    "pardon": "sorry",
    "buddy": "friend",
    "pal": "friend",
}


class ISLGrammarEngine:
    """
    Restructures English sentences into ISL (Time-Topic-Comment) grammar.
    Example: "I am going to the market tomorrow" -> "Tomorrow I go market"
    """
    @staticmethod
    def restructure(text: str) -> str:
        text = text.lower().strip()
        # Remove punctuation
        text = re.sub(r'[^\w\s]', '', text)
        
        words = text.split()
        if not words:
            return ""

        # Basic Time Extraction
        time_indicators = ["tomorrow", "yesterday", "today", "now", "monday", "tuesday", "morning", "night", "soon"]
        times = [w for w in words if w in time_indicators]
        others = [w for w in words if w not in time_indicators]

        # Remove common "stop" words for ISL (articles, auxiliary verbs)
        stop_words = ["is", "am", "are", "the", "a", "an", "to", "be", "been", "was", "were"]
        others = [w for w in others if w not in stop_words]

        # Simple re-ordering: Time + Topic + Comment
        # This is a heuristic for hackathon version
        reordered = times + others
        return " ".join(reordered)


def _tokenize_text(text: str, language: str) -> List[str]:
    """
    Split text into tokens and map to vocabulary words.
    Handles both English and Hindi input.
    Includes alphabet fallback for unknown words.
    """
    # 1. Restructure logic
    if language == "en":
        text = ISLGrammarEngine.restructure(text)
    else:
        text = text.strip().lower()

    matched_tokens = []

    # Map chunks or words
    words = text.split()
    for w in words:
        # Check if direct match or synonym
        if is_valid_word(w):
            matched_tokens.append(w)
        elif w in ENGLISH_SYNONYMS:
            matched_tokens.append(ENGLISH_SYNONYMS[w])
        elif language == "hi" and w in HINDI_TO_ENGLISH:
            matched_tokens.append(HINDI_TO_ENGLISH[w])
        else:
            # ALPHABET FALLBACK
            # Split the unknown word into individual letters
            for char in w:
                if char.isalpha():
                    matched_tokens.append(char)

    return matched_tokens


@router.post("/text-to-sign", response_model=TextToSignResponse)
async def text_to_sign(request: TextToSignRequest):
    """
    Convert text to sign language GIF demonstrations.

    Tokenizes input text, looks up each word in the sign database,
    and returns GIF URLs + descriptions for matched words.

    Also used for Voice-to-Sign: Ayush captures speech via Web Speech API,
    sends the transcribed text here.

    Ayush sends:
    ```json
    {
        "text": "Hello, how are you? I need water please",
        "language": "en"
    }
    ```

    Response:
    ```json
    {
        "original_text": "Hello, how are you? I need water please",
        "words": [
            {"word": "hello", "found": true, "gif_url": "/assets/signs/hello.gif", ...},
            {"word": "how_are_you", "found": true, "gif_url": "/assets/signs/how_are_you.gif", ...},
            {"word": "water", "found": true, "gif_url": "/assets/signs/water.gif", ...},
            {"word": "please", "found": true, "gif_url": "/assets/signs/please.gif", ...}
        ],
        "total_words": 4,
        "matched_words": 4,
        "unmatched_words": []
    }
    ```
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    lang = request.language.lower() if request.language else "en"
    tokens = _tokenize_text(request.text, lang)

    # Build sign data for each matched word
    sign_words = []
    unmatched = []

    for word_key in tokens:
        demo = get_sign_demo(word_key)
        if demo:
            sign_words.append(SignWordData(
                word=word_key,
                display_name=WORD_DISPLAY.get(word_key, word_key),
                found=True,
                gif_url=demo["gif_url"],
                description=demo["description"],
                duration_ms=demo.get("duration_ms", 2000),
            ))
        else:
            sign_words.append(SignWordData(
                word=word_key,
                display_name=word_key,
                found=False,
                gif_url="",
                description=f"Sign for '{word_key}' not yet in our database.",
                duration_ms=0,
            ))
            unmatched.append(word_key)

    # If no tokens matched at all, try the whole text as-is
    if not tokens:
        # Split by spaces and report unmatched
        raw_words = request.text.strip().split()
        for rw in raw_words:
            clean = re.sub(r'[^a-zA-Z\u0900-\u097F]', '', rw).lower()
            if clean:
                unmatched.append(clean)

    return TextToSignResponse(
        original_text=request.text,
        words=sign_words,
        total_words=len(sign_words),
        matched_words=sum(1 for w in sign_words if w.found),
        unmatched_words=unmatched,
    )


@router.get("/signs/{word}", response_model=SignDemoResponse)
async def get_sign(word: str):
    """
    Get detailed sign demonstration for a single word.
    Returns GIF URL, description, tips, and difficulty.

    Ayush calls: GET /api/signs/hello
    """
    demo = get_sign_demo(word.lower())
    if demo is None:
        raise HTTPException(
            status_code=404,
            detail=f"Sign demo for '{word}' not found. Use GET /api/vocabulary to see available words."
        )

    return SignDemoResponse(
        word=word.lower(),
        display_name=WORD_DISPLAY.get(word.lower(), word),
        gif_url=demo["gif_url"],
        description=demo["description"],
        tips=demo.get("tips", []),
        difficulty=demo.get("difficulty", "easy"),
        category=demo.get("category", "common"),
    )
