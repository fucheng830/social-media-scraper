"""Generic scroll-to-load helpers for infinite-scroll pages.

These helpers steadily scroll a Playwright page while collecting
content until a target count is reached or no new content appears.
"""

from __future__ import annotations

import asyncio
import logging
import random

logger = logging.getLogger(__name__)


async def scroll_to_load(
    page,
    max_items: int = 50,
    seen_ids: set[str] | None = None,
    stale_limit: int = 10,
    scroll_delay: tuple[float, float] = (1.5, 3.5),
) -> None:
    """Scroll a Playwright async ``page`` repeatedly until one of these
    conditions is met:

    * ``len(seen_ids) >= max_items``
    * The page height has not changed for ``stale_limit`` consecutive scrolls.

    Parameters
    ----------
    page:
        A Playwright async ``Page``.
    max_items:
        Stop when ``seen_ids`` reaches this size.  Set to ``0`` to disable
        the item-count check.
    seen_ids:
        An optional set that callers populate with unique item ids (e.g.
        via response interception or DOM extraction).  The function
        **mutates** this set in-place so the caller can observe progress.
    stale_limit:
        Number of consecutive unchanged-height scrolls before giving up.
    scroll_delay:
        ``(min_seconds, max_seconds)`` range for the per-iteration delay.
    """
    if seen_ids is None:
        seen_ids = set()

    last_height = 0
    stale_count = 0
    iteration = 0

    while True:
        iteration += 1

        # Scroll to bottom of current page
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

        # Randomised human-like delay
        delay = scroll_delay[0] + random.uniform(0, scroll_delay[1] - scroll_delay[0])
        await asyncio.sleep(delay)

        new_height = await page.evaluate("document.body.scrollHeight")
        current = len(seen_ids)

        if iteration % 5 == 0:
            logger.debug(
                "Scroll #%d: %d items collected, height %d",
                iteration, current, new_height,
            )

        # Check item-count limit
        if max_items and current >= max_items:
            logger.info("Reached max_items=%d after %d scrolls", max_items, iteration)
            break

        # Check staleness
        if new_height == last_height:
            stale_count += 1
            if stale_count >= stale_limit:
                logger.info(
                    "Page height unchanged for %d scrolls, stopping (collected %d items)",
                    stale_count, current,
                )
                break
        else:
            stale_count = 0

        last_height = new_height


def scroll_to_load_sync(
    page,
    max_items: int = 50,
    seen_ids: set[str] | None = None,
    stale_limit: int = 10,
    scroll_delay: tuple[float, float] = (1.5, 3.5),
) -> None:
    """Synchronous counterpart of :func:`scroll_to_load`.

    Uses ``page.wait_for_timeout`` instead of ``asyncio.sleep`` so the
    Playwright sync event loop stays alive (necessary for response
    interception to work in a thread).
    """
    import time as _time

    if seen_ids is None:
        seen_ids = set()

    last_height = 0
    stale_count = 0
    iteration = 0

    while True:
        iteration += 1

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

        delay_ms = int(
            (scroll_delay[0] + random.uniform(0, scroll_delay[1] - scroll_delay[0]))
            * 1000
        )
        page.wait_for_timeout(delay_ms)

        new_height = page.evaluate("document.body.scrollHeight")
        current = len(seen_ids)

        if iteration % 5 == 0:
            logger.debug(
                "Scroll #%d: %d items collected, height %d",
                iteration, current, new_height,
            )

        if max_items and current >= max_items:
            logger.info("Reached max_items=%d after %d scrolls", max_items, iteration)
            break

        if new_height == last_height:
            stale_count += 1
            if stale_count >= stale_limit:
                logger.info(
                    "Page height unchanged for %d scrolls, stopping (collected %d items)",
                    stale_count, current,
                )
                break
        else:
            stale_count = 0

        last_height = new_height
