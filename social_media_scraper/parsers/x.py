"""X/Twitter tweet parser -- pure functions, no side effects."""
from datetime import datetime, timezone

from social_media_scraper.types import PlatformPost, AuthorInfo, PostMetrics, MediaItem
from social_media_scraper.utils import parse_count


def parse_tweet(raw: dict) -> PlatformPost:
    """Parse a raw X API tweet dict into PlatformPost."""
    # Unwrap visibility nesting
    if raw.get("__typename") == "TweetWithVisibilityResults":
        raw = raw.get("tweet", raw)

    legacy = raw.get("legacy", {})
    tweet_id = raw.get("rest_id") or legacy.get("id_str", "")

    # Author
    user_result = raw.get("core", {}).get("user_results", {}).get("result", {})
    user_core = user_result.get("core", {})
    user_legacy = user_result.get("legacy", {}) or {}
    author_name = user_core.get("name") or user_legacy.get("name", "")
    author_avatar = ""
    avatar_obj = user_result.get("avatar")
    if isinstance(avatar_obj, dict):
        author_avatar = avatar_obj.get("image_url", "")
    if not author_avatar:
        author_avatar = user_legacy.get("profile_image_url_https", "")
    user_id = user_result.get("rest_id", "")
    if not user_id:
        import base64

        encoded_id = user_result.get("id", "")
        if encoded_id:
            try:
                user_id = base64.b64decode(encoded_id).decode().split(":")[-1]
            except Exception:
                user_id = legacy.get("user_id_str", "")

    # Media
    media_items = []
    entities_media = legacy.get("entities", {}).get("media", [])
    ext_media = legacy.get("extended_entities", {}).get("media", entities_media)
    if not ext_media:
        media_details = raw.get("mediaDetails") or []
        ext_media = [
            {
                "type": m.get("type", "photo"),
                "media_url_https": m.get("media_url_https", ""),
                "video_info": m.get("video_info"),
            }
            for m in media_details
            if isinstance(m, dict)
        ]

    video_url = None
    for m in ext_media:
        mtype = m.get("type", "photo")
        url = m.get("media_url_https", "")
        if mtype == "photo" and url:
            media_items.append(MediaItem(url=url, media_type="image"))
        elif mtype in ("video", "animated_gif") and url:
            media_items.append(MediaItem(url=url, media_type="image"))
            variants = m.get("video_info", {}).get("variants", [])
            mp4 = [v for v in variants if v.get("content_type") == "video/mp4"]
            if mp4:
                video_url = max(mp4, key=lambda v: v.get("bitrate", 0))["url"]
                media_items.append(MediaItem(url=video_url, media_type="video"))

    # Parse created_at
    published_at = None
    created_str = legacy.get("created_at", "")
    if created_str:
        try:
            published_at = datetime.strptime(created_str, "%a %b %d %H:%M:%S %z %Y")
        except Exception:
            pass

    hashtags = [h.get("text", "") for h in legacy.get("entities", {}).get("hashtags", [])]
    views = raw.get("views", {}).get("count", "0")

    # Extract card (link preview) images — X stores these in card.binding_values
    card = raw.get("card", {})
    if card:
        binding_values = card.get("legacy", {}).get("binding_values", [])
        for bv in binding_values:
            key = bv.get("key", "")
            if key in ("thumbnail_image_original", "player_image_original", "photo_image_full_size_original"):
                img_val = bv.get("value", {}).get("image_value", {})
                card_url = img_val.get("url", "")
                if card_url:
                    media_items.append(MediaItem(url=card_url, media_type="image"))

    return PlatformPost(
        platform="x",
        post_id=str(tweet_id),
        content=legacy.get("full_text", ""),
        published_at=published_at,
        author=AuthorInfo(
            user_id=str(user_id), nickname=author_name, avatar_url=author_avatar
        ),
        media=media_items,
        tags=hashtags,
        metrics=PostMetrics(
            likes=legacy.get("favorite_count", 0),
            comments=legacy.get("reply_count", 0),
            collects=legacy.get("bookmark_count", 0),
            shares=legacy.get("retweet_count", 0),
            views=parse_count(views),
        ),
        video_url=video_url,
        extra={
            "is_retweet": bool(legacy.get("retweeted_status_id_str")),
            "is_quote": bool(legacy.get("quoted_status_id_str")),
        },
        scraped_at=datetime.now(timezone.utc),
    )
