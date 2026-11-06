"""Headless-browser playlist capture.

The Kavimo player fetches its HLS manifests as AES-GCM encrypted hex and only
decrypts them inside its own JavaScript. Rather than reverse-engineering that
obfuscated bundle, we hook ``TextDecoder.prototype.decode`` inside the page and
read the plaintext playlist as soon as the player produces it.
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import (
    PLAYER_ENDPOINT,
    PLAYLIST_TIMEOUT_MS,
    PLAYER_SETTLE_MS,
    USER_AGENT,
    VOD_HOST,
)

_CAPTURE_HOOK = r"""
(() => {
  if (window.__greenoly_cap) return;
  const MAX_HEIGHT = __MAX_HEIGHT__;
  const cap = window.__greenoly_cap = { master: null, media: null, variant: null };

  function variantsOf(txt) {
    const lines = txt.split(/\r?\n/);
    const out = [];
    for (let i = 0; i < lines.length; i++) {
      if (!lines[i].startsWith('#EXT-X-STREAM-INF')) continue;
      let url = '';
      for (let j = i + 1; j < lines.length; j++) {
        if (lines[j].trim() && !lines[j].startsWith('#')) { url = lines[j].trim(); break; }
      }
      if (!url) continue;
      const res = lines[i].match(/RESOLUTION=(\d+)x(\d+)/);
      const bw = (lines[i].match(/BANDWIDTH=(\d+)/) || [])[1] || 0;
      out.push({
        hdr: lines[i],
        url,
        height: res ? parseInt(res[2], 10) : 0,
        px: res ? parseInt(res[1], 10) * parseInt(res[2], 10) : 0,
        bw: parseInt(bw, 10) || 0,
      });
    }
    return out;
  }

  function rewrite(txt) {
    let variants = variantsOf(txt);
    if (!variants.length) return txt;
    if (MAX_HEIGHT) {
      const capped = variants.filter(v => v.height > 0 && v.height <= MAX_HEIGHT);
      if (capped.length) variants = capped;
    }
    variants.sort((a, b) => (b.px - a.px) || (b.bw - a.bw));
    cap.variant = variants[0].url;
    // Keep only the winning rendition: the player's ABR would otherwise drop
    // to a lower bitrate as soon as it starts measuring the connection.
    const best = variants.filter(v => v.px === variants[0].px);
    return '#EXTM3U\n' + best.map(v => v.hdr + '\n' + v.url).join('\n') + '\n';
  }

  const original = TextDecoder.prototype.decode;
  TextDecoder.prototype.decode = function (...args) {
    let out = original.apply(this, args);
    try {
      if (typeof out === 'string' && out.includes('#EXTM3U')) {
        if (out.includes('#EXT-X-STREAM-INF')) {
          cap.master = out;
          out = rewrite(out);
        } else if (out.includes('#EXTINF')) {
          cap.media = out;
        }
      }
    } catch (e) {}
    return out;
  };
})();
"""


@dataclass
class CapturedPlaylist:
    master: str | None
    media: str
    variant_url: str | None = None
    base_url: str = VOD_HOST


def _hook_script(max_height: int | None) -> str:
    return _CAPTURE_HOOK.replace("__MAX_HEIGHT__", str(max_height or 0))


def _read_capture(page) -> dict | None:
    for frame in page.frames:
        try:
            value = frame.evaluate("window.__greenoly_cap || null")
        except Exception:  # noqa: BLE001 - detached frames
            continue
        if value and value.get("media"):
            return value
    return None


def capture_playlist(
    browser,
    cookies: list[dict],
    lesson_id: str,
    max_height: int | None = None,
    timeout_ms: int = PLAYLIST_TIMEOUT_MS,
    settle_ms: int = PLAYER_SETTLE_MS,
) -> CapturedPlaylist:
    """Open the lesson player and return its decrypted media playlist."""
    context = browser.new_context(user_agent=USER_AGENT)
    context.add_cookies(cookies)
    context.add_init_script(_hook_script(max_height))
    page = context.new_page()
    manifests: list[str] = []
    page.on(
        "request",
        lambda request: manifests.append(request.url)
        if ".m3u8" in request.url
        else None,
    )
    try:
        page.goto(
            PLAYER_ENDPOINT.format(lesson_id=lesson_id),
            wait_until="domcontentloaded",
            timeout=timeout_ms,
        )
        page.wait_for_timeout(settle_ms)
        try:
            page.mouse.click(400, 300)
        except Exception:  # noqa: BLE001 - best-effort autoplay nudge
            pass

        waited = 0
        capture = None
        while waited < timeout_ms:
            capture = _read_capture(page)
            if capture:
                break
            page.wait_for_timeout(500)
            waited += 500
        if not capture:
            raise RuntimeError(
                "Timed out waiting for the player playlist "
                "(expired cookies or a locked lesson?)"
            )

        base_url = manifests[-1] if manifests else VOD_HOST
        return CapturedPlaylist(
            master=capture.get("master"),
            media=capture["media"],
            variant_url=capture.get("variant"),
            base_url=base_url,
        )
    finally:
        context.close()
