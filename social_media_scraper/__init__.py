"""social-media-scraper — Playwright-based social media scraping engine."""

# Types
from .types import (
    AuthorInfo,
    MediaItem,
    PlatformAccount,
    PlatformComment,
    PlatformPost,
    PostMetrics,
)

# Engine
from .engine import BaseScraper

# Protocols
from .scraper import ScraperProtocol

# Utilities
from .utils import parse_count, parse_count_cn

# Cookie normalisation
from .cookie import normalize_cookie, normalize_cookies

# Anti-detection
from .anti_detect import inject_stealth, inject_stealth_sync, STEALTH_SCRIPT

# Scroll helpers
from .scroll import scroll_to_load, scroll_to_load_sync

# Response interception
from .response import ResponseInterceptor

# Parsers
from .parsers import parse_tweet, parse_post, parse_video

__version__ = "0.1.0"

__all__ = [
    # Types
    "AuthorInfo",
    "MediaItem",
    "PlatformAccount",
    "PlatformComment",
    "PlatformPost",
    "PostMetrics",
    # Engine
    "BaseScraper",
    "ScraperProtocol",
    # Utilities
    "parse_count",
    "parse_count_cn",
    # Cookie
    "normalize_cookie",
    "normalize_cookies",
    # Anti-detect
    "inject_stealth",
    "inject_stealth_sync",
    "STEALTH_SCRIPT",
    # Scroll
    "scroll_to_load",
    "scroll_to_load_sync",
    # Response
    "ResponseInterceptor",
    # Parsers
    "parse_tweet",
    "parse_post",
    "parse_video",
    # Version
    "__version__",
]
