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

DATA.mkdir(parents=True, exist_ok=True)
STREAMING_DIR.mkdir(parents=True, exist_ok=True)

if not BASE_JSON.exists():
    raise SystemExit("data/badges-base.json is missing")

base = json.loads(BASE_JSON.read_text(encoding="utf-8"))
streaming_filters = [f for f in base.get("filters", []) if f.get("groupId") == "gs"]

marker_re = re.compile(r"\u2063[\u200b\u200c]+\u2064")
rules = []
for f in streaming_filters:
    pattern = f.get("pattern", "")
    m = marker_re.search(pattern)
    rules.append({
        "name": f.get("name", ""),
        "pattern": pattern,
        "marker": m.group(0) if m else "",
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

def fetch_bytes(url):
    req = urllib.request.Request(url, headers={"User-Agent": "streambridge-studio-markers-v2/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()

def text_card(name):
    safe = html.escape(name or "Streaming")
    size = 30 if len(safe) <= 18 else 24 if len(safe) <= 28 else 18
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="320" height="112" viewBox="0 0 320 112">
  <rect x="1" y="1" width="318" height="110" rx="26" fill="#E7EBEC" stroke="#D9DFE1" stroke-width="2"/>
  <text x="160" y="58" dominant-baseline="middle" text-anchor="middle" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif" font-size="{size}" font-weight="700" fill="#111111">{safe}</text>
</svg>'''

def logo_card(png):
    encoded = base64.b64encode(png).decode("ascii")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="320" height="112" viewBox="0 0 320 112">
  <rect x="1" y="1" width="318" height="110" rx="26" fill="#E7EBEC" stroke="#D9DFE1" stroke-width="2"/>
  <image x="28" y="20" width="264" height="72" preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,{encoded}"/>
</svg>'''

for idx, f in enumerate(streaming_filters):
    name = f.get("name", "")
    svg = None
    filename = KNOWN_LOGOS.get(name)
    if filename:
        try:
            svg = logo_card(fetch_bytes(LOGO_ROOT + filename))
        except Exception as exc:
            print(f"[badge] logo download failed for {name}: {exc}")
    if svg is None:
        svg = text_card(name)
    (STREAMING_DIR / f"stream-{idx:03d}.svg").write_text(svg, encoding="utf-8")

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
for (const rule of rules) {
  byName.set(normalize(rule.name), rule);
}
for (const [alias, targetName] of aliases) {
  const target = rules.find((rule) => rule.name === targetName);
  if (target) byName.set(normalize(alias), target);
}

const compiled = rules.map((rule) => {
  try {
    const source = String(rule.pattern || "").replace(/^\(\?i\)/, "");
    return [rule, new RegExp(source, "i")];
  } catch {
    return [rule, null];
  }
});

function hasStreamingProvider(filename) {
  const value = String(filename || "");
  return compiled.some(([, regex]) => regex && regex.test(value));
}

function studioNames(studios) {
  if (!Array.isArray(studios)) return [];
  return studios
    .map((studio) => typeof studio === "string" ? studio : studio && studio.Name)
    .filter(Boolean);
}

function resolveStudioRule(studios) {
  for (const studio of studioNames(studios)) {
    const normalized = normalize(studio);
    if (!normalized) continue;
    if (byName.has(normalized)) return byName.get(normalized);
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

module.exports = {
  applyStudioFallback,
  hasStreamingProvider,
  resolveStudioRule,
};
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
    "common fields",
)

emby = ROOT / "lib" / "embyClient.js"
replace_once(
    emby,
    'const { CommonMediaClient, normalizeMediaSources } = require("./commonClient");',
    'const { CommonMediaClient, normalizeMediaSources } = require("./commonClient");\nconst studioProvider = require("./studioProvider");',
    "emby require",
)
replace_once(
    emby,
    'Fields: "ProviderIds,Name,Id",',
    'Fields: "ProviderIds,Name,Studios,Id",',
    "emby series fields",
)
replace_once(
    emby,
    'async function getPlaybackStreams(item, seriesName = null, config) {',
    'async function getPlaybackStreams(item, seriesName = null, config, fallbackStudios = []) {',
    "emby playback signature",
)
replace_once(
    emby,
    'const medInf = MediaClient.safeExtractMediaInfo(src, playbackData.MediaSources);',
    'const medInf = MediaClient.safeExtractMediaInfo(src, playbackData.MediaSources);\n      medInf.filename = studioProvider.applyStudioFallback(medInf.filename, fallbackStudios.length ? fallbackStudios : (item.Studios || []));',
    "emby media info",
)
replace_once(
    emby,
    'return await getPlaybackStreams(singleItem, parentSeriesName, config);',
    'return await getPlaybackStreams(singleItem, parentSeriesName, config, singleItem.Studios || []);',
    "emby movie studios",
)
replace_once(
    emby,
    'return await getPlaybackStreams(episode, series.Name, config);',
    'return await getPlaybackStreams(episode, series.Name, config, series.Studios || episode.Studios || []);',
    "emby episode studios",
)

jelly = ROOT / "lib" / "jellyfinClient.js"
replace_once(
    jelly,
    'const { CommonMediaClient, normalizeMediaSources } = require("./commonClient");',
    'const { CommonMediaClient, normalizeMediaSources } = require("./commonClient");\nconst studioProvider = require("./studioProvider");',
    "jelly require",
)
replace_once(
    jelly,
    'Fields: "ProviderIds,Name,Id",',
    'Fields: "ProviderIds,Name,Studios,Id",',
    "jelly series fields",
)
replace_once(
    jelly,
    'async function getPlaybackStreams(itemId, seriesName = null, config) {',
    'async function getPlaybackStreams(itemId, seriesName = null, config, fallbackStudios = []) {',
    "jelly playback signature",
)

jelly_text = jelly.read_text(encoding="utf-8")
anchor = 'const mediaInfo = MediaClient.safeExtractMediaInfo(source, mediaSources);'
if anchor in jelly_text and 'studioProvider.applyStudioFallback(mediaInfo.filename' not in jelly_text:
    jelly_text = jelly_text.replace(
        anchor,
        anchor + '\n      mediaInfo.filename = studioProvider.applyStudioFallback(mediaInfo.filename, fallbackStudios);',
        1,
    )
    jelly.write_text(jelly_text, encoding="utf-8")

replace_once(
    jelly,
    'return await getPlaybackStreams(singleItem.Id, parentSeriesName, config);',
    'return await getPlaybackStreams(singleItem.Id, parentSeriesName, config, singleItem.Studios || []);',
    "jelly movie studios",
)
replace_once(
    jelly,
    'return await getPlaybackStreams(episode.Id, series.Name, config);',
    'return await getPlaybackStreams(episode.Id, series.Name, config, series.Studios || episode.Studios || []);',
    "jelly episode studios",
)

index = ROOT / "index.js"
index_text = index.read_text(encoding="utf-8")
if 'const badgeBase = require("./data/badges-base.json");' not in index_text:
    index_text = index_text.replace(
        'const { version } = require("./package.json");',
        'const { version } = require("./package.json");\nconst badgeBase = require("./data/badges-base.json");',
        1,
    )

route = r'''
app.get("/badges.json", (req, res) => {
  const forwardedProto = String(req.headers["x-forwarded-proto"] || req.protocol || "https").split(",")[0].trim();
  const forwardedHost = String(req.headers["x-forwarded-host"] || req.get("host") || "").split(",")[0].trim();
  const origin = `${forwardedProto}://${forwardedHost}`;
  let streamIndex = 0;

  const payload = {
    ...badgeBase,
    filters: badgeBase.filters.map((filter) => {
      if (filter.groupId !== "gs") return filter;
      const asset = `stream-${String(streamIndex++).padStart(3, "0")}.svg`;
      return {
        ...filter,
        imageURL: `${origin}/badges/streaming-fixed/${asset}`,
      };
    }),
  };

  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Cache-Control", "public, s-maxage=300, stale-while-revalidate=86400");
  res.json(payload);
});

'''
if 'app.get("/badges.json"' not in index_text:
    index_text = index_text.replace('app.use(cors());\n', 'app.use(cors());\n' + route, 1)
index.write_text(index_text, encoding="utf-8")

print(f"Prepared {len(streaming_filters)} streaming badges and {len(rules)} Studio-marker rules.")
