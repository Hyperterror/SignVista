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
import unicodedata
from typing import Dict, List

from fastapi import APIRouter, HTTPException

from app.schemas import (
    TextToSignRequest,
    TextToSignResponse,
    SignWordData,
    SignDemoResponse,
)
from ml.sign_demos import SIGN_DEMOS, get_sign_demo
from ml.vocabulary import get_display_name

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


TIME_INDICATORS = {"tomorrow", "yesterday", "today", "now", "monday", "tuesday", "wednesday",
                   "thursday", "friday", "saturday", "sunday", "morning", "night", "evening", "soon", "later"}
ISL_STOP_WORDS = {"is", "am", "are", "the", "a", "an", "to", "be", "been", "was", "were", "of"}
MAX_PHRASE_WORDS = 3


class ISLGrammarEngine:
    """
    Restructures English token lists into ISL (Time-Topic-Comment) order.
    Example: "I am going to the market tomorrow" -> "tomorrow i going market"
    """
    @staticmethod
    def restructure_tokens(tokens: List[str]) -> List[str]:
        times = [t for t in tokens if t in TIME_INDICATORS]
        others = [t for t in tokens if t not in TIME_INDICATORS and t not in ISL_STOP_WORDS]
        return times + others

    @staticmethod
    def restructure(text: str) -> str:
        words = re.sub(r"[^\w\s]", "", text.lower()).split()
        return " ".join(ISLGrammarEngine.restructure_tokens(words))


def _phrase_lookup(language: str) -> Dict[str, str]:
    """Phrase (space separated, lower-case) -> sign key."""
    table: Dict[str, str] = {}
    for key in SIGN_DEMOS:
        if len(key) > 1:  # skip alphabet letters
            table[key.replace("_", " ")] = key
    table.update(ENGLISH_SYNONYMS)
    if language == "hi":
        table.update(HINDI_TO_ENGLISH)
    return table


def _tokenize_text(text: str, language: str) -> List[str]:
    """
    Map text to sign keys:
    1. longest-match multi-word phrases ("how are you" -> how_are_you)
    2. single words and synonyms
    3. finger-spelling fallback for unknown English words (a-z only)
    English input is reordered into ISL Time-Topic-Comment order first.
    """
    table = _phrase_lookup(language)
    # Keep letters, digits, marks (needed for Devanagari vowel signs) and spaces
    cleaned = "".join(ch if (ch.isalnum() or ch.isspace() or unicodedata.category(ch).startswith("M")) else " "
                      for ch in text.lower())
    words = cleaned.split()

    # Pass 1: phrase matching on the original order (stop words still present)
    units: List[str] = []
    i = 0
    while i < len(words):
        for n in range(min(MAX_PHRASE_WORDS, len(words) - i), 1, -1):
            phrase = " ".join(words[i:i + n])
            if phrase in table:
                units.append(table[phrase])
                i += n
                break
        else:
            units.append(words[i])
            i += 1

    if language == "en":
        units = ISLGrammarEngine.restructure_tokens(units)

    tokens: List[str] = []
    for w in units:
        if w in SIGN_DEMOS and len(w) > 1:
            tokens.append(w)
        elif w in table:
            tokens.append(table[w])
        elif re.fullmatch(r"[a-z]+", w):
            tokens.extend(w)  # finger-spell
        else:
            tokens.append(w)  # unmatched (reported as not found)
    return tokens


@router.post("/text-to-sign", response_model=TextToSignResponse)
def text_to_sign(request: TextToSignRequest):
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
                display_name=get_display_name(word_key),
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
def get_sign(word: str):
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
        display_name=get_display_name(word.lower()),
        gif_url=demo["gif_url"],
        description=demo["description"],
        tips=demo.get("tips", []),
        difficulty=demo.get("difficulty", "easy"),
        category=demo.get("category", "common"),
    )
