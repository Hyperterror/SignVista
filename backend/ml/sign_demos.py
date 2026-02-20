"""
SignVista — Sign Demo Data

GIF URLs, descriptions, and tips for each ISL word in the vocabulary.
This is the asset database for text-to-sign conversion and learn mode demos.

Ishit/Ayush: Replace placeholder GIF URLs with actual recorded demonstrations.
"""

from typing import Dict, List


# ─── Sign Demo Database ───────────────────────────────────────────
# Each word has: gif_url, description, tips, difficulty, category

SIGN_DEMOS: Dict[str, Dict] = {
    "hello": {
        "gif_url": "/assets/signs/hello.gif",
        "description": "Raise your right hand to forehead level with palm facing outward, then move it forward in a small arc — like a salute wave.",
        "tips": [
            "Keep fingers together and straight",
            "Start from near your forehead",
            "Make a smooth outward motion",
        ],
        "difficulty": "easy",
        "category": "greetings",
        "duration_ms": 1500,
        "hindi_name": "नमस्ते",
    },
    "thank_you": {
        "gif_url": "/assets/signs/thank_you.gif",
        "description": "Touch your chin with the tips of your flat hand, then move the hand forward and slightly down — as if blowing a kiss of gratitude.",
        "tips": [
            "Fingertips touch the chin first",
            "Move outward smoothly",
            "Slight downward arc at the end",
        ],
        "difficulty": "easy",
        "category": "greetings",
        "duration_ms": 2000,
        "hindi_name": "धन्यवाद",
    },
    "how_are_you": {
        "gif_url": "/assets/signs/how_are_you.gif",
        "description": "Point index fingers at the other person, then make a questioning expression while moving both hands slightly upward with palms up.",
        "tips": [
            "Facial expression is important — look questioning",
            "Both hands move upward together",
            "Keep palms facing up",
        ],
        "difficulty": "medium",
        "category": "greetings",
        "duration_ms": 2500,
        "hindi_name": "आप कैसे हैं",
    },
    "help": {
        "gif_url": "/assets/signs/help.gif",
        "description": "Place your fist (thumb up) on the open palm of your other hand, then raise both hands together upward.",
        "tips": [
            "Thumb points upward on the fist",
            "Other hand is flat, palm up",
            "Lift both hands together",
        ],
        "difficulty": "easy",
        "category": "common",
        "duration_ms": 1800,
        "hindi_name": "मदद",
    },
    "water": {
        "gif_url": "/assets/signs/water.gif",
        "description": "Make a 'W' shape with three fingers extended, tap the index finger to your chin twice.",
        "tips": [
            "Three fingers extended (index, middle, ring)",
            "Tap chin lightly twice",
            "Keep other fingers folded",
        ],
        "difficulty": "easy",
        "category": "needs",
        "duration_ms": 1500,
        "hindi_name": "पानी",
    },
    "food": {
        "gif_url": "/assets/signs/food.gif",
        "description": "Bunch your fingertips together and tap them against your mouth twice — as if putting food in your mouth.",
        "tips": [
            "All fingertips touch together",
            "Tap your lips or chin area",
            "Two clear taps",
        ],
        "difficulty": "easy",
        "category": "needs",
        "duration_ms": 1500,
        "hindi_name": "खाना",
    },
    "yes": {
        "gif_url": "/assets/signs/yes.gif",
        "description": "Make a fist and nod it up and down — like your hand is nodding 'yes'.",
        "tips": [
            "Fist shape, like holding a door handle",
            "Nod wrist up and down",
            "2-3 nods",
        ],
        "difficulty": "easy",
        "category": "responses",
        "duration_ms": 1200,
        "hindi_name": "हाँ",
    },
    "no": {
        "gif_url": "/assets/signs/no.gif",
        "description": "Extend index and middle fingers, bring them together with thumb in a snapping motion.",
        "tips": [
            "Index and middle fingers extended",
            "Snap them against thumb",
            "Quick, decisive motion",
        ],
        "difficulty": "easy",
        "category": "responses",
        "duration_ms": 1000,
        "hindi_name": "नहीं",
    },
    "good": {
        "gif_url": "/assets/signs/good.gif",
        "description": "Place flat hand on chin with fingers pointing up, then move hand outward and down landing palm-up on other hand.",
        "tips": [
            "Start at chin level",
            "Smooth outward-downward motion",
            "Land on open palm of other hand",
        ],
        "difficulty": "easy",
        "category": "descriptions",
        "duration_ms": 1800,
        "hindi_name": "अच्छा",
    },
    "bad": {
        "gif_url": "/assets/signs/bad.gif",
        "description": "Place flat hand on chin, then flip it downward with palm facing down — opposite of 'good'.",
        "tips": [
            "Start same as 'good' — hand on chin",
            "Flip hand downward sharply",
            "Palm ends facing down",
        ],
        "difficulty": "easy",
        "category": "descriptions",
        "duration_ms": 1500,
        "hindi_name": "बुरा",
    },
    "sorry": {
        "gif_url": "/assets/signs/sorry.gif",
        "description": "Make a fist and rub it in a circle over your chest — expressing regret from the heart.",
        "tips": [
            "Fist shape over chest",
            "Circular rubbing motion",
            "Show apologetic expression",
        ],
        "difficulty": "easy",
        "category": "emotions",
        "duration_ms": 2000,
        "hindi_name": "माफ़ करें",
    },
    "please": {
        "gif_url": "/assets/signs/please.gif",
        "description": "Place your flat hand on your chest and move it in a circular motion.",
        "tips": [
            "Open palm on chest",
            "Smooth circular motion",
            "Show a polite expression",
        ],
        "difficulty": "easy",
        "category": "common",
        "duration_ms": 1800,
        "hindi_name": "कृपया",
    },
    "name": {
        "gif_url": "/assets/signs/name.gif",
        "description": "Extend index and middle fingers on both hands, tap them together in an X pattern twice.",
        "tips": [
            "H-shape with both hands",
            "Tap middle finger on index finger",
            "Two taps",
        ],
        "difficulty": "medium",
        "category": "personal",
        "duration_ms": 1800,
        "hindi_name": "नाम",
    },
    "family": {
        "gif_url": "/assets/signs/family.gif",
        "description": "Start with both hands making 'F' shapes in front, then circle them around to meet in front of your body.",
        "tips": [
            "Start with F handshapes facing each other",
            "Circle outward",
            "Bring together in front",
        ],
        "difficulty": "medium",
        "category": "personal",
        "duration_ms": 2500,
        "hindi_name": "परिवार",
    },
    "friend": {
        "gif_url": "/assets/signs/friend.gif",
        "description": "Hook index fingers together, first one way then flip and hook the other way.",
        "tips": [
            "Index fingers hook like chain links",
            "First right on top, then left on top",
            "Smooth alternating motion",
        ],
        "difficulty": "medium",
        "category": "personal",
        "duration_ms": 2000,
        "hindi_name": "दोस्त",
    },
    # Alphabet Fallback Signs
    **{
        char: {
            "gif_url": f"/assets/signs/alphabet/{char}.gif",
            "description": f"Handshape for the letter '{char.upper()}' in Indian Sign Language.",
            "tips": ["Keep your hand steady", "Face your palm forward"],
            "difficulty": "easy",
            "category": "alphabet",
            "duration_ms": 800
        } for char in "abcdefghijklmnopqrstuvwxyz"
    }
}


def get_sign_demo(word: str) -> Dict:
    """Get sign demo data for a word."""
    return SIGN_DEMOS.get(word.lower(), None)


def get_all_sign_words() -> List[str]:
    """Get all words that have sign demos."""
    return list(SIGN_DEMOS.keys())
