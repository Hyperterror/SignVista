"""
SignVista Session Store

Hybrid in-memory + SQLite session management.
- In-memory: fast state for the translate / learn / game loops.
- SQLite: source of truth for XP, level, streaks, achievements, activity,
  learning precision and game history.

Sessions are keyed by the authenticated user's `user_id`, loaded from the DB
on first access, and evicted after a period of inactivity (all durable state
is already persisted, so eviction loses nothing but transient loop state).
"""

import datetime as dt
import logging
import random
import threading
import time
import uuid
from collections import deque
from typing import Any, Dict, List, Optional

from app.config import settings
from app.database import SessionLocal
from app.models import (
    ActivityLog,
    GameSessionHistory,
    LearningPrecision,
    Notification,
    User,
    UserStats,
)

logger = logging.getLogger(__name__)


# ─── Constants ───────────────────────────────────────────────────

USER_LEVEL_THRESHOLDS = [0, 100, 300, 600, 1000, 1500, 2200, 3000, 4000, 5500]

POLYGLOT_WORD_COUNT = 10

ACHIEVEMENT_DEFINITIONS = [
    {"id": "first_sign",      "name": "🌱 First Sign",      "desc": "First correct sign attempt"},
    {"id": "word_collector",  "name": "📚 Word Collector",  "desc": "Practice 5 different words"},
    {"id": "sharpshooter",    "name": "🎯 Sharpshooter",    "desc": "Reach 80% proficiency on a word (min. 5 attempts)"},
    {"id": "on_fire",         "name": "🔥 On Fire",         "desc": "3-day learning streak"},
    {"id": "rising_star",     "name": "⭐ Rising Star",     "desc": "Reach Level 3"},
    {"id": "isl_champion",    "name": "🏆 ISL Champion",    "desc": "Reach Level 7"},
    {"id": "game_on",         "name": "🎮 Game On",         "desc": "Complete your first game"},
    {"id": "perfect_game",    "name": "💯 Perfect Game",    "desc": "Sign 5+ words in a game without a single miss"},
    {"id": "polyglot",        "name": "🗣️ Polyglot",        "desc": f"Practice {POLYGLOT_WORD_COUNT} different signs"},
    {"id": "streak_master",   "name": "🔥 Streak Master",   "desc": "Get a 5+ streak in a game"},
    {"id": "diamond_hands",   "name": "💎 Diamond Hands",   "desc": "Get a 10+ streak in a game"},
    {"id": "grandmaster",     "name": "👑 Grandmaster",     "desc": "Reach Level 10"},
]
ACHIEVEMENTS_BY_ID = {a["id"]: a for a in ACHIEVEMENT_DEFINITIONS}

ACTIVITY_MEMORY_CAP = 50
MAX_GAMES_KEPT = 5


def _today() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def level_for_xp(total_xp: int) -> int:
    level = 1
    for i, threshold in enumerate(USER_LEVEL_THRESHOLDS):
        if total_xp >= threshold:
            level = i + 1
        else:
            break
    return level


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

    def record_attempt(self, target_word: str, predicted_word: Optional[str], confidence: float, user_session: "UserSession") -> Dict[str, Any]:
        """Record a learning attempt and return updated stats."""
        word_key = target_word.lower()

        with user_session.lock:
            stats = self.word_stats.setdefault(word_key, {
                "attempts": 0,
                "correct": 0,
                "proficiency": 0.0,
                "best_confidence": 0.0,
                "last_attempt_time": None,
            })
            stats["attempts"] += 1
            stats["last_attempt_time"] = time.time()

            is_correct = predicted_word is not None and predicted_word.lower() == word_key
            if is_correct:
                stats["correct"] += 1
            if confidence > stats["best_confidence"]:
                stats["best_confidence"] = confidence
            stats["proficiency"] = round((stats["correct"] / stats["attempts"]) * 100, 1)

            self._persist_learning(user_session.session_id, word_key)

            xp = 10 if is_correct else 3
            user_session.touch_streak()
            user_session.award_xp(xp, f"{'Correct sign' if is_correct else 'Practice attempt'}: {target_word}")
            user_session.add_activity("learn_attempt", {
                "word": word_key,
                "correct": is_correct,
                "proficiency": stats["proficiency"],
            }, xp_earned=xp)
            user_session.check_achievements("learn", {"word": word_key, "is_correct": is_correct})

            return {
                "correct": is_correct,
                "proficiency": stats["proficiency"],
                "attempts": stats["attempts"],
                "correct_count": stats["correct"],
                "fault": self._generate_fault(is_correct, confidence),
            }

    def _persist_learning(self, user_id: str, word_key: str):
        """Upsert the LearningPrecision row for this word."""
        stats = self.word_stats[word_key]
        db = SessionLocal()
        try:
            row = db.query(LearningPrecision).filter(
                LearningPrecision.user_id == user_id,
                LearningPrecision.word == word_key,
            ).first()
            if row is None:
                row = LearningPrecision(user_id=user_id, word=word_key)
                db.add(row)
            row.attempts = stats["attempts"]
            row.correct_count = stats["correct"]
            row.proficiency = stats["proficiency"]
            row.best_confidence = stats["best_confidence"]
            row.last_attempt_time = stats["last_attempt_time"]
            db.commit()
        except Exception:
            db.rollback()
            logger.exception(f"Failed to persist learning precision for {user_id}/{word_key}")
        finally:
            db.close()

    @staticmethod
    def _generate_fault(is_correct: bool, confidence: float) -> str:
        """Generate feedback message based on attempt result."""
        if is_correct:
            if confidence >= 0.9:
                return "Excellent form! Perfect sign! 🌟"
            if confidence >= 0.75:
                return "Good form! Keep it up! 👍"
            if confidence >= 0.6:
                return "Correct! Try to be more precise with hand positioning."
            return "Correct, but confidence is low. Practice the motion more smoothly."
        if confidence < 0.3:
            return "Sign not recognized clearly. Ensure good lighting and keep your hands in frame."
        if confidence < 0.5:
            return "Close, but not quite. Check your hand position and movement speed."
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

    NUM_CHALLENGES = 20

    def __init__(self, game_id: str, duration: int, word_pool: List[str]):
        if not word_pool:
            raise ValueError("word_pool must not be empty")
        self.game_id = game_id
        self.duration = duration
        self.start_time = time.time()
        self.score = 0
        self.streak = 0
        self.best_streak = 0
        self.words_completed = 0
        # Attempts = actual predictions made (frames with no prediction don't count)
        self.total_attempts = 0
        self.word_results: Dict[str, bool] = {}
        self.challenges: List[str] = self._generate_challenges(word_pool)
        self.current_index = 0
        self.is_active = True
        self.finished = False
        self._last_wrong_prediction: Optional[str] = None

    def _generate_challenges(self, pool: List[str]) -> List[str]:
        """Random challenge queue without immediate repeats."""
        challenges: List[str] = []
        for _ in range(self.NUM_CHALLENGES):
            options = [w for w in pool if not challenges or w != challenges[-1]] or pool
            challenges.append(random.choice(options))
        return challenges

    @property
    def current_challenge(self) -> str:
        return self.challenges[self.current_index % len(self.challenges)]

    @property
    def time_remaining(self) -> float:
        return max(0.0, self.duration - (time.time() - self.start_time))

    @property
    def is_expired(self) -> bool:
        return self.time_remaining <= 0

    @property
    def multiplier(self) -> int:
        """Streak multiplier: 1x, 2x (3+), 3x (5+), 5x (10+)."""
        if self.streak >= 10:
            return 5
        if self.streak >= 5:
            return 3
        if self.streak >= 3:
            return 2
        return 1

    @property
    def accuracy(self) -> float:
        return round((self.words_completed / max(self.total_attempts, 1)) * 100, 1)

    def record_attempt(self, predicted: Optional[str]) -> Dict[str, Any]:
        """Record a game attempt. Frames without a prediction are not attempts."""
        if self.is_expired:
            self.is_active = False
            return self._build_result(predicted, False)

        if predicted is None:
            return self._build_result(None, False)

        challenge = self.current_challenge
        is_correct = predicted.lower() == challenge.lower()

        if is_correct:
            self.total_attempts += 1
            self.streak += 1
            self.best_streak = max(self.best_streak, self.streak)
            self.score += settings.GAME_POINTS_PER_CORRECT * self.multiplier
            self.words_completed += 1
            self.word_results[challenge] = True
            self.current_index += 1
            self._last_wrong_prediction = None
        elif predicted != self._last_wrong_prediction:
            # The same wrong prediction on consecutive frames counts once
            self.total_attempts += 1
            self.word_results.setdefault(challenge, False)
            self.streak = 0
            self._last_wrong_prediction = predicted

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
            "timeRemaining": round(self.time_remaining, 1),
            "isActive": self.is_active and not self.is_expired,
        }

    def get_final_result(self) -> Dict[str, Any]:
        """Final game results with badges."""
        accuracy = self.accuracy
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
        if self.total_attempts > 0 and accuracy >= 80:
            badges.append("✅ Sharp Eye")
        if self.words_completed > 0 and not badges:
            badges.append("🌱 Getting Started")

        return {
            "gameId": self.game_id,
            "score": self.score,
            "wordsCompleted": self.words_completed,
            "totalChallenges": self.total_attempts,
            "streak_best": self.best_streak,
            "accuracy": accuracy,
            "badges": badges,
            "word_breakdown": self.word_results,
            "duration": self.duration,
        }


class UserSession:
    """Complete session state for one user."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = time.time()
        self.last_access = time.time()
        self.lock = threading.RLock()
        self.translate = TranslateSession()
        self.learn = LearnSession()
        self.games: Dict[str, GameSession] = {}
        self.games_played = 0
        self.best_game_score = 0

        # Gamification
        self.total_xp = 0
        self.level = 1
        self.current_streak = 0
        self.longest_streak = 0
        self.last_active_date: Optional[str] = None  # YYYY-MM-DD (UTC)
        self.unlocked_achievements: List[str] = []
        self.activity_history: List[Dict] = []  # newest last, capped

    # ── Loading ────────────────────────────────────────────────

    def load_from_db(self, db) -> None:
        stats_row = db.query(UserStats).filter(UserStats.user_id == self.session_id).first()
        if stats_row:
            self.total_xp = stats_row.total_xp or 0
            self.level = max(stats_row.level or 1, level_for_xp(self.total_xp))
            self.games_played = stats_row.games_played or 0
            self.best_game_score = max(stats_row.best_score or 0, stats_row.best_game_score or 0)
            self.unlocked_achievements = list(stats_row.unlocked_achievements or [])
            self.current_streak = stats_row.current_streak or 0
            self.longest_streak = stats_row.longest_streak or 0
            self.last_active_date = stats_row.last_active_date
            # A streak is broken if the last activity was before yesterday
            if self.last_active_date:
                last = dt.date.fromisoformat(self.last_active_date)
                if (dt.date.fromisoformat(_today()) - last).days > 1:
                    self.current_streak = 0

        for row in db.query(LearningPrecision).filter(LearningPrecision.user_id == self.session_id).all():
            self.learn.word_stats[row.word] = {
                "attempts": row.attempts or 0,
                "correct": row.correct_count or 0,
                "proficiency": row.proficiency or 0.0,
                "best_confidence": row.best_confidence or 0.0,
                "last_attempt_time": row.last_attempt_time,
            }

        recent = (
            db.query(ActivityLog)
            .filter(ActivityLog.user_id == self.session_id)
            .order_by(ActivityLog.timestamp.desc())
            .limit(ACTIVITY_MEMORY_CAP)
            .all()
        )
        self.activity_history = [
            {"type": r.type, "data": r.data or {}, "timestamp": r.timestamp, "xp_earned": r.xp_earned or 0}
            for r in reversed(recent)
        ]

    # ── Games ──────────────────────────────────────────────────

    def start_game(self, duration: int, word_pool: List[str]) -> GameSession:
        with self.lock:
            self._prune_games()
            game = GameSession(uuid.uuid4().hex[:12], duration, word_pool)
            self.games[game.game_id] = game
            self.add_activity("game_started", {"gameId": game.game_id})
            return game

    def get_game(self, game_id: str) -> Optional[GameSession]:
        return self.games.get(game_id)

    def _prune_games(self) -> None:
        finished = [gid for gid, g in self.games.items() if g.finished]
        for gid in finished[:-MAX_GAMES_KEPT] if len(finished) > MAX_GAMES_KEPT else []:
            self.games.pop(gid, None)

    def finish_game(self, game_id: str) -> Optional[GameSession]:
        """Finalize a game exactly once: award XP, persist history, check achievements."""
        with self.lock:
            game = self.games.get(game_id)
            if game is None or game.finished:
                return game
            game.finished = True
            game.is_active = False

            self.games_played += 1
            self.best_game_score = max(self.best_game_score, game.score)

            game_xp = int(game.score / 10) + 50 if game.total_attempts > 0 else 10
            self.touch_streak()
            self.award_xp(game_xp, f"Completed game {game_id}")
            self.add_activity("game_completed", {
                "gameId": game_id,
                "score": game.score,
                "accuracy": game.accuracy,
            }, xp_earned=game_xp)
            self.check_achievements("game", {"game": game})

            db = SessionLocal()
            try:
                db.add(GameSessionHistory(
                    user_id=self.session_id,
                    game_id=game_id,
                    score=game.score,
                    words_completed=game.words_completed,
                    total_attempts=game.total_attempts,
                    accuracy=game.accuracy,
                    best_streak=game.best_streak,
                    duration=game.duration,
                    played_at=game.start_time,
                ))
                db.commit()
            except Exception:
                db.rollback()
                logger.exception(f"Failed to persist game {game_id} for {self.session_id}")
            finally:
                db.close()
            self._persist_stats()
            return game

    # ── XP / levels / streaks ──────────────────────────────────

    def award_xp(self, amount: int, reason: str):
        with self.lock:
            self.total_xp += amount
            self._check_level_up()
            self._persist_stats()

    def _check_level_up(self):
        new_level = level_for_xp(self.total_xp)
        if new_level > self.level:
            old_level = self.level
            self.level = new_level
            self.add_activity("level_up", {"old": old_level, "new": new_level})
            self.notify("Level up! 🎉", f"You reached Level {new_level}.", "success", "/dashboard")
            self.check_achievements("level", {"level": new_level})

    def touch_streak(self) -> None:
        """Update the daily learning streak (call on any learning/game activity)."""
        with self.lock:
            today = _today()
            if self.last_active_date == today:
                return
            if self.last_active_date and (
                dt.date.fromisoformat(today) - dt.date.fromisoformat(self.last_active_date)
            ).days == 1:
                self.current_streak += 1
            else:
                self.current_streak = 1
            self.longest_streak = max(self.longest_streak, self.current_streak)
            self.last_active_date = today
            self._persist_stats()
            self.check_achievements("streak", {})

    def _persist_stats(self):
        """Write XP, level, streak and achievements to the UserStats row."""
        db = SessionLocal()
        try:
            row = db.query(UserStats).filter(UserStats.user_id == self.session_id).first()
            if row is None:
                if db.query(User.id).filter(User.user_id == self.session_id).first() is None:
                    return  # Not a registered user (e.g. tests); nothing to persist
                row = UserStats(user_id=self.session_id)
                db.add(row)
            row.total_xp = self.total_xp
            row.level = self.level
            row.games_played = self.games_played
            row.best_score = self.best_game_score
            row.best_game_score = self.best_game_score
            row.unlocked_achievements = list(self.unlocked_achievements)
            row.current_streak = self.current_streak
            row.longest_streak = self.longest_streak
            row.last_active_date = self.last_active_date
            db.commit()
        except Exception:
            db.rollback()
            logger.exception(f"Failed to persist stats for {self.session_id}")
        finally:
            db.close()

    # ── Activity / notifications ───────────────────────────────

    def add_activity(self, type: str, data: Dict, xp_earned: int = 0):
        entry = {"type": type, "data": data, "timestamp": time.time(), "xp_earned": xp_earned}
        with self.lock:
            self.activity_history.append(entry)
            if len(self.activity_history) > ACTIVITY_MEMORY_CAP:
                del self.activity_history[: len(self.activity_history) - ACTIVITY_MEMORY_CAP]

        db = SessionLocal()
        try:
            if db.query(User.id).filter(User.user_id == self.session_id).first() is not None:
                db.add(ActivityLog(user_id=self.session_id, type=type, data=data,
                                   xp_earned=xp_earned, timestamp=entry["timestamp"]))
                db.commit()
        except Exception:
            db.rollback()
            logger.exception(f"Failed to persist activity for {self.session_id}")
        finally:
            db.close()

    def notify(self, title: str, message: str, type: str = "info", action_url: Optional[str] = None) -> None:
        db = SessionLocal()
        try:
            if db.query(User.id).filter(User.user_id == self.session_id).first() is not None:
                db.add(Notification(user_id=self.session_id, title=title, message=message,
                                    type=type, action_url=action_url))
                db.commit()
        except Exception:
            db.rollback()
            logger.exception(f"Failed to create notification for {self.session_id}")
        finally:
            db.close()

    # ── Achievements ───────────────────────────────────────────

    def check_achievements(self, trigger_type: str, context: Dict):
        with self.lock:
            unlocked = set(self.unlocked_achievements)
            candidates: List[str] = []

            words_practiced = self.learn.get_words_practiced()
            if words_practiced >= 5:
                candidates.append("word_collector")
            if words_practiced >= POLYGLOT_WORD_COUNT:
                candidates.append("polyglot")
            if any(s["attempts"] >= 5 and s["proficiency"] >= 80 for s in self.learn.word_stats.values()):
                candidates.append("sharpshooter")
            if sum(s["correct"] for s in self.learn.word_stats.values()) >= 1:
                candidates.append("first_sign")
            if self.games_played >= 1:
                candidates.append("game_on")
            if self.current_streak >= 3:
                candidates.append("on_fire")
            if self.level >= 3:
                candidates.append("rising_star")
            if self.level >= 7:
                candidates.append("isl_champion")
            if self.level >= 10:
                candidates.append("grandmaster")

            game = context.get("game") if trigger_type == "game" else None
            if game is not None:
                if game.words_completed >= 5 and game.words_completed == game.total_attempts:
                    candidates.append("perfect_game")
                if game.best_streak >= 5:
                    candidates.append("streak_master")
                if game.best_streak >= 10:
                    candidates.append("diamond_hands")

            newly = [aid for aid in dict.fromkeys(candidates) if aid not in unlocked]
            if not newly:
                return
            for aid in newly:
                self.unlocked_achievements.append(aid)
                self.add_activity("achievement_unlocked", {"id": aid})
                defn = ACHIEVEMENTS_BY_ID[aid]
                self.notify("Achievement unlocked!", f"{defn['name']} — {defn['desc']}", "achievement", "/profile")
            self._persist_stats()


# ─── Global Session Store ─────────────────────────────────────────

_sessions: Dict[str, UserSession] = {}
_sessions_lock = threading.Lock()
_last_eviction = 0.0


def _evict_idle_sessions(now: float) -> None:
    global _last_eviction
    if now - _last_eviction < 60:
        return
    _last_eviction = now
    ttl = settings.SESSION_IDLE_TTL_SECONDS
    for sid in [sid for sid, s in _sessions.items() if now - s.last_access > ttl]:
        _sessions.pop(sid, None)
        logger.debug(f"Evicted idle session {sid}")


def get_session(session_id: str) -> UserSession:
    """Get or create a session, pre-loading persistent state from the DB."""
    now = time.time()
    with _sessions_lock:
        _evict_idle_sessions(now)
        session = _sessions.get(session_id)
        if session is None:
            session = UserSession(session_id)
            db = SessionLocal()
            try:
                session.load_from_db(db)
            except Exception:
                logger.exception(f"Failed to load session state for {session_id}; starting fresh")
            finally:
                db.close()
            _sessions[session_id] = session
        session.last_access = now
        return session


def session_exists(session_id: str) -> bool:
    return session_id in _sessions


def get_active_session_count() -> int:
    return len(_sessions)


def clear_session(session_id: str):
    with _sessions_lock:
        _sessions.pop(session_id, None)


def clear_all_sessions():
    """Clear all sessions (for testing)."""
    with _sessions_lock:
        _sessions.clear()


def get_active_users(exclude_user_id: Optional[str] = None) -> List[Dict]:
    """Users with an in-memory session active in the last 15 minutes."""
    cutoff = time.time() - 15 * 60
    active_ids = [sid for sid, s in list(_sessions.items()) if s.last_access >= cutoff and sid != exclude_user_id]
    if not active_ids:
        return []
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.user_id.in_(active_ids)).all()
        return [
            {"user_id": u.user_id, "name": u.name, "initials": u.name[:2].upper(), "is_online": True}
            for u in users
        ]
    finally:
        db.close()
