#!/usr/bin/env python3
"""Build a reproducible StreamBridge distribution with provider fallback badges."""

from __future__ import annotations

import base64
import gzip
import html
import json
import re
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PUBLIC = ROOT / "public"
STREAMING_DIR = PUBLIC / "badges" / "streaming-fixed"
TECHNICAL_DIR = PUBLIC / "badges" / "technical-fixed"
LOGO_CACHE = DATA / "logo-cache"
BASE_JSON = DATA / "badges-base.json"
BASE_JSON_GZ_B64 = DATA / "badges-base.json.gz.b64"
RULES_JSON = DATA / "streaming-rules.json"

# Pin upstream so a future StreamBridge change cannot silently break our patches.
UPSTREAM_COMMIT = "06e40a16027561516d2f9054ddb20339a30936ab"
UPSTREAM_ROOT = f"https://raw.githubusercontent.com/h4harsimran/streambridge/{UPSTREAM_COMMIT}/"
UPSTREAM_FILES = (
    "index.js",
    "lib/commonClient.js",
    "lib/embyClient.js",
    "lib/jellyfinClient.js",
    "lib/redact.js",
    "public/configure.html",
)

DATA.mkdir(parents=True, exist_ok=True)
STREAMING_DIR.mkdir(parents=True, exist_ok=True)
TECHNICAL_DIR.mkdir(parents=True, exist_ok=True)
LOGO_CACHE.mkdir(parents=True, exist_ok=True)


def fetch_bytes(url: str, timeout: int = 45) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "streambridge-studio-markers/3.0"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def restore_upstream() -> None:
    """Restore the small pinned upstream source tree before applying patches."""
    for relative in UPSTREAM_FILES:
        target = ROOT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(fetch_bytes(UPSTREAM_ROOT + relative))


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"{label}: patch anchor not found in {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


if BASE_JSON_GZ_B64.exists():
    compressed = base64.b64decode(BASE_JSON_GZ_B64.read_text(encoding="ascii"))
    BASE_JSON.write_bytes(gzip.decompress(compressed))

if not BASE_JSON.exists():
    raise RuntimeError(
        "data/badges-base.json.gz.b64 is required; it is the pinned rule snapshot and must be committed"
    )

restore_upstream()

base = json.loads(BASE_JSON.read_text(encoding="utf-8"))
if len(base.get("filters", [])) != 245:
    raise RuntimeError("Unexpected base filter count")


def hidden_marker(value: str) -> str:
    bits = "".join(f"{byte:08b}" for byte in value.encode("utf-8"))
    payload = "".join("\u200b" if bit == "0" else "\u200c" for bit in bits)
    return f"\u2063{payload}\u2064"


bahamut_anime_marker = hidden_marker("巴哈姆特動畫瘋")
line_tv_marker = hidden_marker("LINE TV")
base["filters"].extend(
    [
        {
            "type": "filter",
            "id": "stream-145",
            "name": "巴哈姆特動畫瘋",
            "pattern": (
                r"(?:(?:^|[^A-Za-z0-9])(?:ANi|ANI|巴哈姆特(?:動畫瘋|动画疯)|"
                r"動畫瘋|动画疯|(?:Bahamut|BAHAMUT)[\s._-]*(?:Anime|ANIME)"
                r"(?:[\s._-]*(?:Crazy|CRAZY))?|ani\.gamer\.com\.tw)"
                r"(?=$|[^A-Za-z0-9])|"
                + bahamut_anime_marker
                + ")"
            ),
            "caseSensitive": True,
            "tagColor": "#00000000",
            "borderColor": "#00000000",
            "textColor": "#FFFFFF",
            "tagStyle": "filled",
            "imageURL": "",
            "isEnabled": True,
            "groupId": "gs",
        },
        {
            "type": "filter",
            "id": "stream-146",
            "name": "LINE TV",
            "pattern": (
                r"(?i)(?:(?:^|[^A-Za-z0-9])LINE[\s._-]*TV(?=$|[^A-Za-z0-9])|"
                + line_tv_marker
                + ")"
            ),
            "tagColor": "#00000000",
            "borderColor": "#00000000",
            "textColor": "#FFFFFF",
            "tagStyle": "filled",
            "imageURL": "",
            "isEnabled": True,
            "groupId": "gs",
        },
    ]
)
BASE_JSON.write_text(json.dumps(base, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

streaming_filters = [f for f in base["filters"] if f.get("groupId") == "gs"]
if len(streaming_filters) != 146:
    raise RuntimeError("Unexpected streaming filter count")

marker_re = re.compile(r"\u2063[\u200b\u200c]+\u2064")
rules = []
for item in streaming_filters:
    pattern = item.get("pattern", "")
    marker_match = marker_re.search(pattern)
    rules.append(
        {
            "name": item.get("name", ""),
            "pattern": pattern,
            "marker": marker_match.group(0) if marker_match else "",
            "caseSensitive": bool(item.get("caseSensitive")),
        }
    )
RULES_JSON.write_text(
    json.dumps(rules, ensure_ascii=False, indent=2),
    encoding="utf-8",
)


# Transparent coloured wordmarks. They are cached at build time and embedded;
# deployed badges never depend on a nested remote image.
PNG_LOGOS = {
    "Netflix": "netflix-red.png",
    "Amazon Prime Video": "prime-video.png",
    "HBO Max": "hbo-max-purple.png",
    "Disney+": "disney-plus-blue.png",
    "Hulu": "hulu-green.png",
    "Apple TV+": "apple-tv-plus.png",
    "Apple TV": "apple-tv-plus.png",
    "iTunes": "apple-tv-plus.png",
    "Paramount+": "paramount-plus-blue.png",
    "Peacock": "peacock.png",
    "Crunchyroll": "crunchyroll-orange.png",
}
LOGO_ROOT = "https://raw.githubusercontent.com/kingsizew/badges/main/badge-images/streaming/"
QUALITY_LOGO_ROOT = "https://raw.githubusercontent.com/kingsizew/badges/main/badge-images/quality/"

# Real vector wordmarks for the most important domestic platforms. Embedding
# the source bytes avoids font substitution and keeps each badge self-contained.
SVG_LOGOS = {
    "爱奇艺": (
        "iqiyi-2022.svg",
        "https://upload.wikimedia.org/wikipedia/commons/0/0f/IQIYI_logo_%282022%29.svg",
    ),
    "腾讯视频": (
        "wetv.svg",
        "https://upload.wikimedia.org/wikipedia/commons/5/54/WeTV_logo.svg",
    ),
    "WeTV": (
        "wetv.svg",
        "https://upload.wikimedia.org/wikipedia/commons/5/54/WeTV_logo.svg",
    ),
    "优酷": (
        "youku-compact.svg",
        "https://upload.wikimedia.org/wikipedia/commons/0/08/Youku_logo_%282%29.svg",
    ),
    "哔哩哔哩": (
        "bilibili-2023.svg",
        "https://upload.wikimedia.org/wikipedia/commons/1/12/Bilibili_2023.svg",
    ),
    "Bstation": (
        "bilibili-2023.svg",
        "https://upload.wikimedia.org/wikipedia/commons/1/12/Bilibili_2023.svg",
    ),
    "AcFun": (
        "acfun.svg",
        "https://upload.wikimedia.org/wikipedia/commons/8/8c/AcFun.svg",
    ),
}

# Disc-format marks are technical badges, not streaming-provider cards. Keep
# their official vector silhouette, recolour it for the dark player UI, and
# preserve a compact intrinsic aspect ratio so they align with 4K/HDR badges.
TRANSPARENT_SVG_LOGOS = {
    "Ultra HD Blu-ray": (
        "ultra-hd-blu-ray.svg",
        "https://upload.wikimedia.org/wikipedia/commons/2/21/Ultra_HD_Blu-ray_%28logo%29.svg",
        290,
        100,
    ),
}


# Brand colours are used directly on transparent wordmarks. There is no card,
# plate, rounded rectangle, or generic grey/white background around providers.
BRAND_STYLES = {
    "爱奇艺": ("iQIYI", "#00BE06", "#E9FFE9", "#D5F9DA"),
    "腾讯视频": ("Tencent Video", "#00A8E8", "#EAFBFF", "#D8F4FF"),
    "WeTV": ("WeTV", "#00C878", "#EBFFF6", "#D7F8E9"),
    "优酷": ("YOUKU", "#FF5C35", "#FFF4F0", "#EAF8FF"),
    "芒果TV": ("Mango TV", "#FF7A1A", "#FFF5E9", "#FFE8C8"),
    "哔哩哔哩": ("bilibili", "#00A1D6", "#ECFAFF", "#DDF5FF"),
    "Bstation": ("Bstation", "#00A1D6", "#ECFAFF", "#DDF5FF"),
    "AcFun": ("AcFun", "#FD4C5D", "#FFF0F2", "#FFE0E4"),
    "华数TV": ("Wasu TV", "#FF3344", "#FFF1F2", "#FFE1E4"),
    "百视TV": ("BesTV", "#8D74FF", "#F4F0FF", "#E8E0FF"),
    "埋堆堆": ("Maiduidui", "#FF5268", "#FFF0F3", "#FFE0E6"),
    "SOHU VIDEO": ("SOHU", "#FF453A", "#FFF0F0", "#FFE0E1"),
    "MIGU VIDEO": ("MIGU", "#FF4DA3", "#FFF0F8", "#FFE0F1"),
    "PPTV": ("PP VIDEO", "#3D8BFF", "#EEF5FF", "#DDEBFF"),
    "XIGUA VIDEO": ("XIGUA", "#FF5B50", "#FFF1EF", "#FFE1DE"),
    "DOUYIN": ("DOUYIN", "#25F4EE", "#F6F6F6", "#E8E8E8"),
    "M1905": ("M1905", "#D8B45C", "#FFF9ED", "#F7EBCF"),
    "巴哈姆特動畫瘋": ("動畫瘋", "#25B7C9", "#F5F6F7", "#E8EAED"),
    "LINE TV": ("LINE TV", "#06C755", "#ECFFF1", "#D8FFE2"),
    "Crunchyroll": ("Crunchyroll", "#F47521", "#FFF4EA", "#FFE5D0"),
    "Apple TV+": ("tv+", "#FFFFFF", "#101010", "#292929"),
    "Apple TV": ("tv", "#FFFFFF", "#101010", "#292929"),
    "iTunes": ("iTunes", "#FFFFFF", "#101010", "#292929"),
    "Netflix": ("N", "#E50914", "#FFF2F2", "#FFE3E4"),
    "Amazon Prime Video": ("prime video", "#FFFFFF", "#102A43", "#184D70"),
    "HBO Max": ("HBO max", "#9D7CFF", "#F3EFFF", "#E6DFFF"),
    "Disney+": ("Disney+", "#4EA7FF", "#F1F4FF", "#DFE7FF"),
    "Hulu": ("hulu", "#1CE783", "#0B2419", "#123A28"),
    "Paramount+": ("Paramount+", "#4D95FF", "#EEF5FF", "#DCEAFF"),
    "Peacock": ("peacock", "#FFFFFF", "#FFFDE8", "#FFF6C5"),
    "Paramount+ with Showtime": ("P+ SHOWTIME", "#4D95FF", "#EEF5FF", "#DCEAFF"),
    "YouTube Premium": ("YT Premium", "#FF3344", "#FFF2F2", "#FFE3E4"),
    "Google Play Movies & TV": ("Google Play", "#FFFFFF", "#F7FAFB", "#E7EEF1"),
    "The Roku Channel": ("Roku Channel", "#B28CFF", "#F7FAFB", "#E7EEF1"),
    "Criterion Channel": ("Criterion", "#FFFFFF", "#F7FAFB", "#E7EEF1"),
    "ARD Mediathek": ("ARD", "#68B9FF", "#F7FAFB", "#E7EEF1"),
    "Mediaset Infinity": ("Mediaset", "#FFFFFF", "#F7FAFB", "#E7EEF1"),
    "Movistar Plus+": ("Movistar+", "#4CC9FF", "#F7FAFB", "#E7EEF1"),
    "SBS On Demand": ("SBS", "#FF8A3D", "#F7FAFB", "#E7EEF1"),
    "WOWOW On Demand": ("WOWOW", "#5AA8FF", "#F7FAFB", "#E7EEF1"),
    "Now TV Hong Kong": ("Now TV", "#FF5AA5", "#F7FAFB", "#E7EEF1"),
    "STARZPLAY MENA": ("STARZPLAY", "#FFFFFF", "#F7FAFB", "#E7EEF1"),
}


def style_for(name: str) -> tuple[str, str, str, str]:
    return BRAND_STYLES.get(
        name,
        (name or "Streaming", "#FFFFFF", "#F7FAFB", "#E7EEF1"),
    )


def font_size(label: str) -> int:
    width_units = sum(1.0 if ord(char) > 127 else 0.62 for char in label)
    return max(16, min(72, int(280 / max(width_units, 1))))


def transparent_wordmark(name: str) -> str:
    label, accent, _, _ = style_for(name)
    safe = html.escape(label)
    size = font_size(label)
    width = 300
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="100" viewBox="0 0 {width} 100" role="img" aria-label="{html.escape(name)}">
  <text x="150" y="52" dominant-baseline="middle" text-anchor="middle"
    font-family="Arial,Helvetica,'Noto Sans SC',system-ui,sans-serif"
    font-size="{size}" font-weight="900" letter-spacing="-.5" fill="{accent}">{safe}</text>
</svg>'''


def transparent_image_badge(name: str, image_bytes: bytes, mime_type: str = "image/png") -> str:
    if mime_type == "image/svg+xml":
        source = image_bytes.decode("utf-8")
        source = re.sub(r"#000000|#000(?![0-9A-Fa-f])", "#FFFFFF", source, flags=re.IGNORECASE)
        source = re.sub(r"(?<=[:=\"'])black(?=[;\"'])", "#FFFFFF", source, flags=re.IGNORECASE)
        image_bytes = source.encode("utf-8")
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="300" height="100" viewBox="0 0 300 100" role="img" aria-label="{html.escape(name)}">
  <image x="0" y="0" width="300" height="100" preserveAspectRatio="xMidYMid meet"
    href="data:{mime_type};base64,{encoded}"/>
</svg>'''


def netflix_badge() -> str:
    """Official Simple Icons Netflix N path on a padded square canvas."""
    return '''<svg xmlns="http://www.w3.org/2000/svg" width="86" height="100" viewBox="0 0 32 32" role="img" aria-label="Netflix">
  <path transform="translate(4 4)" fill="#E50914" d="m5.398 0 8.348 23.602c2.346.059 4.856.398 4.856.398L10.113 0H5.398zm8.489 0v9.172l4.715 13.33V0h-4.715zM5.398 1.5V24c1.873-.225 2.81-.312 4.715-.398V14.83L5.398 1.5z"/>
</svg>'''


def itunes_badge() -> str:
    """Clean iTunes source wordmark with no Apple or Music icon."""
    return '''<svg xmlns="http://www.w3.org/2000/svg" width="226" height="100" viewBox="0 0 226 100" role="img" aria-label="iTunes">
  <text x="4" y="72" fill="#FFFFFF" stroke="#15171A" stroke-width="2.2" paint-order="stroke fill"
    font-family="Arial,Helvetica,sans-serif" font-size="67" font-weight="800" letter-spacing="-3">iTunes</text>
</svg>'''


def bahamut_anime_badge() -> str:
    """Official Bahamut Anime three-tile artwork, pre-rasterized to avoid font fallback."""
    encoded = "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Mzp15zse9lmevVCkyfSjf/7HF//4P/jLxfbZ88h5odXpYowhSSzj107z7Kf/gD/7P/8tpNm47hq+RZ9vtTetvf6Lv/ZY8czLn0hm86NlRpPrAhoi3ZZk66PY6nxwfyy2+nQfexuLyYzJcMjs0mWGL79ONp5SaCjLUZSgXpaZK2rS8jLLpq0cwFmj3cJ7Pa9GLrX6vd3p5Z3P9W874tJ269Tu2Qtfue1djyjGnJoNF9uP/ej365++747xX/gP/goOpb2+xl3vfIQiz9nd3eXOd7yNt/3Q996SNfwmQzq91b6e23h3+ErDcFFUj1ZhjXvItbS2hpDNYNjJC7c07riSSzoydegFRZ9+qqrda1TRWjoiA+BjuhUxJAHeWCStJojsqNNzva0Nsvniy7aZnu2uD85dfvX0Hx575AFt9nuvbb969tyDH/vO4p/9x//J+NjkblBoHQ2hewJkkzGXXnqZf/TcKbYevOcNX8O3CPat9qa1O7/tUX/xDx4fF/PcNdLUL4rs8nw6PzovcrPwjqwILpDcFWQ+GH5cLKvpSmxyKRWz52cMKscIquqbaUNJk6nLi9O99XUKdS+I56X+sa3dS6+f/vTWvXcUa0eOnD/z7MunHv6B7+De7/jg6Od/9D/KLzhH7+7bK5dQvliwe/os/87f/q+4611fe6z4WwT7VnvTWvvknbvj3/v8X2z0OycHJ28vXhtd6pz68tP/a7Ez6qr4SmOtmwMkIoeMEPDgMYg8SVK1aZLleXa6PRi4xWLx5cQkFzdvOza7fP787/WPHZlt3HX7zivPvPDMAx94rz7wPR8a/9wf/w9nL2zvcttjbweveOfwec58d8iFrzzDv/cv/6ev9RJdt71FsG+1N68tFh74oihfxCu7zeR4luenwL094NBMAMQLmMR6sWbqiuJ8Z20N5/zz6vX1wYnjxXh759P9Tm9n4/47pxeeP/Xkybe/rXjwe759+2/96J/NXv7K03zoR3+Y3tFNXOHwzpFNZ5x/4RR/8ZP/OIzj83uCFP7fX+uFOXh7y+j0Vvuatd/4uX/QvvjVF389zfKPYuSVPMu/unH7cRbT+e+Jta+tHT96/vxXn33i3ve9m7X3Pnz5Fz72k+NfPvNF/sKP/HkeeNc7GNxzgosvvMwdjzzEkfvu5sS3v/drPaU3vP3/ASyGcLZUyn8TAAAAIXRFWHRleGlmOkRhdGVUaW1lADIwMTY6MDE6MDYgMTQ6NTg6MzfNcHzIAAAAE3RFWHRleGlmOkV4aWZPZmZzZXQAMTE19D2NRQAAABh0RVh0ZXhpZjpQaXhlbFhEaW1lbnNpb24ANzkyfXPmugAAABh0RVh0ZXhpZjpQaXhlbFlEaW1lbnNpb24AMzg1YAoL8gAAACJ0RVh0ZXhpZjpTb2Z0d2FyZQBBQ0QgU3lzdGVtcyAuLi4uLi4uLi6OqGYAAAATdEVYdGV4aWY6U3ViU2VjVGltZQA4MTGqD1uuAAAAF3RFWHRleGlmOllDYkNyUG9zaXRpb25pbmcAMawPgGMAAAAASUVORK5CYII="
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="236" height="100" viewBox="0 0 236 100" role="img" aria-label="巴哈姆特動畫瘋">
  <image x="0" y="0" width="236" height="100" preserveAspectRatio="xMidYMid meet"
    href="data:image/png;base64,{encoded}"/>
</svg>'''


def line_tv_badge() -> str:
    """Official LINE TV green play symbol with a dark-UI-safe transparent wordmark."""
    return '''<svg xmlns="http://www.w3.org/2000/svg" width="280" height="100" viewBox="0 0 280 100" role="img" aria-label="LINE TV">
  <path transform="translate(8 14) scale(2.9)" fill="#06C755" d="M19.81 12a.94.94 0 0 0-.45-.8L1.46.15A1 1 0 0 0 1 0 1 1 0 0 0 0 .93v22.22a1 1 0 0 0 1 .93.9.9 0 0 0 .51-.15l17.9-11.09a.94.94 0 0 0 .4-.84ZM4.8 16.17V7.87L11.53 12 4.8 16.21Z"/>
  <text x="80" y="70" fill="#FFFFFF" stroke="#15171A" stroke-width="2" paint-order="stroke fill"
    font-family="Arial Black,Arial,Helvetica,sans-serif" font-size="56" font-weight="900" letter-spacing="-3">LINE TV</text>
</svg>'''


def transparent_white_logo(name: str, image_bytes: bytes, width: int, height: int) -> str:
    source = image_bytes.decode("utf-8")
    source = re.sub(r'fill="#[0-9A-Fa-f]{6}"', 'fill="#FFFFFF"', source)
    encoded = base64.b64encode(source.encode("utf-8")).decode("ascii")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(name)}">
  <image x="0" y="0" width="{width}" height="{height}" preserveAspectRatio="xMidYMid meet"
    href="data:image/svg+xml;base64,{encoded}"/>
</svg>'''


def fps_badge(rate: int) -> str:
    """Compact HFR lockup: the rate stays dominant at small player sizes."""
    width = 282 if rate == 120 else 220
    divider_x = 187 if rate == 120 else 125
    label_x = divider_x + 18
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="100" viewBox="0 0 {width} 100" role="img" aria-label="{rate} FPS">
  <path d="M6 16h29M6 16v20M6 84h29M6 84V64" fill="none" stroke="#45D9FF" stroke-width="6" stroke-linecap="round"/>
  <text x="25" y="78" fill="#FFFFFF" font-family="Arial Black,Arial,Helvetica,sans-serif" font-size="78" font-weight="900" letter-spacing="-5">{rate}</text>
  <path d="M{divider_x} 20v60" stroke="#45D9FF" stroke-width="3" stroke-linecap="round"/>
  <text x="{label_x}" y="45" fill="#45D9FF" font-family="Arial,Helvetica,sans-serif" font-size="26" font-weight="900" letter-spacing="2">HFR</text>
  <text x="{label_x}" y="75" fill="#FFFFFF" font-family="Arial,Helvetica,sans-serif" font-size="25" font-weight="800" letter-spacing="2">FPS</text>
</svg>'''


def flac_badge() -> str:
    """Transparent lossless wordmark using the familiar equalizer language."""
    return '''<svg xmlns="http://www.w3.org/2000/svg" width="278" height="100" viewBox="0 0 278 100" role="img" aria-label="FLAC lossless audio">
  <g fill="#45D9FF">
    <rect x="4" y="38" width="8" height="25" rx="4"/><rect x="18" y="23" width="8" height="55" rx="4"/>
    <rect x="32" y="10" width="8" height="80" rx="4"/><rect x="46" y="28" width="8" height="44" rx="4"/>
    <rect x="60" y="40" width="8" height="21" rx="4"/>
  </g>
  <text x="82" y="67" fill="#FFFFFF" font-family="Arial,Helvetica,sans-serif" font-size="64" font-weight="900" letter-spacing="-4">flac</text>
  <text x="85" y="88" fill="#AEB5BD" font-family="Arial,Helvetica,sans-serif" font-size="16" font-weight="800" letter-spacing="4">LOSSLESS</text>
</svg>'''


def hq_badge() -> str:
    return '''<svg xmlns="http://www.w3.org/2000/svg" width="154" height="100" viewBox="0 0 154 100" role="img" aria-label="HQ">
  <text x="2" y="78" fill="#F5C451" font-family="Arial Black,Arial,Helvetica,sans-serif" font-size="86" font-weight="900" letter-spacing="-7">HQ</text>
</svg>'''


def hdr_vivid_badge() -> str:
    return '''<svg xmlns="http://www.w3.org/2000/svg" width="292" height="100" viewBox="0 0 292 100" role="img" aria-label="HDR Vivid">
  <defs><linearGradient id="vivid" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#26D9FF"/><stop offset=".5" stop-color="#A65CFF"/><stop offset="1" stop-color="#FF4D7D"/></linearGradient></defs>
  <text x="0" y="72" fill="url(#vivid)" font-family="Arial Black,Arial,Helvetica,sans-serif" font-size="70" font-weight="900" letter-spacing="-5">HDR</text>
  <text x="151" y="68" fill="#FFFFFF" font-family="Arial,Helvetica,sans-serif" font-size="44" font-weight="900" letter-spacing="-2">VIVID</text>
</svg>'''


(TECHNICAL_DIR / "60-fps.svg").write_text(fps_badge(60), encoding="utf-8")
(TECHNICAL_DIR / "120-fps.svg").write_text(fps_badge(120), encoding="utf-8")
(TECHNICAL_DIR / "flac.svg").write_text(flac_badge(), encoding="utf-8")
(TECHNICAL_DIR / "hq.svg").write_text(hq_badge(), encoding="utf-8")
(TECHNICAL_DIR / "hdr-vivid.svg").write_text(hdr_vivid_badge(), encoding="utf-8")


for index, item in enumerate(streaming_filters):
    name = item.get("name", "")
    badge = None
    if name == "Netflix":
        badge = netflix_badge()
    elif name == "iTunes":
        badge = itunes_badge()
    elif name == "巴哈姆特動畫瘋":
        badge = bahamut_anime_badge()
    elif name == "LINE TV":
        badge = line_tv_badge()
    elif name == "Blu-ray Disc":
        bluray_cache = LOGO_CACHE / "bluray-blue.png"
        if not bluray_cache.exists():
            bluray_cache.write_bytes(fetch_bytes(QUALITY_LOGO_ROOT + "bluray-blue.png"))
        badge = transparent_image_badge(name, bluray_cache.read_bytes(), "image/png")
    transparent_logo = TRANSPARENT_SVG_LOGOS.get(name)
    if transparent_logo:
        logo_file, logo_url, width, height = transparent_logo
        cache_path = LOGO_CACHE / logo_file
        try:
            if not cache_path.exists():
                cache_path.write_bytes(fetch_bytes(logo_url))
            badge = transparent_white_logo(name, cache_path.read_bytes(), width, height)
        except Exception as exc:
            print(f"[transparent vector logo fallback] {name}: {exc}")
    vector_logo = SVG_LOGOS.get(name)
    if vector_logo:
        logo_file, logo_url = vector_logo
        cache_path = LOGO_CACHE / logo_file
        try:
            if not cache_path.exists():
                cache_path.write_bytes(fetch_bytes(logo_url))
            badge = transparent_image_badge(name, cache_path.read_bytes(), "image/svg+xml")
        except Exception as exc:
            print(f"[vector logo fallback] {name}: {exc}")
    logo_file = PNG_LOGOS.get(name)
    if logo_file:
        cache_path = LOGO_CACHE / logo_file
        try:
            if not cache_path.exists():
                cache_path.write_bytes(fetch_bytes(LOGO_ROOT + logo_file))
            if name not in {"Netflix", "iTunes"}:
                badge = transparent_image_badge(name, cache_path.read_bytes(), "image/png")
        except Exception as exc:
            print(f"[logo fallback] {name}: {exc}")
    if badge is None:
        badge = transparent_wordmark(name)
    (STREAMING_DIR / f"stream-{index:03d}.svg").write_text(badge, encoding="utf-8")


provider_module = r'''"use strict";

const rules = require("../data/streaming-rules.json");

function normalizeStudioName(value) {
  return String(value || "")
    .normalize("NFKC")
    .toLowerCase()
    .replace(/[™®©]/g, "")
    .replace(/&/g, "and")
    .replace(/[^a-z0-9\u4e00-\u9fff+]+/g, "")
    .trim();
}

const studioProviderAliases = {
  "爱奇艺": [
    "爱奇艺", "爱奇藝", "iQIYI", "iQIYI Studios", "iQIYI Pictures",
    "iQIYI Animation", "iQIYI International", "北京爱奇艺科技有限公司",
  ],
  "腾讯视频": [
    "腾讯视频", "騰訊視頻", "Tencent Video", "Tencent Video Original",
    "企鹅影视", "企鵝影視", "Tencent Penguin Pictures",
  ],
  "WeTV": ["WeTV", "Tencent WeTV", "腾讯视频国际版"],
  "优酷": ["优酷", "優酷", "Youku", "Youku Original", "优酷信息技术北京有限公司"],
  "芒果TV": [
    "芒果TV", "Mango TV", "MangoTV", "芒果超媒", "湖南快乐阳光互动娱乐传媒有限公司",
  ],
  "哔哩哔哩": [
    "哔哩哔哩", "嗶哩嗶哩", "Bilibili", "Bilibili Productions", "Bilibili Pictures",
    "上海宽娱数码科技有限公司",
  ],
  "Bstation": ["Bstation", "Bilibili International", "Bilibili SEA"],
  "AcFun": ["AcFun", "A站", "AcFun弹幕视频网"],
  "华数TV": ["华数TV", "華數TV", "Wasu TV", "华数传媒"],
  "百视TV": ["百视TV", "百視TV", "BesTV", "百视通"],
  "埋堆堆": ["埋堆堆", "TVB埋堆堆", "MaiDuiDui"],
  "SOHU VIDEO": ["搜狐视频", "搜狐視頻", "Sohu Video"],
  "MIGU VIDEO": ["咪咕视频", "咪咕視訊", "Migu Video", "MIGU VIDEO"],
  "PPTV": ["PP视频", "PPTV", "PPTV聚力", "PP Video", "PPLive"],
  "XIGUA VIDEO": ["西瓜视频", "西瓜視頻", "Xigua Video"],
  "DOUYIN": ["抖音", "Douyin", "抖音影视"],
  "M1905": ["1905电影网", "1905.com", "M1905"],
  "巴哈姆特動畫瘋": [
    "巴哈姆特動畫瘋", "巴哈姆特动画疯", "動畫瘋", "动画疯",
    "Bahamut Anime", "Bahamut Anime Crazy", "ani.gamer.com.tw",
    "巴哈姆特電玩資訊站", "巴哈姆特电玩资讯站", "ONEUP NETWORK CORPORATION",
  ],
  "LINE TV": [
    "LINE TV", "LINETV", "LINE TV Taiwan", "LINE TV Thailand", "LINE TV Original",
  ],

  "Netflix": [
    "Netflix", "Netflix Studios", "Netflix Animation", "Netflix International",
    "Netflix Original", "Netflix Worldwide Entertainment",
  ],
  "Amazon Prime Video": [
    "Prime Video", "Amazon Prime Video", "Amazon Studios", "Amazon MGM Studios",
    "Amazon Video", "Amazon Content Services",
  ],
  "HBO Max": ["HBO Max", "Max", "HBO", "HBO Entertainment", "Max Originals"],
  "Disney+": ["Disney+", "Disney Plus", "Disney+ Original"],
  "Hulu": ["Hulu", "Hulu Originals", "Hulu Original Programming"],
  "Apple TV+": [
    "Apple TV+", "Apple TV Plus", "Apple Studios", "Apple Original Films",
    "Apple Original Productions", "Apple TV+ Original",
  ],
  "Paramount+": ["Paramount+", "Paramount Plus", "Paramount+ Originals"],
  "Peacock": ["Peacock", "Peacock TV", "Peacock Originals"],
  "Discovery+": ["Discovery+", "Discovery Plus", "Discovery+ Originals"],
  "Crunchyroll": [
    "Crunchyroll", "Crunchyroll Studios", "Crunchyroll LLC", "Crunchyroll Anime",
    "Crunchyroll Originals", "Ellation",
  ],
  "Funimation": ["Funimation", "Funimation Entertainment", "Funimation Productions"],
  "HIDIVE": ["HIDIVE", "Sentai Filmworks", "Sentai Studios"],
  "YouTube Premium": ["YouTube Premium", "YouTube Originals", "YouTube Red"],
  "BBC iPlayer": ["BBC iPlayer", "BBC Television", "BBC Studios"],
  "JioHotstar": ["JioHotstar", "Disney+ Hotstar", "Hotstar"],
  "TVING": ["TVING", "Tving Original"],
  "Wavve": ["Wavve", "Wavve Original"],
  "Coupang Play": ["Coupang Play", "Coupang Play Original"],
  "U-NEXT": ["U-NEXT", "U Next"],
  "ABEMA": ["ABEMA", "AbemaTV"],
  "Hulu Japan": ["Hulu Japan", "HJ Holdings"],
  "Viki": ["Rakuten Viki", "Viki"],
  "Viu": ["Viu", "Viu Original"],
  "myTV SUPER": ["myTV SUPER", "TVB New Media"],
  "Now TV Hong Kong": ["Now TV Hong Kong", "Now TV"],
  "friDay影音": ["friDay影音", "friDay Video"],
  "KKTV": ["KKTV", "KKTV Original"],
  "Hami Video": ["Hami Video", "HamiVideo"],
};

const ruleByName = new Map(rules.map((rule) => [rule.name, rule]));
const ruleByStudio = new Map();
for (const [provider, aliases] of Object.entries(studioProviderAliases)) {
  const rule = ruleByName.get(provider);
  if (!rule) continue;
  for (const alias of [provider, ...aliases]) {
    ruleByStudio.set(normalizeStudioName(alias), rule);
  }
}

const compiledRules = rules
  .filter((rule) => rule.marker)
  .map((rule) => {
    try {
      const source = String(rule.pattern || "").replace(/^\(\?i\)/, "");
      return [rule, new RegExp(source, rule.caseSensitive ? "" : "i")];
    } catch (_error) {
      return [rule, null];
    }
  });

function studioName(studio) {
  if (typeof studio === "string") return studio;
  return studio && (studio.Name || studio.name || studio.Studio || studio.studio) || "";
}

function detectProviderFromFilename(filename) {
  const value = String(filename || "");
  for (const [rule, regex] of compiledRules) {
    if (regex && regex.test(value)) return rule;
  }
  return null;
}

function detectProviderFromStudio(studios) {
  if (!Array.isArray(studios)) return null;
  for (const studio of studios) {
    const rawName = studioName(studio);
    const rule = ruleByStudio.get(normalizeStudioName(rawName));
    if (rule) return { rule, studio: rawName };
  }
  return null;
}

function providerToHiddenMarker(provider) {
  const rule = typeof provider === "string" ? ruleByName.get(provider) : provider;
  return rule && rule.marker || "";
}

function resolveStreamingProvider(filename, itemStudios = [], seriesStudios = []) {
  const filenameRule = detectProviderFromFilename(filename);
  if (filenameRule) {
    return { provider: filenameRule.name, source: "filename", rule: filenameRule, studio: null };
  }
  const itemMatch = detectProviderFromStudio(itemStudios);
  if (itemMatch) {
    return { provider: itemMatch.rule.name, source: "item-studio", rule: itemMatch.rule, studio: itemMatch.studio };
  }
  const seriesMatch = detectProviderFromStudio(seriesStudios);
  if (seriesMatch) {
    return { provider: seriesMatch.rule.name, source: "series-studio", rule: seriesMatch.rule, studio: seriesMatch.studio };
  }
  return { provider: null, source: null, rule: null, studio: null };
}

function makeBadgeFilename(filename, resolution) {
  const rawFilename = String(filename || "");
  if (!resolution || resolution.source === "filename") return rawFilename;
  const marker = providerToHiddenMarker(resolution.rule);
  if (!marker || rawFilename.includes(marker)) return rawFilename;
  return `${rawFilename} ${marker}`;
}

function debugResolution(context, resolution, badgeFilename) {
  if (process.env.STREAM_PROVIDER_DEBUG !== "1") return;
  const filenameMatch = detectProviderFromFilename(context.filename);
  const itemStudioMatch = detectProviderFromStudio(context.itemStudios || []);
  const seriesStudioMatch = detectProviderFromStudio(context.seriesStudios || []);
  const safe = {
    itemId: context.item && context.item.Id,
    itemType: context.item && context.item.Type,
    itemName: context.item && context.item.Name,
    itemStudios: (context.itemStudios || []).map(studioName),
    seriesId: context.seriesId || null,
    seriesStudios: (context.seriesStudios || []).map(studioName),
    filename: context.filename,
    filenameProvider: filenameMatch && filenameMatch.name || null,
    itemStudioProvider: itemStudioMatch && itemStudioMatch.rule.name || null,
    seriesStudioProvider: seriesStudioMatch && seriesStudioMatch.rule.name || null,
    finalProvider: resolution.provider,
    providerSource: resolution.source,
    resolvedStudio: resolution.studio,
    injectedMarker: badgeFilename !== String(context.filename || ""),
  };
  console.log("[stream-provider]", JSON.stringify(safe));
}

function resolveBadgeFilename(filename, itemStudios = [], seriesStudios = [], context = {}) {
  const resolution = resolveStreamingProvider(filename, itemStudios, seriesStudios);
  const rawFilename = String(filename || "");
  const badgeFilename = makeBadgeFilename(rawFilename, resolution);
  debugResolution(
    { ...context, filename: rawFilename, itemStudios, seriesStudios },
    resolution,
    badgeFilename,
  );
  return { rawFilename, badgeFilename, ...resolution };
}

module.exports = {
  studioProviderAliases,
  normalizeStudioName,
  detectProviderFromFilename,
  detectProviderFromStudio,
  providerToHiddenMarker,
  resolveStreamingProvider,
  resolveBadgeFilename,
};
'''
(ROOT / "lib" / "streamingProvider.js").write_text(provider_module, encoding="utf-8")


common = ROOT / "lib" / "commonClient.js"
replace_once(
    common,
    'const DEFAULT_FIELDS = "ProviderIds,Name,MediaSources,Path,Id,IndexNumber,ParentIndexNumber";',
    'const DEFAULT_FIELDS = "ProviderIds,Name,Studios,SeriesId,MediaSources,Path,Id,IndexNumber,ParentIndexNumber";',
    "common Studios fields",
)


def patch_media_client(path: Path, label: str) -> None:
    replace_once(
        path,
        'const common = require("./commonClient");',
        'const common = require("./commonClient");\nconst streamingProvider = require("./streamingProvider");',
        f"{label} provider helper",
    )
    replace_once(
        path,
        'Fields: "ProviderIds,Name,Id", // Only need these fields for series lookup',
        'Fields: "ProviderIds,Name,Studios,Id", // Include Studios for platform fallback',
        f"{label} series Studios",
    )
    replace_once(
        path,
        'async function getPlaybackStreams(item, seriesName = null, config) {',
        'async function getPlaybackStreams(item, seriesName = null, config, seriesStudios = [], seriesId = null) {',
        f"{label} playback Studios arguments",
    )
    replace_once(
        path,
        'const mediaInfo = common.safeExtractMediaInfo(source, videoStream, audioStream);',
        '''const mediaInfo = common.safeExtractMediaInfo(source, videoStream, audioStream);
            const providerResolution = streamingProvider.resolveBadgeFilename(
                mediaInfo.filename,
                item.Studios || [],
                seriesStudios || [],
                { item, seriesId }
            );
            mediaInfo.rawFilename = providerResolution.rawFilename;
            mediaInfo.filename = providerResolution.badgeFilename;
            mediaInfo.streamingProvider = providerResolution.provider;
            mediaInfo.streamingProviderSource = providerResolution.source;''',
        f"{label} apply Studio fallback",
    )
    replace_once(
        path,
        'const streams = await getPlaybackStreams(episode, series.Name, config);',
        'const streams = await getPlaybackStreams(episode, series.Name, config, series.Studios || [], series.Id);',
        f"{label} episode series fallback",
    )
    replace_once(
        path,
        'const streams = await getPlaybackStreams(singleItem, parentSeriesName, config);',
        'const streams = await getPlaybackStreams(singleItem, parentSeriesName, config, [], null);',
        f"{label} movie fallback",
    )


patch_media_client(ROOT / "lib" / "embyClient.js", "Emby")
patch_media_client(ROOT / "lib" / "jellyfinClient.js", "Jellyfin")

index_js = ROOT / "index.js"
replace_once(
    index_js,
    '// const jellyfinClient = require("./lib/jellyfinClient");',
    'const jellyfinClient = require("./lib/jellyfinClient");',
    "Jellyfin import",
)
replace_once(
    index_js,
    'const { version } = require("./package.json");',
    'const { version } = require("./package.json");\nconst badgeBase = require("./data/badges-base.json");',
    "badge rule import",
)
replace_once(
    index_js,
    'const client = embyClient;',
    "const client = cfg.serverType === 'jellyfin' ? jellyfinClient : embyClient;",
    "Emby/Jellyfin client selection",
)

badge_route = r'''
app.get("/badges.json", (req, res) => {
  const proto = String(req.headers["x-forwarded-proto"] || req.protocol || "https").split(",")[0].trim();
  const host = String(req.headers["x-forwarded-host"] || req.get("host") || "").split(",")[0].trim();
  const origin = `${proto}://${host}`;
  let streamIndex = 0;
  const technicalAssets = {
    FLAC: "flac.svg",
  };
  const assetUrl = (folder, asset) => `${origin}/badges/${folder}/${asset}?v=3.0.8`;
  const baseFilters = badgeBase.filters.map((filter) => {
    if (filter.groupId === "gs") {
      const asset = `stream-${String(streamIndex++).padStart(3, "0")}.svg`;
      return { ...filter, imageURL: assetUrl("streaming-fixed", asset) };
    }
    const technicalAsset = technicalAssets[filter.name];
    if (technicalAsset) {
      return { ...filter, imageURL: assetUrl("technical-fixed", technicalAsset) };
    }
    if (filter.name === "HDR (新导入)") {
      return { ...filter, pattern: "(?i)\\bhdr\\b(?![ ._-]*vivid)" };
    }
    return filter;
  });
  const customFilters = [
    {
      type: "filter",
      id: "fps-120",
      name: "120 FPS",
      pattern: "(?i)(?<![0-9])(?:119\\.88|120(?:\\.0+)?)[ ._-]*(?:fps|hz)(?![A-Za-z0-9])",
      tagColor: "#00000000",
      borderColor: "#00000000",
      textColor: "#FFFFFF",
      tagStyle: "filled",
      imageURL: assetUrl("technical-fixed", "120-fps.svg"),
      isEnabled: true,
      groupId: "gfr",
    },
    {
      type: "filter",
      id: "quality-hq",
      name: "HQ High Quality",
      pattern: "(?i)(?<![A-Za-z0-9])hq(?![A-Za-z0-9])",
      tagColor: "#00000000",
      borderColor: "#00000000",
      textColor: "#FFFFFF",
      tagStyle: "filled",
      imageURL: assetUrl("technical-fixed", "hq.svg"),
      isEnabled: true,
      groupId: "gst",
    },
    {
      type: "filter",
      id: "video-hdr-vivid",
      name: "HDR Vivid",
      pattern: "(?i)(?<![A-Za-z0-9])hdr[ ._-]*vivid(?![A-Za-z0-9])",
      tagColor: "#00000000",
      borderColor: "#00000000",
      textColor: "#FFFFFF",
      tagStyle: "filled",
      imageURL: assetUrl("technical-fixed", "hdr-vivid.svg"),
      isEnabled: true,
      groupId: "video-tech",
    },
    {
      type: "filter",
      id: "fps-60",
      name: "60 FPS",
      pattern: "(?i)(?<![0-9])(?:59\\.94|60(?:\\.0+)?)[ ._-]*(?:fps|hz)(?![A-Za-z0-9])",
      tagColor: "#00000000",
      borderColor: "#00000000",
      textColor: "#FFFFFF",
      tagStyle: "filled",
      imageURL: assetUrl("technical-fixed", "60-fps.svg"),
      isEnabled: true,
      groupId: "gfr",
    },
  ];
  const frameRateGroup = {
    id: "gfr",
    name: "Frame Rate",
    color: "#A9E7FF",
    borderColor: "#00000000",
    isExpanded: true,
  };
  const payload = {
    ...badgeBase,
    groups: [
      ...badgeBase.groups.slice(0, 2),
      frameRateGroup,
      ...badgeBase.groups.slice(2),
    ],
    filters: [...baseFilters, ...customFilters],
  };
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Cache-Control", "public, s-maxage=300, stale-while-revalidate=86400");
  res.json(payload);
});

'''
replace_once(index_js, "app.use(cors());\n", "app.use(cors());\n" + badge_route, "badge route")

index_text = index_js.read_text(encoding="utf-8")
listen_re = re.compile(
    r'app\.listen\(PORT,\s*\(\)\s*=>\s*\n\s*console\.log\(`🚀  StreamBridge up at http://localhost:\$\{PORT\}/<cfg>/manifest\.json`\)\s*\n\);'
)
replacement = '''if (require.main === module) {
  app.listen(PORT, () =>
    console.log(`🚀  StreamBridge up at http://localhost:${PORT}/<cfg>/manifest.json`)
  );
}
module.exports = app;'''
index_text, count = listen_re.subn(replacement, index_text, count=1)
if count != 1:
    raise RuntimeError("Vercel export patch anchor not found")
index_js.write_text(index_text, encoding="utf-8")

print(
    f"v3 build complete: {len(streaming_filters)} streaming rules, "
    f"{sum(bool(rule['marker']) for rule in rules)} hidden markers"
)
