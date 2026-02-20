from typing import List
from fastapi import APIRouter, HTTPException, Depends
from app.schemas import CommunityFeedResponse, CreatePostRequest, LikeRequest, CommunityPost, ActiveUsersResponse
from app.session_store import get_session, get_community_feed, add_community_post, toggle_like, get_active_users
from app.dependencies import get_current_user
import time
import uuid

router = APIRouter(prefix="/api/community", tags=["Community"])

@router.get("/feed", response_model=CommunityFeedResponse)
async def get_feed():
    """Get the global community feed."""
    posts = get_community_feed()
    # Map raw dicts to CommunityPost models
    formatted_posts = []
    for p in posts:
        formatted_posts.append(CommunityPost(
            id=p["id"],
            user_name=p["user_name"],
            avatar_initials=p["avatar_initials"],
            content=p["content"],
            likes=p["likes"],
            comments_count=len(p["comments"]),
            comments=[], # Comments not fully implemented in frontend yet
            timestamp=p["timestamp"],
            is_official=p.get("is_official", False),
            achievement_text=p.get("achievement_text"),
            tags=p.get("tags", [])
        ))
    return CommunityFeedResponse(posts=formatted_posts)

@router.post("/post", response_model=CommunityPost)
async def create_post(request: CreatePostRequest, current_user: dict = Depends(get_current_user)):
    """Create a new community post."""
    session = get_session(request.sessionId)
    
    # Use real user data from JWT
    new_post = {
        "id": str(uuid.uuid4())[:8],
        "user_name": current_user["name"],
        "avatar_initials": current_user["name"][:2].upper(),
        "content": request.content,
        "likes": 0,
        "comments": [],
        "timestamp": time.time(),
        "is_official": False,
        "achievement_text": None,
        "tags": request.tags
    }
    
    add_community_post(new_post)
    return CommunityPost(
        id=new_post["id"],
        user_name=new_post["user_name"],
        avatar_initials=new_post["avatar_initials"],
        content=new_post["content"],
        likes=new_post["likes"],
        comments_count=0,
        comments=[],
        timestamp=new_post["timestamp"],
        tags=new_post["tags"]
    )

@router.post("/like")
async def like_post(request: LikeRequest, current_user: dict = Depends(get_current_user)):
    """Like a community post."""
    post = toggle_like(request.postId, request.sessionId)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"status": "ok", "likes": post["likes"]}

@router.get("/active-users", response_model=ActiveUsersResponse)
async def get_users():
    """Get list of currently active users."""
    users = get_active_users()
    return ActiveUsersResponse(users=users)
