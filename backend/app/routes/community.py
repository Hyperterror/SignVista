"""
SignVista — Community Routes

GET  /api/community/feed                    — paginated global feed
POST /api/community/post                    — create a post
POST /api/community/like                    — toggle like (one per user per post)
GET  /api/community/posts/{id}/comments     — list comments
POST /api/community/posts/{id}/comments     — add a comment
GET  /api/community/active-users            — users active in the last 15 minutes
"""

import time
import uuid
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import CommunityCommentBase, CommunityPostBase, PostLike
from app.rate_limit import enforce
from app.schemas import (
    ActiveUsersResponse,
    Comment,
    CommunityFeedResponse,
    CommunityPost,
    CreateCommentRequest,
    CreatePostRequest,
    LikeRequest,
)
from app.session_store import get_active_users

router = APIRouter(prefix="/api/community", tags=["Community"])


def _to_schema(p: CommunityPostBase, liked: bool) -> CommunityPost:
    return CommunityPost(
        id=p.id,
        user_name=p.user_name,
        avatar_initials=p.avatar_initials,
        content=p.content,
        likes=p.likes or 0,
        comments_count=p.comments_count or 0,
        liked_by_me=liked,
        comments=[],
        timestamp=p.timestamp,
        is_official=bool(p.is_official),
        achievement_text=p.achievement_text,
        tags=p.tags or [],
    )


@router.get("/feed", response_model=CommunityFeedResponse)
def get_feed(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Global community feed, newest first."""
    base = db.query(CommunityPostBase)
    total = base.count()
    posts = base.order_by(CommunityPostBase.timestamp.desc()).offset(offset).limit(limit).all()

    liked_ids = set()
    if posts:
        liked_ids = {
            r[0] for r in db.query(PostLike.post_id).filter(
                PostLike.user_id == current_user["user_id"],
                PostLike.post_id.in_([p.id for p in posts]),
            )
        }

    return CommunityFeedResponse(
        posts=[_to_schema(p, p.id in liked_ids) for p in posts],
        total=total,
        has_more=offset + len(posts) < total,
    )


@router.post("/post", response_model=CommunityPost)
def create_post(request: CreatePostRequest, current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new community post as the authenticated user."""
    enforce(f"post:{current_user['user_id']}", limit=10, window_seconds=600,
            detail="You're posting too often. Please wait a few minutes.")
    post = CommunityPostBase(
        id=uuid.uuid4().hex[:12],
        user_id=current_user["user_id"],
        user_name=current_user["name"],
        avatar_initials=current_user["name"][:2].upper(),
        content=request.content,
        likes=0,
        comments_count=0,
        timestamp=time.time(),
        is_official=False,
        achievement_text=None,
        tags=request.tags,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return _to_schema(post, False)


@router.post("/like")
def like_post(request: LikeRequest, current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Toggle the current user's like on a post."""
    post = db.query(CommunityPostBase).filter(CommunityPostBase.id == request.postId).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    existing = db.query(PostLike).filter(
        PostLike.post_id == post.id, PostLike.user_id == current_user["user_id"]
    ).first()
    if existing:
        db.delete(existing)
        liked = False
    else:
        db.add(PostLike(post_id=post.id, user_id=current_user["user_id"]))
        liked = True
    try:
        db.flush()
    except IntegrityError:
        # Concurrent duplicate like — treat as already liked
        db.rollback()
        liked = True

    post.likes = db.query(PostLike).filter(PostLike.post_id == post.id).count()
    db.commit()
    return {"status": "ok", "likes": post.likes, "liked": liked}


@router.get("/posts/{post_id}/comments", response_model=List[Comment])
def list_comments(post_id: str, current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if db.query(CommunityPostBase.id).filter(CommunityPostBase.id == post_id).first() is None:
        raise HTTPException(status_code=404, detail="Post not found")
    rows = (
        db.query(CommunityCommentBase)
        .filter(CommunityCommentBase.post_id == post_id)
        .order_by(CommunityCommentBase.timestamp.asc())
        .limit(500)
        .all()
    )
    return [Comment(id=c.id, user_name=c.user_name, content=c.content, timestamp=c.timestamp) for c in rows]


@router.post("/posts/{post_id}/comments", response_model=Comment)
def add_comment(post_id: str, request: CreateCommentRequest,
                current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    enforce(f"comment:{current_user['user_id']}", limit=30, window_seconds=600,
            detail="You're commenting too often. Please wait a few minutes.")
    post = db.query(CommunityPostBase).filter(CommunityPostBase.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    comment = CommunityCommentBase(
        id=uuid.uuid4().hex[:12],
        post_id=post_id,
        user_id=current_user["user_id"],
        user_name=current_user["name"],
        content=request.content,
        timestamp=time.time(),
    )
    db.add(comment)
    post.comments_count = (post.comments_count or 0) + 1
    db.commit()
    return Comment(id=comment.id, user_name=comment.user_name, content=comment.content, timestamp=comment.timestamp)


@router.get("/active-users", response_model=ActiveUsersResponse)
def get_users(current_user: Dict = Depends(get_current_user)):
    """Users active in the last 15 minutes (excluding yourself)."""
    return ActiveUsersResponse(users=get_active_users(exclude_user_id=current_user["user_id"]))
