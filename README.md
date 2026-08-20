# StreamBridge Studio Markers v2

Clean badge-hosting project for BetterFormatter / resource badge imports.

This repository is used for the repaired streaming-platform badge pack. It keeps the original matching rules while moving streaming artwork to stable self-hosted assets.

## Priority

`filename provider > Emby Studio provider > no provider`

The static badge pack handles matching and artwork. Emby `Studios` fallback must be injected by the player / formatter layer that already has access to the current Emby item or series metadata.
