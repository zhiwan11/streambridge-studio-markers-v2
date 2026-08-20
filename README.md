# StreamBridge Studio Markers v2

Patched StreamBridge build for BetterFormatter streaming-platform badges.

## Fixes

- Fixes broken Netflix / Apple TV / Hulu / Prime Video / HBO Max / Disney+ / Paramount+ / Peacock / Crunchyroll artwork by generating self-contained badge cards at build time. The SVG no longer references a removed `/badges-v2/*` asset.
- Keeps the original 245 filters, 15 groups and 144 Source / Streaming rules.
- Adds Emby `Studios` fallback without asking the user for another Emby API key.
- Priority is always: `filename provider > Emby Studio provider > no provider`.

If a filename already contains `NF`, `AppleTV`, etc., the filename wins. If it contains no known platform, StreamBridge checks the already-fetched Emby item/series `Studios` and appends the matching invisible marker before BetterFormatter sees the media filename.

Important: a Studio fallback can only identify a platform when Emby's `Studios` metadata itself contains a recognizable platform name such as `Apple TV+`, `Netflix`, `Hulu`, `Prime Video`, etc. A production-company-only value such as `Tropper Ink Productions` cannot by itself prove the streaming service.

## Deployment

Vercel runs `scripts/build_v2.py` during the install step. The script pulls the clean upstream `h4harsimran/streambridge`, preserves the current badge rule pack, patches the Emby data path, generates the streaming artwork and exports the Express app for Vercel.

After deployment, import:

`https://<your-v2-vercel-domain>/badges.json`
