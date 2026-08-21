#!/usr/bin/env python3
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
base = json.loads((ROOT / "data" / "badges-base.json").read_text(encoding="utf-8"))
streaming = [item for item in base["filters"] if item.get("groupId") == "gs"]
assets = sorted((ROOT / "public" / "badges" / "streaming-fixed").glob("stream-*.svg"))
technical_dir = ROOT / "public" / "badges" / "technical-fixed"

assert len(base["filters"]) == 245
assert len(base["groups"]) == 15
assert len(streaming) == 144
assert len(assets) == 144

for asset in assets:
    text = asset.read_text(encoding="utf-8")
    assert text.startswith("<svg")
    assert 'href="http' not in text
    assert "/badges-v2/" not in text

by_name = {item["name"]: index for index, item in enumerate(streaming)}

def svg(name: str) -> str:
    index = by_name[name]
    return (ROOT / "public" / "badges" / "streaming-fixed" / f"stream-{index:03d}.svg").read_text(encoding="utf-8")


assert "#00BE06" in svg("爱奇艺")
assert "data:image/svg+xml;base64," in svg("爱奇艺")
assert "<text" not in svg("爱奇艺")
assert "#101010" in svg("Apple TV+")
assert "#102A43" in svg("Amazon Prime Video")
assert "#F47521" in svg("Crunchyroll")
assert "#00A1D6" in svg("哔哩哔哩")
assert "data:image/svg+xml;base64," in svg("哔哩哔哩")
assert "<text" not in svg("哔哩哔哩")
for disc_name in ("Blu-ray Disc", "Ultra HD Blu-ray"):
    disc_svg = svg(disc_name)
    assert "data:image/svg+xml;base64," in disc_svg
    assert "<rect" not in disc_svg
    assert "<text" not in disc_svg
    encoded = disc_svg.split("base64,", 1)[1].split('"', 1)[0]
    embedded = __import__("base64").b64decode(encoded).decode("utf-8")
    assert 'fill="#FFFFFF"' in embedded
    assert "#0095D5" not in embedded
    assert "#0096D6" not in embedded

assert 'width="210"' in svg("Blu-ray Disc")
assert 'height="112"' in svg("Blu-ray Disc")
assert 'width="290"' in svg("Ultra HD Blu-ray")
assert 'height="100"' in svg("Ultra HD Blu-ray")

for technical_asset in ("60-fps.svg", "120-fps.svg", "flac.svg"):
    technical_svg = (technical_dir / technical_asset).read_text(encoding="utf-8")
    assert technical_svg.startswith("<svg")
    assert "#FFFFFF" in technical_svg
    assert 'href="http://' not in technical_svg
    assert 'href="https://' not in technical_svg
    assert "linearGradient" not in technical_svg

assert 'aria-label="60 FPS"' in (technical_dir / "60-fps.svg").read_text(encoding="utf-8")
assert 'aria-label="120 FPS"' in (technical_dir / "120-fps.svg").read_text(encoding="utf-8")
assert "FLAC" in (technical_dir / "flac.svg").read_text(encoding="utf-8")

print("badges_test.py: 144 provider/disc + 3 technical badges passed")
