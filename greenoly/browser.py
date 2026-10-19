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
    return '#EXTM3U\n' + variants.map(v => v.hdr + '\n' + v.url).join('\n') + '\n';
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


