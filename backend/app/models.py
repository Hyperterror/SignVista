import time
from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from .database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    preferred_language = Column(String(10), default="en")
    created_at = Column(Float, default=time.time)

    stats = relationship("UserStats", back_populates="user", uselist=False, cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    learning_precision = relationship("LearningPrecision", back_populates="user", cascade="all, delete-orphan")
    game_history = relationship("GameSessionHistory", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class UserStats(Base):
    """Overall lifetime progression and cumulative statistics."""
    __tablename__ = "user_stats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), unique=True)
    total_xp = Column(Integer, default=0)
    level = Column(Integer, default=1)
    games_played = Column(Integer, default=0)
    best_game_score = Column(Integer, default=0)
    unlocked_achievements = Column(JSON, default=list)  # List of string IDs
    
    user = relationship("User", back_populates="stats")


class LearningPrecision(Base):
    """Tracks how well the user does on specific words in the learning module."""
    __tablename__ = "learning_precision"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id"))
    word = Column(String(50), nullable=False, index=True)
    attempts = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    best_confidence = Column(Float, default=0.0)
    proficiency = Column(Float, default=0.0)  # Calculated percentage
    last_practiced = Column(Float, default=time.time)

    user = relationship("User", back_populates="learning_precision")


class GameSessionHistory(Base):
    """Historical record of all games played."""
    __tablename__ = "game_session_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id"))
    score = Column(Integer, default=0)
    words_completed = Column(Integer, default=0)
    total_attempts = Column(Integer, default=0)
    best_streak = Column(Integer, default=0)
    accuracy = Column(Float, default=0.0)
    timestamp = Column(Float, default=time.time)

    user = relationship("User", back_populates="game_history")


class ChatAnalytics(Base):
    """Logs when users interact with community or AI chats, for broad analytics."""
    __tablename__ = "chat_analytics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=True, index=True)  # Nullable if anonymous allowed
    message_count = Column(Integer, default=1)
    topic = Column(String(100), nullable=True) # E.g., "grammar_help", "definition"
    timestamp = Column(Float, default=time.time)


class UserSettings(Base):
    """User preferences and settings."""
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), unique=True, index=True)
    theme = Column(String(20), default="system")  # "light", "dark", "system"
    notifications_enabled = Column(Boolean, default=True)
    sound_enabled = Column(Boolean, default=True)
    daily_goal_minutes = Column(Integer, default=15)
    updated_at = Column(Float, default=time.time)

    user = relationship("User", back_populates="settings")


class Notification(Base):
    """System and community notifications for the user."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), default="info")  # e.g., "info", "success", "warning", "achievement"
    is_read = Column(Boolean, default=False)
    timestamp = Column(Float, default=time.time)
    action_url = Column(String(200), nullable=True) # Optional link to click

    user = relationship("User", back_populates="notifications")


class CommunityPostBase(Base):
    """Global community feed posts."""
    __tablename__ = "community_posts"

    id = Column(String(50), primary_key=True, index=True)
    user_name = Column(String(100), nullable=False)
    avatar_initials = Column(String(10), nullable=False)
    content = Column(Text, nullable=False)
    likes = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    timestamp = Column(Float, default=time.time)
    is_official = Column(Boolean, default=False)
    achievement_text = Column(String(200), nullable=True)
    tags = Column(JSON, default=list)

class CommunityCommentBase(Base):
    """Replies to community posts."""
    __tablename__ = "community_comments"

    id = Column(String(50), primary_key=True, index=True)
    post_id = Column(String(50), ForeignKey("community_posts.id", ondelete="CASCADE"), index=True)
    user_name = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(Float, default=time.time)
