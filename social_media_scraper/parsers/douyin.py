"""Douyin video parser — pure functions."""
from datetime import datetime, timezone
from social_media_scraper.types import PlatformPost, AuthorInfo, PostMetrics, MediaItem


def parse_video(raw: dict) -> PlatformPost:
    """Parse a raw Douyin aweme/detail API response into PlatformPost."""
    author = raw.get("author", {})
    stats = raw.get("statistics", {})
    video = raw.get("video", {})
    text_extra = raw.get("text_extra", [])

    cover_url = ""
    if video.get("cover"):
        urls = video["cover"].get("url_list", [])
        cover_url = urls[0] if urls else ""

    video_url = ""
    if video.get("play_addr"):
        urls = video["play_addr"].get("url_list", [])
        video_url = urls[0] if urls else ""

    avatar_url = ""
    if author.get("avatar_larger"):
        urls = author["avatar_larger"].get("url_list", [])
        avatar_url = urls[0] if urls else ""

    desc = raw.get("desc", "")

    return PlatformPost(
        platform="douyin",
        post_id=raw.get("aweme_id", ""),
        title=desc[:80] if desc else "",
        content=desc,
        author=AuthorInfo(
            user_id=str(author.get("uid", "")),
            nickname=author.get("nickname", ""),
            avatar_url=avatar_url or None,
        ),
        media=[MediaItem(url=video_url, media_type="video")] if video_url else [],
        tags=[t.get("hashtag_name", "") for t in text_extra if t.get("hashtag_name")],
        metrics=PostMetrics(
            likes=stats.get("digg_count", 0),
            comments=stats.get("comment_count", 0),
            shares=stats.get("share_count", 0),
            views=stats.get("play_count", 0),
        ),
        cover_url=cover_url,
        video_url=video_url,
        note_type="video",
        scraped_at=datetime.now(timezone.utc),
    )
