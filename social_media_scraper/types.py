from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel


class AuthorInfo(BaseModel):
    user_id: str
    nickname: str
    avatar_url: str | None = None
    follower_count: int | None = None
    bio: str | None = None


class MediaItem(BaseModel):
    url: str
    local_path: str | None = None
    media_type: str = "image"
    width: int | None = None
    height: int | None = None
    duration: float | None = None


class PostMetrics(BaseModel):
    likes: int = 0
    comments: int = 0
    collects: int = 0
    shares: int = 0
    views: int | None = None


class PlatformPost(BaseModel):
    platform: str
    post_id: str
    title: str | None = None
    content: str
    author: AuthorInfo
    media: list[MediaItem] = []
    tags: list[str] = []
    metrics: PostMetrics = PostMetrics()
    cover_url: str | None = None
    video_url: str | None = None
    note_type: str | None = None
    extra: dict | None = None
    published_at: datetime | None = None
    scraped_at: datetime
    source_url: str | None = None


class PlatformComment(BaseModel):
    comment_id: str
    post_id: str
    user_name: str
    user_id: str
    content: str
    like_count: int = 0
    sub_comment_count: int = 0
    parent_comment_id: str | None = None
    created_at: datetime | None = None


class PlatformAccount(BaseModel):
    platform: str
    account_id: str
    nickname: str
    avatar_url: str | None = None
    follower_count: int | None = None
    following_count: int | None = None
    bio: str | None = None
    cookies: dict | None = None
