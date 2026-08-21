# StreamBridge Studio Markers v3

StreamBridge build for BetterFormatter streaming-platform badges.

## Provider resolution

The resolver uses the existing Emby/Jellyfin connection and applies this strict priority:

1. explicit provider in the media-source filename;
2. current movie/episode `Studios`;
3. parent series `Studios`;
4. no provider badge.

No additional Emby, Jellyfin, TMDB, API-key, server, or token setting is required.
The original filename is retained as `rawFilename`. An invisible provider marker is
added only to `behaviorHints.filename`, which is the value BetterFormatter matches.

Examples:

- `NF` in the filename wins over a series Studio of `Apple TV+`.
- a provider-free filename with `Studios: [{ "Name": "iQIYI" }]` receives the
  existing iQIYI hidden marker and displays the iQIYI badge.
- an episode with no Studios falls back to its series Studios.

## Artwork

The build creates 144 self-contained `320x112` SVG badges. Major platforms use
embedded coloured wordmarks; every remaining provider receives a high-contrast
brand card. No SVG references the removed `/badges-v2/*` assets or a nested
remote image.

Domestic vector sources: [iQIYI](https://commons.wikimedia.org/wiki/File:IQIYI_logo_(2022).svg),
[Bilibili](https://commons.wikimedia.org/wiki/File:Bilibili_2023.svg),
[Youku](https://commons.wikimedia.org/wiki/File:Youku_logo_(2).svg),
[WeTV](https://commons.wikimedia.org/wiki/File:WeTV_logo.svg), and
[AcFun](https://commons.wikimedia.org/wiki/File:AcFun.svg). The AcFun artwork is
credited to Beijing Danmu Network Technology Co., Ltd. under CC BY 2.5; the
other listed wordmarks are public-domain text/geometric logos on Commons.

The v3.0.5 configuration self-hosts transparent, high-contrast technical marks
for `60 FPS`, `120 FPS`, `FLAC`, `HQ`, and `HDR Vivid`. The frame-rate rules recognize both
integer and common fractional rates (`59.94` and `119.88`) without matching
ordinary numbers elsewhere in the source name.

All 144 source/provider assets use transparent canvases with enlarged brand
artwork. The build rejects the former rounded card background, provides an
Apple + iTunes movie/TV lockup, and keeps artwork readable in light and dark UI.

## Build and test

```bash
npm test
```

The build restores the small pinned upstream StreamBridge source, applies the
Emby and Jellyfin patches, generates the provider rule table, creates the badge
assets, and runs resolver and artwork checks.

Production badge URL:

`https://streambridge-studio-markers.vercel.app/badges.json`

Set `STREAM_PROVIDER_DEBUG=1` only while diagnosing metadata. Debug records show
item IDs, item/series Studios, filename, final provider, and marker status; they
never log server URLs, API keys, tokens, or credentials.
