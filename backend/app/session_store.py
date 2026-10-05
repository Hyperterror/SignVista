"""
SignVista Session Store

Hybrid in-memory + SQLite session management.
- In-memory: Fast lookup for translate / learn / game loop state.
- SQLite: Persistent storage for XP, level, game history, and learning precision.

On first access, user sessions are pre-loaded from the DB so state
survives server restarts.
"""

import time
import uuid
import random
import json
import os
from collections import deque
from typing import Any, Dict, List, Optional, Tuple

from ml.vocabulary import WORD_LIST, WORD_DISPLAY, is_valid_word
from app.config import settings
import bcrypt
from app.database import SessionLocal
from app.models import User, UserStats, UserSettings, LearningPrecision, GameSessionHistory

# ─── Auth Setup ──────────────────────────────────────────────────

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

# ─── Auth Setup Removed In-Memory Dict ───────────────────────────
# Legacy USERS mock DB and json caching removed in favor of SQLite.


# ─── Constants ───────────────────────────────────────────────────

USER_LEVEL_THRESHOLDS = [0, 100, 300, 600, 1000, 1500, 2200, 3000, 4000, 5500]

ACHIEVEMENT_DEFINITIONS = [
    {"id": "first_sign",      "name": "🌱 First Sign",      "desc": "First correct sign attempt"},
    {"id": "word_collector", "name": "📚 Word Collector", "desc": "Practice 5 different words"},
    {"id": "sharpshooter",    "name": "🎯 Sharpshooter",    "desc": "Reach 80% proficiency on a word"},
    {"id": "on_fire",         "name": "🔥 On Fire",         "desc": "3-day learning streak"},
    {"id": "rising_star",    "name": "⭐ Rising Star",    "desc": "Reach Level 3"},
    {"id": "isl_champion",    "name": "🏆 ISL Champion",    "desc": "Reach Level 7"},
    {"id": "game_on",         "name": "🎮 Game On",         "desc": "Complete your first game"},
    {"id": "perfect_game",    "name": "💯 Perfect Game",    "desc": "100% accuracy in a game"},
    {"id": "polyglot",        "name": "🗣️ Polyglot",        "desc": "Practice all 15 vocabulary words"},
    {"id": "streak_master",   "name": "🔥 Streak Master",   "desc": "Get a 5+ streak in a game"},
    {"id": "diamond_hands",   "name": "💎 Diamond Hands",   "desc": "Get a 10+ streak in a game"},
    {"id": "grandmaster",     "name": "👑 Grandmaster",     "desc": "Reach Level 10"},
]


# ─── Session Data Structures ─────────────────────────────────────

class TranslateSession:
    """State for translate mode."""

    def __init__(self):
        self.history: deque = deque(maxlen=5)  # Last 5 predicted words
        self.last_prediction: Optional[str] = None
        self.last_confidence: float = 0.0
        self.total_predictions: int = 0

    def add_prediction(self, word: str, confidence: float):
        self.history.append(word)
        self.last_prediction = word
        self.last_confidence = confidence
        self.total_predictions += 1

    def get_history(self) -> List[str]:
        return list(self.history)


class LearnSession:
    """State for learn mode — tracks per-word proficiency."""

    def __init__(self):
        self.word_stats: Dict[str, Dict[str, Any]] = {}

    def record_attempt(self, target_word: str, predicted_word: Optional[str], confidence: float, user_session: Any) -> Dict[str, Any]:
        """Record a learning attempt and return updated stats."""
        word_key = target_word.lower()

        if word_key not in self.word_stats:
            self.word_stats[word_key] = {
                "attempts": 0,
                "correct": 0,
                "proficiency": 0.0,
                "best_confidence": 0.0,
                "last_attempt_time": None,
            }

        stats = self.word_stats[word_key]
        stats["attempts"] += 1
        stats["last_attempt_time"] = time.time()

        is_correct = predicted_word is not None and predicted_word.lower() == word_key
        if is_correct:
            stats["correct"] += 1
            # Award XP for correct sign
            user_session.award_xp(10, f"Correct sign: {target_word}")
        else:
            # Small XP for effort
            user_session.award_xp(3, f"Practice attempt: {target_word}")

        if confidence > stats["best_confidence"]:
            stats["best_confidence"] = confidence

        # Calculate proficiency as percentage
        stats["proficiency"] = round((stats["correct"] / stats["attempts"]) * 100, 1)

        # Generate fault feedback
        fault = self._generate_fault(is_correct, confidence, stats)
        
        # Check for achievements
        user_session.check_achievements("learn", {"word": word_key, "is_correct": is_correct})

        # Add activity
        user_session.add_activity("learn_attempt", {
            "word": word_key,
            "correct": is_correct,
            "proficiency": stats["proficiency"]
        })

        # Persist learning precision to SQLite
        self._persist_learning(user_session.session_id, word_key)

        return {
            "correct": is_correct,
            "proficiency": stats["proficiency"],
            "attempts": stats["attempts"],
            "correct_count": stats["correct"],
            "fault": fault,
        }

    def _persist_learning(self, user_session_id: str, word_key: str):
        """Upsert LearningPrecision row for this word in SQLite."""
        stats = self.word_stats[word_key]
        db = SessionLocal()
        try:
            row = db.query(LearningPrecision).filter(
                LearningPrecision.user_id == user_session_id,
                LearningPrecision.word == word_key,
            ).first()
            if row:
                row.attempts = stats["attempts"]
                row.correct_count = stats["correct"]
                row.proficiency = stats["proficiency"]
                row.best_confidence = stats["best_confidence"]
                row.last_attempt_time = stats["last_attempt_time"]
            else:
                row = LearningPrecision(
                    user_id=user_session_id,
                    word=word_key,
                    attempts=stats["attempts"],
                    correct_count=stats["correct"],
                    proficiency=stats["proficiency"],
                    best_confidence=stats["best_confidence"],
                    last_attempt_time=stats["last_attempt_time"],
                )
                db.add(row)
            db.commit()
        except Exception:
            pass  # Never crash a learn attempt over a DB write
        finally:
            db.close()


    def _generate_fault(self, is_correct: bool, confidence: float, stats: Dict) -> str:
        """Generate feedback message based on attempt result."""
        if is_correct:
            if confidence >= 0.9:
                return "Excellent form! Perfect sign! 🌟"
            elif confidence >= 0.75:
                return "Good form! Keep it up! 👍"
            elif confidence >= 0.6:
                return "Correct! Try to be more precise with hand positioning."
            else:
                return "Correct, but confidence is low. Practice the motion more smoothly."
        else:
            if confidence < 0.3:
                return "Sign not recognized clearly. Ensure good lighting and face visibility."
            elif confidence < 0.5:
                return "Close, but not quite. Check your hand position and movement speed."
            else:
                return "Incorrect sign detected. Watch the demo again and focus on the hand shape."

    def get_stats(self) -> Dict[str, Dict]:
        return self.word_stats

    def get_words_practiced(self) -> int:
        return len(self.word_stats)

    def get_overall_proficiency(self) -> float:
        if not self.word_stats:
            return 0.0
        total_prof = sum(s["proficiency"] for s in self.word_stats.values())
        return round(total_prof / len(self.word_stats), 1)


class GameSession:
    """State for a single game round."""

    def __init__(self, game_id: str, duration: int = 30):
        self.game_id = game_id
        self.duration = duration
        self.start_time = time.time()
        self.score = 0
        self.streak = 0
        self.best_streak = 0
        self.words_completed = 0
        self.total_attempts = 0
        self.word_results: Dict[str, bool] = {}

        # Generate random challenge queue
        self.challenges: List[str] = self._generate_challenges()
        self.current_index = 0
        self.is_active = True

    def _generate_challenges(self) -> List[str]:
        """Create a shuffled list of challenge words."""
        # Use core words (priority 1) with some repeats
        challenges = WORD_LIST[:10] * 2  # 20 challenges from core words
        random.shuffle(challenges)
        return challenges

    @property
    def current_challenge(self) -> str:
        """Get the current challenge word."""
        if self.current_index >= len(self.challenges):
            # Wrap around if needed
            self.current_index = 0
        return self.challenges[self.current_index]

    @property
    def time_remaining(self) -> float:
        elapsed = time.time() - self.start_time
        return max(0, self.duration - elapsed)

    @property
    def is_expired(self) -> bool:
        return self.time_remaining <= 0

    @property
    def multiplier(self) -> int:
        """Streak multiplier: 1x, 2x (3+), 3x (5+), 5x (10+)."""
        if self.streak >= 10:
            return 5
        elif self.streak >= 5:
            return 3
        elif self.streak >= 3:
            return 2
        return 1

    def record_attempt(self, predicted: Optional[str], confidence: float) -> Dict[str, Any]:
        """Record a game attempt and return result."""
        self.total_attempts += 1

        if self.is_expired:
            self.is_active = False
            return self._build_result(predicted, False)

        is_correct = (
            predicted is not None
            and predicted.lower() == self.current_challenge.lower()
        )

        if is_correct:
            self.streak += 1
            if self.streak > self.best_streak:
                self.best_streak = self.streak
            points = settings.GAME_POINTS_PER_CORRECT * self.multiplier
            self.score += points
            self.words_completed += 1
            self.word_results[self.current_challenge] = True
            self.current_index += 1  # Move to next challenge
        else:
            self.word_results.setdefault(self.current_challenge, False)
            self.streak = 0

        return self._build_result(predicted, is_correct)

    def _build_result(self, predicted: Optional[str], is_correct: bool) -> Dict[str, Any]:
        return {
            "predicted": predicted,
            "correct": is_correct,
            "currentChallenge": self.current_challenge,
            "score": self.score,
            "streak": self.streak,
            "multiplier": self.multiplier,
            "wordsCompleted": self.words_completed,
        }

    def get_final_result(self) -> Dict[str, Any]:
        """Get final game results with badges."""
        accuracy = (self.words_completed / max(self.total_attempts, 1)) * 100

        badges = []
        if self.score >= 1000:
            badges.append("🏆 ISL Champion")
        if self.score >= 500:
            badges.append("⭐ Star Signer")
        if self.best_streak >= 5:
            badges.append("🔥 Streak Master")
        if self.best_streak >= 10:
            badges.append("💎 Unstoppable")
        if self.words_completed >= 10:
            badges.append("🎯 Speed Demon")
        if accuracy >= 80:
            badges.append("✅ Sharp Eye")
        if self.words_completed > 0 and not badges:
            badges.append("🌱 Getting Started")

        return {
            "gameId": self.game_id,
            "score": self.score,
            "wordsCompleted": self.words_completed,
            "totalChallenges": self.total_attempts,
            "streak_best": self.best_streak,
            "accuracy": round(accuracy, 1),
            "badges": badges,
            "word_breakdown": self.word_results,
            "duration": self.duration,
        }


class UserSession:
    """Complete session state for one user."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = time.time()
        self.translate = TranslateSession()
        self.learn = LearnSession()
        self.games: Dict[str, GameSession] = {}
        self.games_played = 0
        self.best_game_score = 0
        
        # Gamification
        self.total_xp = 0
        self.level = 1
        self.current_streak = 0
        self.last_active_date = ""  # YYYY-MM-DD
        self.unlocked_achievements: List[str] = []
        self.activity_history: List[Dict] = []  # capped activity log

    def start_game(self, duration: int = 30) -> GameSession:
        game_id = str(uuid.uuid4())[:8]
        game = GameSession(game_id, duration)
        self.games[game_id] = game
        self.games_played += 1
        
        self.add_activity("game_started", {"gameId": game_id})
        return game

    def get_game(self, game_id: str) -> Optional[GameSession]:
        return self.games.get(game_id)

    def finish_game(self, game_id: str):
        game = self.games.get(game_id)
        if not game:
            return

        if game.score > self.best_game_score:
            self.best_game_score = game.score

        # Award Game XP
        game_xp = int(game.score / 10) + 50  # Base 50 + 10% of score
        self.award_xp(game_xp, f"Completed game {game_id}")

        # Check game achievements
        self.check_achievements("game", {"game": game})

        accuracy = round((game.words_completed / max(game.total_attempts, 1)) * 100, 1)
        self.add_activity("game_completed", {
            "gameId": game_id,
            "score": game.score,
            "accuracy": accuracy,
        })

        # Persist game result to SQLite
        db = SessionLocal()
        try:
            history_row = GameSessionHistory(
                user_id=self.session_id,
                game_id=game_id,
                score=game.score,
                words_completed=game.words_completed,
                total_attempts=game.total_attempts,
                accuracy=accuracy,
                best_streak=game.best_streak,
                duration=game.duration,
                played_at=game.start_time,
            )
            db.add(history_row)
            db.commit()
        except Exception:
            pass  # Never crash the game flow over a DB write
        finally:
            db.close()

    def award_xp(self, amount: int, reason: str):
        self.total_xp += amount
        self._check_level_up()
        # Persist XP and level to SQLite in the background
        self._persist_xp()

    def _check_level_up(self):
        new_level = 1
        for i, threshold in enumerate(USER_LEVEL_THRESHOLDS):
            if self.total_xp >= threshold:
                new_level = i + 1
            else:
                break

        if new_level > self.level:
            old_level = self.level
            self.level = new_level
            self.add_activity("level_up", {"old": old_level, "new": new_level})
            self.check_achievements("level", {"level": new_level})

    def _persist_xp(self):
        """Write current XP and level to the UserStats table."""
        db = SessionLocal()
        try:
            stats_row = db.query(UserStats).filter(UserStats.user_id == self.session_id).first()
            if stats_row:
                stats_row.total_xp = self.total_xp
                stats_row.level = self.level
                stats_row.games_played = self.games_played
                stats_row.best_score = self.best_game_score
                db.commit()
        except Exception:
            pass  # Never crash the game loop over a DB write
        finally:
            db.close()

    def add_activity(self, type: str, data: Dict):
        self.activity_history.append({
            "type": type,
            "data": data,
            "timestamp": time.time()
        })
        # Cap at 50 entries
        if len(self.activity_history) > 50:
            self.activity_history.pop(0)

    def check_achievements(self, trigger_type: str, context: Dict):
        unlocked_now = []
        
        # 📚 Word Collector: Practice 5 different words
        if "word_collector" not in self.unlocked_achievements:
            if self.learn.get_words_practiced() >= 5:
                unlocked_now.append("word_collector")

        # 🎯 Sharpshooter: 80% proficiency on any word
        if "sharpshooter" not in self.unlocked_achievements:
            for stats in self.learn.word_stats.values():
                if stats["attempts"] >= 5 and stats["proficiency"] >= 80:
                    unlocked_now.append("sharpshooter")
                    break

        # 🌱 First Sign
        if "first_sign" not in self.unlocked_achievements:
            total_correct = sum(s["correct"] for s in self.learn.word_stats.values())
            if total_correct >= 1:
                unlocked_now.append("first_sign")

        # 🎮 Game On
        if "game_on" not in self.unlocked_achievements and self.games_played >= 1:
            unlocked_now.append("game_on")

        # 🗣️ Polyglot: All 15 words
        if "polyglot" not in self.unlocked_achievements:
            if self.learn.get_words_practiced() >= 15:
                unlocked_now.append("polyglot")

        # Game specific
        if trigger_type == "game":
            game = context.get("game")
            if game:
                if "perfect_game" not in self.unlocked_achievements:
                    if game.words_completed >= 5 and game.words_completed == game.total_attempts:
                        unlocked_now.append("perfect_game")
                
                if "streak_master" not in self.unlocked_achievements and game.best_streak >= 5:
                    unlocked_now.append("streak_master")
                
                if "diamond_hands" not in self.unlocked_achievements and game.best_streak >= 10:
                    unlocked_now.append("diamond_hands")

        # Level specific
        if trigger_type == "level":
            lvl = context.get("level", self.level)
            if "rising_star" not in self.unlocked_achievements and lvl >= 3:
                unlocked_now.append("rising_star")
            if "isl_champion" not in self.unlocked_achievements and lvl >= 7:
                unlocked_now.append("isl_champion")
            if "grandmaster" not in self.unlocked_achievements and lvl >= 10:
                unlocked_now.append("grandmaster")

        for aid in unlocked_now:
            if aid not in self.unlocked_achievements:
                self.unlocked_achievements.append(aid)
                self.add_activity("achievement_unlocked", {"id": aid})


# ─── Global Session Store ─────────────────────────────────────────

_sessions: Dict[str, UserSession] = {}


def get_session(session_id: str) -> UserSession:
    """Get or create a session. Pre-loads persistent state from DB on first access."""
    if session_id not in _sessions:
        session = UserSession(session_id)
        # Pre-load XP, level, and game stats from SQLite so they survive restarts
        db = SessionLocal()
        try:
            stats_row = db.query(UserStats).filter(UserStats.user_id == session_id).first()
            if stats_row:
                session.total_xp = stats_row.total_xp or 0
                session.level = stats_row.level or 1
                session.games_played = stats_row.games_played or 0
                session.best_game_score = stats_row.best_score or 0
            # Pre-load per-word learning precision from SQLite
            precision_rows = db.query(LearningPrecision).filter(
                LearningPrecision.user_id == session_id
            ).all()
            for row in precision_rows:
                session.learn.word_stats[row.word] = {
                    "attempts": row.attempts or 0,
                    "correct": row.correct_count or 0,
                    "proficiency": row.proficiency or 0.0,
                    "best_confidence": row.best_confidence or 0.0,
                    "last_attempt_time": row.last_attempt_time,
                }
        except Exception:
            pass  # Warm cache failure is non-fatal; session starts fresh
        finally:
            db.close()
        _sessions[session_id] = session
    return _sessions[session_id]


def session_exists(session_id: str) -> bool:
    """Check if a session exists."""
    return session_id in _sessions


def get_active_session_count() -> int:
    """Get total number of active sessions."""
    return len(_sessions)


def clear_session(session_id: str):
    """Remove a session."""
    _sessions.pop(session_id, None)


def clear_all_sessions():
    """Clear all sessions (for testing)."""
    _sessions.clear()


# ─── Community Data (Global) ──────────────────────────────────────

# In a real app, this would be a database. 
# For the hackathon, we use global lists.
def get_active_users() -> List[Dict]:
    """Get the list of currently active users natively from SQLite."""
    active = []
    if not _sessions:
        return active
        
    db = SessionLocal()
    try:
        active_ids = list(_sessions.keys())
        users = db.query(User).filter(User.user_id.in_(active_ids)).all()
        for u in users:
            active.append({
                "name": u.name,
                "initials": u.name[:2].upper(),
                "is_online": True
            })
    except Exception:
        pass
    finally:
        db.close()
        
    return active

def register_user(data: Dict[str, Any]) -> Tuple[bool, str, Optional[UserSession]]:
    """Register a new user and create a session."""
    db = SessionLocal()
    try:
        phone = data["phone"]
        existing_user = db.query(User).filter(User.phone == phone).first()
        if existing_user:
            return False, "Phone number already registered", None
            
        hashed_pwd = hash_password(data["password"])
        user_id = str(uuid.uuid4())[:8]
        
        new_user = User(
            user_id=user_id,
            name=data["name"],
            email=data["email"],
            phone=phone,
            password_hash=hashed_pwd,
            preferred_language=data.get("preferred_language", "en"),
            created_at=time.time()
        )
        db.add(new_user)
        
        # Initialize relational records automatically
        stats = UserStats(user_id=user_id)
        settings = UserSettings(user_id=user_id)
        db.add(stats)
        db.add(settings)
        
        db.commit()
        
        session = get_session(user_id)
        return True, "Success", session
    except Exception as e:
        db.rollback()
        return False, f"Server Error: {str(e)}", None
    finally:
        db.close()

def login_user(phone: str, password: str) -> Tuple[bool, str, Optional[UserSession]]:
    """Authenticate user and return session."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.phone == phone).first()
        if not user:
            return False, "User not found", None
            
        if not verify_password(password, user.password_hash):
            return False, "Invalid password", None
            
        session = get_session(user.user_id)
        return True, "Login successful", session
    finally:
        db.close()
