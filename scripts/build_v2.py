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
LOGO_CACHE = DATA / "logo-cache"
BASE_JSON = DATA / "badges-base.json"
BASE_JSON_GZ = DATA / "badges-base.json.gz"
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


if not BASE_JSON.exists() and BASE_JSON_GZ.exists():
    BASE_JSON.write_bytes(gzip.decompress(BASE_JSON_GZ.read_bytes()))

if not BASE_JSON.exists():
    raise RuntimeError(
        "data/badges-base.json.gz is required; it is the pinned rule snapshot and must be committed"
    )

restore_upstream()

base = json.loads(BASE_JSON.read_text(encoding="utf-8"))
if len(base.get("filters", [])) != 245:
    raise RuntimeError("Unexpected base filter count")

streaming_filters = [f for f in base["filters"] if f.get("groupId") == "gs"]
if len(streaming_filters) != 144:
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


# All other services receive a high-contrast brand card instead of the old
# unreadable generic white card.
BRAND_STYLES = {
    "爱奇艺": ("iQIYI", "#00BE06", "#E9FFE9", "#D5F9DA"),
    "腾讯视频": ("Tencent Video", "#00A8E8", "#EAFBFF", "#D8F4FF"),
    "WeTV": ("WeTV", "#00C878", "#EBFFF6", "#D7F8E9"),
    "优酷": ("YOUKU", "#FF5C35", "#FFF4F0", "#EAF8FF"),
    "芒果TV": ("芒果TV", "#FF6A00", "#FFF5E9", "#FFE8C8"),
    "哔哩哔哩": ("bilibili", "#00A1D6", "#ECFAFF", "#DDF5FF"),
    "Bstation": ("Bstation", "#00A1D6", "#ECFAFF", "#DDF5FF"),
    "AcFun": ("AcFun", "#FD4C5D", "#FFF0F2", "#FFE0E4"),
    "华数TV": ("华数TV", "#E60012", "#FFF1F2", "#FFE1E4"),
    "百视TV": ("百视TV", "#7656FF", "#F4F0FF", "#E8E0FF"),
    "埋堆堆": ("埋堆堆", "#FF4057", "#FFF0F3", "#FFE0E6"),
    "SOHU VIDEO": ("搜狐视频", "#E7252C", "#FFF0F0", "#FFE0E1"),
    "MIGU VIDEO": ("咪咕视频", "#E6007E", "#FFF0F8", "#FFE0F1"),
    "PPTV": ("PP视频", "#2878FF", "#EEF5FF", "#DDEBFF"),
    "XIGUA VIDEO": ("西瓜视频", "#FF4A3D", "#FFF1EF", "#FFE1DE"),
    "DOUYIN": ("抖音", "#111111", "#F6F6F6", "#E8E8E8"),
    "M1905": ("1905电影网", "#B79245", "#FFF9ED", "#F7EBCF"),
    "Crunchyroll": ("Crunchyroll", "#F47521", "#FFF4EA", "#FFE5D0"),
    "Apple TV+": ("tv+", "#FFFFFF", "#101010", "#292929"),
    "Apple TV": ("tv", "#FFFFFF", "#101010", "#292929"),
    "iTunes": ("tv", "#FFFFFF", "#101010", "#292929"),
    "Netflix": ("NETFLIX", "#E50914", "#FFF2F2", "#FFE3E4"),
    "Amazon Prime Video": ("prime video", "#FFFFFF", "#102A43", "#184D70"),
    "HBO Max": ("HBO max", "#5B2DFF", "#F3EFFF", "#E6DFFF"),
    "Disney+": ("Disney+", "#113CCF", "#F1F4FF", "#DFE7FF"),
    "Hulu": ("hulu", "#1CE783", "#0B2419", "#123A28"),
    "Paramount+": ("Paramount+", "#0064FF", "#EEF5FF", "#DCEAFF"),
    "Peacock": ("peacock", "#111111", "#FFFDE8", "#FFF6C5"),
}


def style_for(name: str) -> tuple[str, str, str, str]:
    return BRAND_STYLES.get(
        name,
        (name or "Streaming", "#16212A", "#F7FAFB", "#E7EEF1"),
    )


def font_size(label: str) -> int:
    width_units = sum(1.65 if ord(char) > 127 else 1 for char in label)
    if width_units <= 12:
        return 39
    if width_units <= 18:
        return 32
    if width_units <= 25:
        return 26
    return 21


def card_shell(name: str, content: str) -> str:
    _, accent, bg_start, bg_end = style_for(name)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="320" height="112" viewBox="0 0 320 112" role="img" aria-label="{html.escape(name)}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{bg_start}"/>
      <stop offset="1" stop-color="{bg_end}"/>
    </linearGradient>
  </defs>
  <rect x="1" y="1" width="318" height="110" rx="27" fill="url(#bg)" stroke="{accent}" stroke-opacity=".22" stroke-width="2"/>
  {content}
</svg>'''


def wordmark_card(name: str) -> str:
    label, accent, _, _ = style_for(name)
    safe = html.escape(label)
    size = font_size(label)
    content = f'''<text x="160" y="58" dominant-baseline="middle" text-anchor="middle"
    font-family="Arial,Helvetica,'Noto Sans SC',sans-serif"
    font-size="{size}" font-weight="800" letter-spacing="-.5" fill="{accent}">{safe}</text>'''
    return card_shell(name, content)


def image_card(name: str, image_bytes: bytes, mime_type: str = "image/png") -> str:
    encoded = base64.b64encode(image_bytes).decode("ascii")
    content = f'''<image x="30" y="20" width="260" height="72" preserveAspectRatio="xMidYMid meet"
    href="data:{mime_type};base64,{encoded}"/>'''
    return card_shell(name, content)


for index, item in enumerate(streaming_filters):
    name = item.get("name", "")
    card = None
    vector_logo = SVG_LOGOS.get(name)
    if vector_logo:
        logo_file, logo_url = vector_logo
        cache_path = LOGO_CACHE / logo_file
        try:
            if not cache_path.exists():
                cache_path.write_bytes(fetch_bytes(logo_url))
            card = image_card(name, cache_path.read_bytes(), "image/svg+xml")
        except Exception as exc:
            print(f"[vector logo fallback] {name}: {exc}")
    logo_file = PNG_LOGOS.get(name)
    if logo_file:
        cache_path = LOGO_CACHE / logo_file
        try:
            if not cache_path.exists():
                cache_path.write_bytes(fetch_bytes(LOGO_ROOT + logo_file))
            card = image_card(name, cache_path.read_bytes(), "image/png")
        except Exception as exc:
            print(f"[logo fallback] {name}: {exc}")
    if card is None:
        card = wordmark_card(name)
    (STREAMING_DIR / f"stream-{index:03d}.svg").write_text(card, encoding="utf-8")


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
      return [rule, new RegExp(source, "i")];
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
  const payload = {
    ...badgeBase,
    filters: badgeBase.filters.map((filter) => {
      if (filter.groupId !== "gs") return filter;
      const asset = `stream-${String(streamIndex++).padStart(3, "0")}.svg`;
      return { ...filter, imageURL: `${origin}/badges/streaming-fixed/${asset}` };
    }),
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
