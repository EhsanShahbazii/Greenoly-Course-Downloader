"""Cookie loading: Netscape files or straight out of the user's browser."""

from __future__ import annotations

import http.cookiejar
from pathlib import Path

import requests

from .config import COOKIE_DOMAIN, SUPPORTED_BROWSERS, USER_AGENT


def load_netscape_cookies(path: str | Path) -> list[dict]:
    """Parse a Netscape ``cookies.txt`` file into Playwright/requests cookies."""
    cookies: list[dict] = []
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 7:
                continue
            domain, _flag, cpath, _secure, _exp, name, value = parts[:7]
            cookies.append(
                {
                    "name": name,
                    "value": value,
                    "domain": domain,
                    "path": cpath or "/",
                }
            )
    return cookies


def _jar_to_dicts(jar: http.cookiejar.CookieJar, domain: str) -> list[dict]:
    cookies: list[dict] = []
    for cookie in jar:
        host = (cookie.domain or "").lstrip(".")
        if domain and domain not in host:
            continue
        cookies.append(
            {
                "name": cookie.name,
                "value": cookie.value,
                "domain": cookie.domain or domain,
                "path": cookie.path or "/",
            }
        )
    return cookies


def cookies_from_browser(
    browser: str = "auto",
    domain: str = COOKIE_DOMAIN,
) -> tuple[list[dict], str]:
    """Read ``greenoly.tv`` cookies from an installed browser via browser-cookie3."""
    try:
        import browser_cookie3
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise SystemExit(
            "browser-cookie3 is not installed.\n"
            "  pip install browser-cookie3\n"
            "or pass --cookies path/to/greenoly.tv_cookies.txt"
        ) from exc

    candidates = SUPPORTED_BROWSERS if browser in {"auto", ""} else (browser,)
    errors: list[str] = []
    for name in candidates:
        loader = getattr(browser_cookie3, name, None)
        if loader is None:
            continue
        try:
            jar = loader(domain_name=domain)
        except Exception as exc:  # noqa: BLE001 - keychain/permission issues
            errors.append(f"{name}: {type(exc).__name__}")
            continue
        cookies = _jar_to_dicts(jar, domain)
        if cookies:
            return cookies, name
    detail = (" (" + ", ".join(errors) + ")") if errors else ""
    raise SystemExit(
        f"No {domain} cookies found in any browser{detail}.\n"
        "Log in to greenoly.tv in your browser first, or export a cookies.txt."
    )


def build_session(cookies: list[dict]) -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    for cookie in cookies:
        session.cookies.set(
            cookie["name"], cookie["value"], domain=cookie["domain"], path=cookie["path"]
        )
    return session


def resolve_cookies(
    cookies_file: str | Path | None,
    browser: str | None,
) -> tuple[list[dict], str]:
    """Return ``(cookies, source_description)`` from a file or the browser."""
    if cookies_file:
        path = Path(cookies_file)
        if not path.exists():
            raise SystemExit(f"Cookie file not found: {path}")
        cookies = load_netscape_cookies(path)
        if not cookies:
            raise SystemExit(f"No cookies parsed from {path}")
        return cookies, f"file {path.name}"
    return cookies_from_browser(browser or "auto")
