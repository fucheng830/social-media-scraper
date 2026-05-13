"""Xiaohongshu post parser -- pure functions."""
from datetime import datetime, timezone

from social_media_scraper.types import PlatformPost, AuthorInfo, PostMetrics, MediaItem
from social_media_scraper.utils import parse_count_cn


def parse_post(raw: dict, url: str = "") -> PlatformPost:
    """Parse raw XHS API/SSR note dict into PlatformPost."""
    note = raw.get("note", raw)
    note_id = note.get("noteId") or note.get("id", "")

    user = note.get("user", {})
    author = AuthorInfo(
        user_id=user.get("userId", user.get("userid", "")),
        nickname=user.get("nickname", ""),
        avatar_url=user.get("avatar", ""),
    )

    interact = note.get("interactInfo", {})
    metrics = PostMetrics(
        likes=parse_count_cn(interact.get("likedCount", 0)),
        comments=parse_count_cn(interact.get("commentCount", 0)),
        collects=parse_count_cn(interact.get("collectedCount", 0)),
        shares=parse_count_cn(interact.get("shareCount", 0)),
    )

    images = note.get("imageList", note.get("image_list", []))
    media = []
    for img in images:
        img_url = img.get("urlDefault", img.get("url_default", img.get("url", "")))
        if img_url:
            media.append(MediaItem(url=img_url, media_type="image"))

    video_url = None
    note_type = note.get("type", "normal")
    if note_type == "video":
        video_info = note.get("video", {}) or {}
        origin_key = video_info.get("consumer", {}).get(
            "originVideoKey"
        ) or video_info.get("originVideoKey", "")
        if origin_key:
            video_url = f"https://sns-video-bd.xhscdn.com/{origin_key}"
            media.append(MediaItem(url=video_url, media_type="video"))

    tags = [
        t.get("name", t.get("tag_name", ""))
        for t in note.get("tagList", note.get("tag_list", []))
    ]

    cover_url = ""
    if note.get("cover", {}):
        cover_url = note["cover"].get("urlDefault", note["cover"].get("url", ""))
    elif media:
        cover_url = media[0].url

    return PlatformPost(
        platform="xhs",
        post_id=str(note_id),
        title=note.get("title", ""),
        content=note.get("desc", ""),
        author=author,
        media=media,
        tags=tags,
        metrics=metrics,
        cover_url=cover_url,
        video_url=video_url,
        note_type=note_type,
        source_url=url,
        scraped_at=datetime.now(timezone.utc),
    )
