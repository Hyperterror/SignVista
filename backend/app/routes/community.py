from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import time
import uuid

from app.schemas import CommunityFeedResponse, CreatePostRequest, LikeRequest, CommunityPost, ActiveUsersResponse
from app.database import get_db
from app.models import CommunityPostBase
from app.dependencies import get_current_user
from app.session_store import get_active_users

router = APIRouter(prefix="/api/community", tags=["Community"])

@router.get("/feed", response_model=CommunityFeedResponse)
async def get_feed(db: Session = Depends(get_db)):
    """Get the global community feed directly from SQLite."""
    posts_db = db.query(CommunityPostBase).order_by(CommunityPostBase.timestamp.desc()).all()
    
    formatted_posts = []
    for p in posts_db:
        # Convert JSON tags safely
        tags = p.tags if p.tags else []
        
        formatted_posts.append(CommunityPost(
            id=p.id,
            user_name=p.user_name,
            avatar_initials=p.avatar_initials,
            content=p.content,
            likes=p.likes,
            comments_count=p.comments_count,
            comments=[], 
            timestamp=p.timestamp,
            is_official=p.is_official,
            achievement_text=p.achievement_text,
            tags=tags
        ))
    return CommunityFeedResponse(posts=formatted_posts)

@router.post("/post", response_model=CommunityPost)
async def create_post(request: CreatePostRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new community post inside SQLite DB."""
    new_id = str(uuid.uuid4())[:8]
    db_post = CommunityPostBase(
        id=new_id,
        user_name=current_user["name"],
        avatar_initials=current_user["name"][:2].upper(),
        content=request.content,
        likes=0,
        comments_count=0,
        timestamp=time.time(),
        is_official=False,
        achievement_text=None,
        tags=request.tags
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)

    return CommunityPost(
        id=db_post.id,
        user_name=db_post.user_name,
        avatar_initials=db_post.avatar_initials,
        content=db_post.content,
        likes=db_post.likes,
        comments_count=db_post.comments_count,
        comments=[],
        timestamp=db_post.timestamp,
        tags=db_post.tags if db_post.tags else []
    )

@router.post("/like")
async def like_post(request: LikeRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Like a community post updating SQLite natively."""
    db_post = db.query(CommunityPostBase).filter(CommunityPostBase.id == request.postId).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    db_post.likes += 1
    db.commit()
    db.refresh(db_post)
    
    return {"status": "ok", "likes": db_post.likes}

@router.get("/active-users", response_model=ActiveUsersResponse)
async def get_users():
    """Get list of currently active users from the in-memory proxy."""
    users = get_active_users()
    return ActiveUsersResponse(users=users)
