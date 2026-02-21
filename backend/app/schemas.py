"""
SignVista API Schemas (Pydantic Models)

These define the exact JSON contracts between Ayush's frontend and our backend.
Ayush: Use these as your TypeScript interface reference.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ─── Translate Mode ───────────────────────────────────────────────

class RecognizeFrameRequest(BaseModel):
    """POST /api/recognize-frame — sent every 200ms from frontend camera."""
    sessionId: str = Field(..., description="Unique session identifier")
    frame: str = Field(..., description="Base64-encoded JPEG frame (with or without data URI prefix)")


class RecognizeFrameResponse(BaseModel):
    """Response from translation inference."""
    word: Optional[str] = Field(None, description="Predicted ISL word (null if no confident prediction)")
    confidence: float = Field(0.0, description="Prediction confidence 0.0-1.0")
    buffer_status: str = Field("collecting", description="'collecting' while building 45-frame buffer, 'ready' when predicting")
    history: List[str] = Field(default_factory=list, description="Last 5 predicted words for context")


# ─── Learn Mode ───────────────────────────────────────────────────

class LearnAttemptRequest(BaseModel):
    """POST /api/learn/attempt — practice a specific word."""
    sessionId: str = Field(..., description="Unique session identifier")
    targetWord: str = Field(..., description="The word the user is trying to sign")
    frame: str = Field(..., description="Base64-encoded JPEG frame")


class LearnAttemptResponse(BaseModel):
    """Response with proficiency feedback."""
    predicted: Optional[str] = Field(None, description="What the model predicted")
    correct: bool = Field(False, description="Whether predicted matches targetWord")
    proficiency: float = Field(0.0, description="Proficiency percentage for this word (0-100)")
    attempts: int = Field(0, description="Total attempts for this word")
    correct_count: int = Field(0, description="Total correct attempts for this word")
    fault: str = Field("", description="Feedback message — 'Good form!' or specific fault")
    confidence: float = Field(0.0, description="Raw model confidence")


# ─── Game Mode ────────────────────────────────────────────────────

class GameStartRequest(BaseModel):
    """POST /api/game/start — initialize a new game round."""
    sessionId: str = Field(..., description="Unique session identifier")
    duration: int = Field(30, description="Game duration in seconds (default 30)")


class GameStartResponse(BaseModel):
    """Returns the first challenge word and game metadata."""
    gameId: str = Field(..., description="Unique game session ID")
    currentChallenge: str = Field(..., description="First word to sign")
    duration: int = Field(30, description="Game duration in seconds")
    totalChallenges: int = Field(0, description="Total challenges queued")


class GameAttemptRequest(BaseModel):
    """POST /api/game/attempt — submit a sign during game."""
    sessionId: str = Field(..., description="Unique session identifier")
    gameId: str = Field(..., description="Game session ID from /game/start")
    frame: str = Field(..., description="Base64-encoded JPEG frame")


class GameAttemptResponse(BaseModel):
    """Response after each game attempt."""
    predicted: Optional[str] = Field(None, description="What the model predicted")
    correct: bool = Field(False, description="Whether it matched the challenge")
    currentChallenge: str = Field(..., description="Current word to sign (same if wrong, next if correct)")
    score: int = Field(0, description="Current total score")
    streak: int = Field(0, description="Current consecutive correct streak")
    multiplier: int = Field(1, description="Current streak multiplier")
    wordsCompleted: int = Field(0, description="Total words signed correctly this game")
    confidence: float = Field(0.0, description="Model confidence")


class GameResultResponse(BaseModel):
    """GET /api/game/result/{sessionId}/{gameId} — final game results."""
    gameId: str
    score: int = Field(0)
    wordsCompleted: int = Field(0)
    totalChallenges: int = Field(0)
    streak_best: int = Field(0, description="Best streak achieved")
    accuracy: float = Field(0.0, description="Accuracy percentage")
    badges: List[str] = Field(default_factory=list, description="Badges earned this game")
    word_breakdown: Dict[str, bool] = Field(default_factory=dict, description="Per-word correct/incorrect")
    duration: int = Field(30)


# ─── Stats ────────────────────────────────────────────────────────

class WordStats(BaseModel):
    """Stats for a single word."""
    attempts: int = 0
    correct: int = 0
    proficiency: float = 0.0


class SessionStatsResponse(BaseModel):
    """GET /api/stats/{sessionId} — complete learning stats."""
    sessionId: str
    words: Dict[str, WordStats] = Field(default_factory=dict)
    total_attempts: int = 0
    total_correct: int = 0
    overall_proficiency: float = 0.0
    words_practiced: int = 0
    games_played: int = 0
    best_game_score: int = 0


# ─── Vocabulary ───────────────────────────────────────────────────

class WordInfo(BaseModel):
    """Vocabulary word metadata."""
    word: str
    display_name: str
    priority: int = Field(1, description="1 = core, 2 = extended")
    index: int = Field(0, description="Model label index")


class VocabularyResponse(BaseModel):
    """GET /api/vocabulary — available words."""
    total: int
    words: List[WordInfo]


# ─── Health ───────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """GET /health"""
    status: str = "ok"
    model_loaded: bool = False
    active_sessions: int = 0
    vocabulary_size: int = 0
    version: str = "1.0.0"


# ─── User Profile ────────────────────────────────────────────────

class ProfileCreateRequest(BaseModel):
    """POST /api/profile — register/update user profile."""
    sessionId: str = Field(..., description="Unique session identifier")
    name: str = Field(..., description="User's full name", min_length=1, max_length=100)
    email: str = Field(..., description="User's email address")
    phone: str = Field("", description="Phone number (optional)")
    preferred_language: str = Field("en", description="'en' for English, 'hi' for Hindi")


class ProfileResponse(BaseModel):
    """Response with user profile data."""
    sessionId: str
    name: str
    email: str
    phone: str = ""
    preferred_language: str = "en"
    welcome_message: str = Field("", description="Welcome text in preferred language")
    welcome_sign_data: List[Dict] = Field(default_factory=list, description="Sign language GIF data for welcome")
    created_at: Optional[float] = None


# ─── Text to Sign Language ────────────────────────────────────────

class TextToSignRequest(BaseModel):
    """POST /api/text-to-sign — convert text to sign language GIFs."""
    text: str = Field(..., description="Input text to convert to sign language", min_length=1, max_length=500)
    language: str = Field("en", description="Input language: 'en' or 'hi'")


class SignWordData(BaseModel):
    """Sign data for a single word."""
    word: str = Field(..., description="The word")
    display_name: str = Field("", description="Display-friendly name")
    found: bool = Field(True, description="Whether this word exists in our sign vocabulary")
    gif_url: str = Field("", description="URL/path to the sign GIF demonstration")
    description: str = Field("", description="Text description of how to perform the sign")
    duration_ms: int = Field(2000, description="Duration of the GIF in milliseconds")


class TextToSignResponse(BaseModel):
    """Response with sign language data for each word."""
    original_text: str
    words: List[SignWordData]
    total_words: int = 0
    matched_words: int = 0
    unmatched_words: List[str] = Field(default_factory=list)


# ─── Sign Demo Assets ────────────────────────────────────────────

class SignDemoResponse(BaseModel):
    """GET /api/signs/{word} — get sign demonstration data for a word."""
    word: str
    display_name: str
    gif_url: str = Field("", description="URL to the GIF demonstration")
    description: str = Field("", description="Step-by-step description of the sign")
    tips: List[str] = Field(default_factory=list, description="Practice tips")
    difficulty: str = Field("easy", description="easy | medium | hard")
    category: str = Field("common", description="Word category")


# ─── AR Landmarks ─────────────────────────────────────────────────

class ARLandmarksRequest(BaseModel):
    """POST /api/ar/landmarks — extract landmarks for AR overlay."""
    sessionId: str = Field(..., description="Unique session identifier")
    frame: str = Field(..., description="Base64-encoded JPEG frame")


class LandmarkPoint(BaseModel):
    """Single landmark point with 3D coordinates."""
    x: float
    y: float
    z: float
    visibility: float = Field(1.0, description="Landmark visibility confidence")


class ARLandmarksResponse(BaseModel):
    """Response with pose and hand landmarks for AR rendering."""
    pose_landmarks: List[LandmarkPoint] = Field(default_factory=list, description="33 pose landmarks")
    left_hand_landmarks: List[LandmarkPoint] = Field(default_factory=list, description="21 left hand landmarks")
    right_hand_landmarks: List[LandmarkPoint] = Field(default_factory=list, description="21 right hand landmarks")
    face_detected: bool = False
    prediction: Optional[str] = Field(None, description="Current sign prediction if available")
    confidence: float = 0.0
    gesture_hint: str = Field("", description="AR overlay hint text")


# ─── Dictionary ──────────────────────────────────────────────────

class DictionaryEntry(BaseModel):
    """Full word metadata for the dictionary."""
    word: str
    display_name: str
    hindi_name: str = ""
    category: str = "common"
    difficulty: str = "easy"
    gif_url: str = ""
    description: str = ""
    tips: List[str] = Field(default_factory=list)

class DictionaryResponse(BaseModel):
    """GET /api/dictionary"""
    total: int
    categories: List[str]
    difficulties: List[str]
    words: List[DictionaryEntry]

# ─── Progress & Dashboard ────────────────────────────────────────

class ProgressWordDetail(BaseModel):
    """Detailed proficiency for a word."""
    word: str
    display_name: str
    proficiency: float
    attempts: int
    correct: int
    mastery_tier: str = "Novice"  # Novice, Beginner, Intermediate, Advanced, Master

class ProgressResponse(BaseModel):
    """GET /api/progress/{sessionId}"""
    sessionId: str
    overall_proficiency: float
    words_practiced: int
    total_mastered: int
    word_details: List[ProgressWordDetail]

class LearningPathResponse(BaseModel):
    """GET /api/progress/{sessionId}/next"""
    suggested_words: List[DictionaryEntry]

class ActivityEvent(BaseModel):
    """Single activity entry in history."""
    type: str
    timestamp: float
    title: str
    description: str
    xp_earned: int = 0

class HistoryResponse(BaseModel):
    """GET /api/history/{sessionId}"""
    sessionId: str
    activities: List[ActivityEvent]

class AchievementInfo(BaseModel):
    """Achievement details."""
    id: str
    name: str
    description: str
    unlocked: bool = False
    unlocked_at: Optional[float] = None

class AchievementsResponse(BaseModel):
    """GET /api/achievements/{sessionId}"""
    sessionId: str
    total_unlocked: int
    achievements: List[AchievementInfo]

class XPLevelInfo(BaseModel):
    """XP bar details."""
    current_xp: int
    level: int
    next_level_xp: int
    progress_percent: float

class DashboardResponse(BaseModel):
    """Unified dashboard data."""
    sessionId: str
    user_name: str = "User"
    xp_info: XPLevelInfo
    overall_proficiency: float
    words_practiced: int
    words_mastered: int
    current_streak: int
    recent_activity: List[ActivityEvent]
    total_achievements: int
    unlocked_achievements_count: int
    best_game_score: int
    suggested_next_words: List[str]


# ─── Community Hub ───────────────────────────────────────────────

class Comment(BaseModel):
    id: str
    user_name: str
    content: str
    timestamp: float

class CommunityPost(BaseModel):
    id: str
    user_name: str
    avatar_initials: str
    content: str
    likes: int
    comments_count: int
    comments: List[Comment] = Field(default_factory=list)
    timestamp: float
    is_official: bool = False
    achievement_text: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class CreatePostRequest(BaseModel):
    sessionId: str
    content: str
    tags: List[str] = Field(default_factory=list)

class LikeRequest(BaseModel):
    sessionId: str
    postId: str

class CommunityFeedResponse(BaseModel):
    posts: List[CommunityPost]

class ActiveUser(BaseModel):
    name: str
    initials: str
    is_online: bool = True

class ActiveUsersResponse(BaseModel):
    users: List[ActiveUser]


# ─── Authentication ───────────────────────────────────────────────

class AuthRegisterRequest(BaseModel):
    """POST /api/auth/register"""
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(...)
    phone: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=6)
    preferred_language: str = Field("en", description="'en' or 'hi'")

class AuthLoginRequest(BaseModel):
    """POST /api/auth/login"""
    phone: str = Field(...)
    password: str = Field(...)

class AuthResponse(BaseModel):
    """Authentication response payload."""
    status: str = "ok"
    sessionId: str
    user_name: str
    email: str
    access_token: Optional[str] = None
    token_type: str = "bearer"
    message: str = ""
    error: Optional[str] = None


# ─── Notifications & Settings ──────────────────────────────────────

class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    type: str
    is_read: bool
    timestamp: float
    action_url: Optional[str] = None

class NotificationsListResponse(BaseModel):
    unread_count: int
    notifications: List[NotificationResponse]

class UserSettingsResponse(BaseModel):
    theme: str
    notifications_enabled: bool
    sound_enabled: bool
    daily_goal_minutes: int
    updated_at: float

class UserSettingsUpdate(BaseModel):
    theme: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    sound_enabled: Optional[bool] = None
    daily_goal_minutes: Optional[int] = None
