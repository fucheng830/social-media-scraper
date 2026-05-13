"""Response interception helper for collecting API data during page loads.

Captures network responses whose URLs match one or more *glob-like*
patterns and extracts their JSON bodies.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Iterable
from fnmatch import fnmatch

logger = logging.getLogger(__name__)


def _matches(url: str, patterns: Iterable[str]) -> bool:
    """Return True if *url* matches any of the ``fnmatch`` *patterns*."""
    return any(fnmatch(url, p) for p in patterns)


class ResponseInterceptor:
    """Intercept page responses matching URL patterns and extract JSON data.

    Usage (async)::

        interceptor = ResponseInterceptor(page, ["*homefeed*", "*note_info*"])
        page.goto("https://example.com")
        results = await interceptor.collect(timeout=30)

    Parameters
    ----------
    page:
        An async Playwright ``Page`` to attach response listeners to.
    patterns:
        URL patterns to match (``fnmatch``-style globs, e.g.
        ``"*TweetDetail*"`` or ``"*api/v1/*"``).
    """

    def __init__(self, page, patterns: Iterable[str]):
        self._page = page
        self._patterns = list(patterns)
        self._collected: list[dict] = []
        self._done = asyncio.Event()

    # ------------------------------------------------------------------
    # Async API
    # ------------------------------------------------------------------

    async def _handle_response(self, response) -> None:
        url = response.url
        if not url or not _matches(url, self._patterns):
            return
        try:
            body = await response.json()
            if isinstance(body, dict):
                self._collected.append(body)
        except Exception:
            pass  # non-JSON body — ignore

    async def collect(self, timeout: float = 30) -> list[dict]:
        """Attach listener, wait *timeout* seconds, then return captured JSON.

        The listener is removed automatically after the timeout.
        """
        self._collected.clear()
        self._done.clear()

        self._page.on("response", self._handle_response)

        try:
            # Wait until either event fires or timeout elapses
            start = time.monotonic()
            while time.monotonic() - start < timeout:
                await asyncio.sleep(1.0)
        finally:
            self._page.remove_listener("response", self._handle_response)

        return list(self._collected)

    # ------------------------------------------------------------------
    # Sync API (for use in ThreadPoolExecutor)
    # ------------------------------------------------------------------

    def _handle_response_sync(self, response) -> None:
        url = response.url
        if not url or not _matches(url, self._patterns):
            return
        try:
            body = response.json()
            if isinstance(body, dict):
                self._collected.append(body)
        except Exception:
            pass

    def collect_sync(self, timeout: float = 30) -> list[dict]:
        """Synchronous counterpart of :meth:`collect`.

        Uses ``page.wait_for_timeout`` so the Playwright sync event loop
        stays alive.
        """
        self._collected.clear()

        self._page.on("response", self._handle_response_sync)

        try:
            start = time.monotonic()
            while time.monotonic() - start < timeout:
                self._page.wait_for_timeout(1000)
        finally:
            self._page.remove_listener("response", self._handle_response_sync)

        return list(self._collected)
