"""Cookie normalization utilities for Playwright compatibility."""

from __future__ import annotations


def normalize_cookie(cookie: dict) -> dict:
    """Normalize a single cookie dict for Playwright compatibility.

    Handles:
    - sameSite: maps various formats to Playwright's accepted values
      (Strict, Lax, None) with correct casing.
    - expirationDate: converts browser-extension format to Playwright's
      ``expires`` field.

    Returns a new dict (does not mutate the input).
    """
    pc: dict = {
        "name": cookie.get("name", ""),
        "value": cookie.get("value", ""),
        "domain": cookie.get("domain", ""),
        "path": cookie.get("path", "/"),
        "secure": cookie.get("secure", True),
        "httpOnly": cookie.get("httpOnly", False),
    }

    # --- sameSite normalization ---
    ss = (cookie.get("sameSite") or "").lower()
    if ss in ("no_restriction", "none"):
        pc["sameSite"] = "None"
    elif ss in ("strict",):
        pc["sameSite"] = "Strict"
    else:
        pc["sameSite"] = "Lax"

    # --- expires handling ---
    if "expires" in cookie:
        pc["expires"] = cookie["expires"]
    elif "expirationDate" in cookie and cookie["expirationDate"]:
        pc["expires"] = cookie["expirationDate"]

    return pc


def normalize_cookies(cookies: list[dict]) -> list[dict]:
    """Normalize a list of cookie dicts.

    Equivalent to ``[normalize_cookie(c) for c in cookies]``.
    """
    return [normalize_cookie(c) for c in cookies]
