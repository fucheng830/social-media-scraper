"""Platform-specific parsers -- pure functions with no side effects."""

from social_media_scraper.parsers.x import parse_tweet
from social_media_scraper.parsers.xhs import parse_post
from social_media_scraper.parsers.douyin import parse_video

__all__ = ["parse_tweet", "parse_post", "parse_video"]
