#!/usr/bin/env python3
import base64
import html
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PUBLIC = ROOT / "public"
STREAMING_DIR = PUBLIC / "badges" / "streaming-fixed"
BASE_JSON = DATA / "badges-base.json"
RULES_JSON = DATA / "streaming-rules.json"
BADGE_SOURCE = "https://streambridge-studio-markers.vercel.app/badges.json"

DATA.mkdir(parents=True, exist_ok=True)
STREAMING_DIR.mkdir(parents=True, exist_ok=True)

def fetch_bytes(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "streambridge-studio-markers-v2/2.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()

if not BASE_JSON.exists():
    BASE_JSON.write_bytes(fetch_bytes(BADGE_SOURCE))

base = json.loads(BASE_JSON.read_text(encoding="utf-8"))
if len(base.get("filters", [])) != 245:
    raise RuntimeError("Unexpected base filter count")
streaming_filters = [f for f in base["filters"] if f.get("groupId") == "gs"]
if len(streaming_filters) != 144:
    raise RuntimeError("Unexpected streaming filter count")

marker_re = re.compile(r"\u2063[\u200b\u200c]+\u2064")
rules = []
for f in streaming_filters:
    pattern = f.get("pattern", "")
    marker_match = marker_re.search(pattern)
    rules.append({
        "name": f.get("name", ""),
        "pattern": pattern,
        "marker": marker_match.group(0) if marker_match else "",
    })
RULES_JSON.write_text(json.dumps(rules, ensure_ascii=False, indent=2), encoding="utf-8")

KNOWN_LOGOS = {
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

def text_card(name):
    safe = html.escape(name or "Streaming")
    size = 30 if len(safe) <= 18 else 24 if len(safe) <= 28 else 18
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="320" height="112" viewBox="0 0 320 112">
  <rect x="1" y="1" width="318" height="110" rx="26" fill="#E7EBEC" stroke="#D9DFE1" stroke-width="2"/>
  <text x="160" y="58" dominant-baseline="middle" text-anchor="middle" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif" font-size="{size}" font-weight="700" fill="#111111">{safe}</text>
</svg>'''

def image_card(image_bytes):
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="320" height="112" viewBox="0 0 320 112">
  <rect x="1" y="1" width="318" height="110" rx="26" fill="#E7EBEC" stroke="#D9DFE1" stroke-width="2"/>
  <image x="28" y="20" width="264" height="72" preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,{encoded}"/>
</svg>'''

for index, f in enumerate(streaming_filters):
    name = f.get("name", "")
    card = None
    logo_file = KNOWN_LOGOS.get(name)
    if logo_file:
        try:
            card = image_card(fetch_bytes(LOGO_ROOT + logo_file))
        except Exception as exc:
            print(f"[logo] {name}: {exc}")
    if card is None:
        card = text_card(name)
    (STREAMING_DIR / f"stream-{index:03d}.svg").write_text(card, encoding="utf-8")

studio_provider = r'''const rules = require("../data/streaming-rules.json");

function normalize(value) {
  return String(value || "")
    .normalize("NFKC")
    .toLowerCase()
    .replace(/[™®©]/g, "")
    .replace(/\b(inc|llc|ltd|limited|studios?)\b/g, "")
    .replace(/[^a-z0-9\u4e00-\u9fff+]+/g, "")
    .trim();
}

const aliases = new Map([
  ["amazonprime", "Amazon Prime Video"],
  ["amazonprimevideo", "Amazon Prime Video"],
  ["primevideo", "Amazon Prime Video"],
  ["amazonvideo", "Amazon Prime Video"],
  ["max", "HBO Max"],
  ["hbomax", "HBO Max"],
  ["disneyplus", "Disney+"],
  ["disney+", "Disney+"],
  ["appletvplus", "Apple TV+"],
  ["appletv+", "Apple TV+"],
  ["appletv", "Apple TV+"],
  ["paramountplus", "Paramount+"],
  ["paramount+", "Paramount+"],
  ["peacocktv", "Peacock"],
]);

const byName = new Map();
for (const rule of rules) byName.set(normalize(rule.name), rule);
for (const [alias, target] of aliases) {
  const rule = rules.find((candidate) => candidate.name === target);
  if (rule) byName.set(normalize(alias), rule);
}

const compiled = rules.map((rule) => {
  try {
    const source = String(rule.pattern || "").replace(/^\(\?i\)/, "");
    return [rule, new RegExp(source, "i")];
  } catch (_error) {
    return [rule, null];
  }
});

function hasStreamingProvider(filename) {
  const value = String(filename || "");
  return compiled.some(([, regex]) => regex && regex.test(value));
}

function resolveStudioRule(studios) {
  if (!Array.isArray(studios)) return null;
  for (const studio of studios) {
    const name = typeof studio === "string" ? studio : studio && studio.Name;
    const key = normalize(name);
    if (key && byName.has(key)) return byName.get(key);
  }
  return null;
}

function applyStudioFallback(filename, studios) {
  const value = String(filename || "");
  if (!value || hasStreamingProvider(value)) return value;
  const rule = resolveStudioRule(studios);
  if (!rule || !rule.marker) return value;
  return `${value} ${rule.marker}`;
}

module.exports = { applyStudioFallback, hasStreamingProvider, resolveStudioRule };
'''
(ROOT / "lib" / "studioProvider.js").write_text(studio_provider, encoding="utf-8")

def replace_once(path, old, new, label):
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"{label}: patch anchor not found in {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")

common = ROOT / "lib" / "commonClient.js"
replace_once(
    common,
    'const DEFAULT_FIELDS = "ProviderIds,Name,MediaSources,Path,Id,IndexNumber,ParentIndexNumber";',
    'const DEFAULT_FIELDS = "ProviderIds,Name,Studios,MediaSources,Path,Id,IndexNumber,ParentIndexNumber";',
    "common Studios fields",
)

emby = ROOT / "lib" / "embyClient.js"
replace_once(
    emby,
    'const common = require("./commonClient");',
    'const common = require("./commonClient");\nconst studioProvider = require("./studioProvider");',
    "Emby Studio helper",
)
replace_once(
    emby,
    'Fields: "ProviderIds,Name,Id", // Only need these fields for series lookup',
    'Fields: "ProviderIds,Name,Studios,Id", // Include Studios for platform fallback',
    "series Studios fields",
)
replace_once(
    emby,
    'async function getPlaybackStreams(item, seriesName = null, config) {',
    'async function getPlaybackStreams(item, seriesName = null, config, fallbackStudios = []) {',
    "playback Studios argument",
)
replace_once(
    emby,
    'const mediaInfo = common.safeExtractMediaInfo(source, videoStream, audioStream);',
    'const mediaInfo = common.safeExtractMediaInfo(source, videoStream, audioStream);\n            mediaInfo.filename = studioProvider.applyStudioFallback(mediaInfo.filename, fallbackStudios.length ? fallbackStudios : (item.Studios || []));',
    "apply Studio fallback",
)
replace_once(
    emby,
    'const streams = await getPlaybackStreams(episode, series.Name, config);',
    'const streams = await getPlaybackStreams(episode, series.Name, config, series.Studios || episode.Studios || []);',
    "episode Studios fallback",
)
replace_once(
    emby,
    'const streams = await getPlaybackStreams(singleItem, parentSeriesName, config);',
    'const streams = await getPlaybackStreams(singleItem, parentSeriesName, config, singleItem.Studios || []);',
    "movie Studios fallback",
)

index_js = ROOT / "index.js"
index_text = index_js.read_text(encoding="utf-8")
if 'const badgeBase = require("./data/badges-base.json");' not in index_text:
    index_text = index_text.replace(
        'const { version } = require("./package.json");',
        'const { version } = require("./package.json");\nconst badgeBase = require("./data/badges-base.json");',
        1,
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
if 'app.get("/badges.json"' not in index_text:
    index_text = index_text.replace('app.use(cors());\n', 'app.use(cors());\n' + badge_route, 1)

if "module.exports = app;" not in index_text:
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
print(f"v2 build complete: {len(streaming_filters)} streaming rules")
