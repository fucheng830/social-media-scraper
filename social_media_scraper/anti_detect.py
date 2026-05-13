"""Anti-detection / stealth utilities for Playwright browsers.

Provides async and sync helpers to inject stealth scripts into browser
contexts, making automated browsers harder to detect by social-media
platforms.
"""

from __future__ import annotations

import logging
from importlib.resources import files

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Inline stealth script (loaded via context.add_init_script every time)
# ---------------------------------------------------------------------------

STEALTH_SCRIPT = """
// Override navigator properties that automation detection scripts check
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en-US', 'en'] });
Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });

// Spoof chrome object (some sites check for chrome.runtime)
window.chrome = { runtime: {}, loadTimes: function(){}, csi: function(){}, app: {} };

// Override permissions to avoid "AutomationControlled" flag
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications' ?
        Promise.resolve({ state: Notification.permission }) :
        originalQuery(parameters)
);

// Plugins spoof
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5],
});

// Hardware concurrency
Object.defineProperty(navigator, 'hardwareConcurrency', {
    get: () => 8,
});
"""


def _resolve_stealth_min_js_path() -> str | None:
    """Return the absolute path to ``stealth.min.js`` bundled in the package.

    Uses :mod:`importlib.resources` so the package can be installed as a
    wheel or remain editable and still locate the file.
    """
    try:
        resource = files("social_media_scraper") / "stealth.min.js"
        if resource.is_file():
            return str(resource)
    except Exception:
        logger.debug("Could not resolve stealth.min.js via importlib.resources")
    return None


# ---- Async helpers -------------------------------------------------------


async def inject_stealth(context) -> None:
    """Inject anti-detection scripts into a Playwright **async** browser context.

    Call this **once** per context, before opening any pages:

    .. code-block:: python

        ctx = await browser.new_context()
        await inject_stealth(ctx)
        page = await ctx.new_page()
    """
    # 1. Bundled puppeteer-extra stealth script (if available)
    stealth_path = _resolve_stealth_min_js_path()
    if stealth_path:
        await context.add_init_script(path=stealth_path)

    # 2. Inline overrides (always applied)
    await context.add_init_script(script=STEALTH_SCRIPT)


# ---- Sync helpers --------------------------------------------------------


def inject_stealth_sync(context) -> None:
    """Inject anti-detection scripts into a Playwright **sync** browser context.

    Call this **once** per context, before opening any pages:

    .. code-block:: python

        ctx = browser.new_context()
        inject_stealth_sync(ctx)
        page = ctx.new_page()
    """
    stealth_path = _resolve_stealth_min_js_path()
    if stealth_path:
        context.add_init_script(path=stealth_path)

    context.add_init_script(script=STEALTH_SCRIPT)
