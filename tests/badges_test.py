#!/usr/bin/env python3
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
base = json.loads((ROOT / "data" / "badges-base.json").read_text(encoding="utf-8"))
streaming = [item for item in base["filters"] if item.get("groupId") == "gs"]
assets = sorted((ROOT / "public" / "badges" / "streaming-fixed").glob("stream-*.svg"))
technical_dir = ROOT / "public" / "badges" / "technical-fixed"

assert len(base["filters"]) == 247
assert len(base["groups"]) == 15
assert len(streaming) == 146
assert len(assets) == 146

for asset in assets:
    text = asset.read_text(encoding="utf-8")
    assert text.startswith("<svg")
    assert 'href="http' not in text
    assert "/badges-v2/" not in text
    assert 'id="bg"' not in text
    assert 'width="318" height="110"' not in text

by_name = {item["name"]: index for index, item in enumerate(streaming)}

def svg(name: str) -> str:
    index = by_name[name]
    return (ROOT / "public" / "badges" / "streaming-fixed" / f"stream-{index:03d}.svg").read_text(encoding="utf-8")


assert "data:image/svg+xml;base64," in svg("爱奇艺")
assert "<text" not in svg("爱奇艺")
assert "data:image/png;base64," in svg("Apple TV+")
assert "data:image/png;base64," in svg("Amazon Prime Video")
assert "data:image/png;base64," in svg("Crunchyroll")
assert 'aria-label="Netflix"' in svg("Netflix")
assert "#E50914" in svg("Netflix")
assert 'width="86"' in svg("Netflix")
assert 'm5.398 0 8.348 23.602' in svg("Netflix")
assert 'aria-label="iTunes"' in svg("iTunes")
assert "iTunes" in svg("iTunes")
assert "data:image" not in svg("iTunes")
assert "apple-only" not in svg("iTunes")
assert "linearGradient" not in svg("iTunes")
assert "data:image/svg+xml;base64," in svg("哔哩哔哩")
assert "<text" not in svg("哔哩哔哩")
bahamut_anime_svg = svg("巴哈姆特動畫瘋")
assert 'aria-label="巴哈姆特動畫瘋"' in bahamut_anime_svg
assert "Ani-One" not in bahamut_anime_svg
assert "data:image/png;base64," in bahamut_anime_svg
assert 'width="236"' in bahamut_anime_svg
line_tv_svg = svg("LINE TV")
assert 'aria-label="LINE TV"' in line_tv_svg
assert ">LINE TV</text>" in line_tv_svg
assert "#06C755" in line_tv_svg
assert "data:image" not in line_tv_svg
bluray_svg = svg("Blu-ray Disc")
assert 'width="300"' in bluray_svg
assert 'height="100"' in bluray_svg
assert "data:image/png;base64," in bluray_svg
assert "<text" not in bluray_svg

ultra_bluray_svg = svg("Ultra HD Blu-ray")
assert "data:image/svg+xml;base64," in ultra_bluray_svg
encoded = ultra_bluray_svg.split("base64,", 1)[1].split('"', 1)[0]
embedded = __import__("base64").b64decode(encoded).decode("utf-8")
assert 'fill="#FFFFFF"' in embedded
assert "#0095D5" not in embedded
assert "#0096D6" not in embedded
assert 'width="290"' in svg("Ultra HD Blu-ray")
assert 'height="100"' in svg("Ultra HD Blu-ray")

for technical_asset in ("60-fps.svg", "120-fps.svg", "flac.svg", "hq.svg", "hdr-vivid.svg"):
    technical_svg = (technical_dir / technical_asset).read_text(encoding="utf-8")
    assert technical_svg.startswith("<svg")
    if technical_asset != "hq.svg":
        assert "#FFFFFF" in technical_svg
    assert 'href="http://' not in technical_svg
    assert 'href="https://' not in technical_svg

assert 'aria-label="60 FPS"' in (technical_dir / "60-fps.svg").read_text(encoding="utf-8")
assert 'aria-label="120 FPS"' in (technical_dir / "120-fps.svg").read_text(encoding="utf-8")
assert "FLAC" in (technical_dir / "flac.svg").read_text(encoding="utf-8")
hq_svg = (technical_dir / "hq.svg").read_text(encoding="utf-8")
assert ">HQ</text>" in hq_svg
assert "QUALITY" not in hq_svg
assert "HIGH" not in hq_svg
assert "<path" not in hq_svg
assert "VIVID" in (technical_dir / "hdr-vivid.svg").read_text(encoding="utf-8")

print("badges_test.py: 146 provider/disc + 5 technical badges passed")
