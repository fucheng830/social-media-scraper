"""Base scraper engine providing Playwright browser lifecycle and utilities.

All platform scrapers should subclass :class:`BaseScraper` to get
anti-detection, cookie management, scroll helpers, and response
interception for free.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from playwright.async_api import async_playwright, Browser, BrowserContext

from .anti_detect import inject_stealth
from .cookie import normalize_cookie, normalize_cookies
from .types import PlatformPost, PlatformComment, PlatformAccount, PostMetrics, MediaItem

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------

DEFAULT_HEADLESS: bool = True
DEFAULT_TIMEOUT: int = 30000  # ms
DEFAULT_BROWSER_ARGS: list[str] = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
]


# ---------------------------------------------------------------------------
# BaseScraper
# ---------------------------------------------------------------------------


class BaseScraper(ABC):
    """Abstract base class for platform-specific social-media scrapers.

    Provides Playwright browser lifecycle management, cookie
    normalisation, stealth injection, and reusable helper methods so
    that platform scrapers only need to implement parsing logic.

    Parameters
    ----------
    config:
        A dictionary of engine-level configuration:

        * ``headless`` (:class:`bool`) — run browser in headless mode.
          Default ``True``.
        * ``timeout`` (:class:`int`) — navigation timeout in milliseconds.
          Default ``30000``.
        * ``browser_args`` (:class:`list[str]`) — extra Chromium launch
          arguments.
        * ``rules`` (:class:`dict`) — platform-specific rules for
          dynamic scraping configuration (selectors, API patterns, etc.).

    Subclass contract
    -----------------
    Subclasses must implement the five abstract methods:
    :meth:`scrape_post`, :meth:`scrape_profile`, :meth:`scrape_comments`,
    :meth:`check_login_status`, and :meth:`login`.
    """

    # ---- attributes expected by subclasses ----

    platform: str
    """Short name of the platform (e.g. ``"x"``, ``"xhs"``)."""

    # ---- constructor ----

    def __init__(self, config: dict[str, Any] | None = None):
        cfg = config or {}

        self.headless: bool = cfg.get("headless", DEFAULT_HEADLESS)
        self.timeout: int = cfg.get("timeout", DEFAULT_TIMEOUT)
        self.browser_args: list[str] = cfg.get(
            "browser_args", list(DEFAULT_BROWSER_ARGS)
        )
        self.rules: dict[str, Any] = cfg.get("rules", {})

        # --- internal state ---
        self._playwright: Any = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._cookie_state: dict | None = None

    # ------------------------------------------------------------------
    # Browser lifecycle (async)
    # ------------------------------------------------------------------

    async def _ensure_browser(self) -> None:
        """Ensure a Playwright browser instance is running.

        Lazily calls :meth:`_launch_browser` if the browser has not been
        started yet.  Idempotent — safe to call before every scrape.
        """
        if self._browser is None:
            await self._launch_browser()

    async def _launch_browser(self, headless: bool | None = None) -> None:
        """Start Playwright and launch a Chromium browser.

        Parameters
        ----------
        headless:
            Override the instance-level ``headless`` setting.  When
            ``None`` (default), ``self.headless`` is used.
        """
        if headless is None:
            headless = self.headless

        if self._browser is not None:
            logger.debug("Browser already running, reusing")
            return

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=headless,
            timeout=self.timeout,
            args=list(self.browser_args),
        )
        logger.info("Browser launched (headless=%s)", headless)

    async def _load_state(
        self, cookie_data: dict | None = None
    ) -> BrowserContext:
        """Create (or reuse) a browser context preloaded with cookies and
        stealth scripts.

        The first call creates a new context; subsequent calls return
        the cached context so cookies accumulated during a session are
        preserved.

        Parameters
        ----------
        cookie_data:
            A storage-state dict in Playwright format, i.e.
            ``{"cookies": [...], "origins": [...]}``.  When provided it
            is used as the initial storage state for the context.  Falls
            back to ``self._cookie_state`` then to a fresh context.

        Returns
        -------
        BrowserContext
            The (cached or newly created) browser context.
        """
        if self._context is not None:
            return self._context

        if self._browser is None:
            await self._ensure_browser()

        state = cookie_data or self._cookie_state
        kwargs: dict[str, Any] = {}
        if state:
            kwargs["storage_state"] = state

        self._context = await self._browser.new_context(**kwargs)
        await inject_stealth(self._context)
        logger.debug("Browser context created (stealth injected)")
        return self._context

    async def _close_browser(self) -> None:
        """Tear down the browser context, browser, and Playwright instance.

        Safe to call multiple times — no-op if already closed.
        """
        if self._context is not None:
            await self._context.close()
            self._context = None
            logger.debug("Browser context closed")

        if self._browser is not None:
            await self._browser.close()
            self._browser = None
            logger.debug("Browser closed")

        if self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None
            logger.debug("Playwright stopped")

    # ------------------------------------------------------------------
    # Cookie management
    # ------------------------------------------------------------------

    def set_cookie_state(self, cookie_data: dict) -> None:
        """Store cookie data for subsequent browser contexts.

        Normalises ``sameSite`` values to Playwright-compatible casing
        before storing.

        Parameters
        ----------
        cookie_data:
            A dict that must contain a ``"cookies"`` key with a list of
            cookie objects (or a raw storage-state dict).
        """
        if cookie_data and "cookies" in cookie_data:
            cookie_data = {
                "cookies": normalize_cookies(cookie_data["cookies"]),
                "origins": cookie_data.get("origins", []),
            }
        self._cookie_state = cookie_data
        logger.debug("Cookie state stored (%d cookies)",
                     len(cookie_data.get("cookies", [])) if cookie_data else 0)

    # ------------------------------------------------------------------
    # Utility hooks that subclasses may override
    # ------------------------------------------------------------------

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Look up a value from the ``rules`` dict or return *default*."""
        return self.rules.get(key, default)

    # ------------------------------------------------------------------
    # Abstract scraping interface
    # ------------------------------------------------------------------

    @abstractmethod
    async def scrape_post(self, url: str) -> PlatformPost:
        """Scrape a single post by URL."""

    @abstractmethod
    async def scrape_profile(self, account_id: str) -> PlatformAccount:
        """Scrape a user/account profile."""

    @abstractmethod
    async def scrape_comments(self, post_id: str) -> list[PlatformComment]:
        """Scrape comments for a given post."""

    @abstractmethod
    async def check_login_status(self) -> bool:
        """Check whether the scraper has valid login credentials."""

    @abstractmethod
    async def login(self, method: str = "qrcode") -> None:
        """Perform login (e.g. via QR code or phone)."""
