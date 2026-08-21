"use strict";

const app = require("../index");

function compile(pattern) {
  return new RegExp(String(pattern).replace(/^\(\?i\)/, ""), "i");
}

function compileFilter(filter) {
  const source = String(filter.pattern).replace(/^\(\?i\)/, "");
  return new RegExp(source, filter.caseSensitive ? "" : "i");
}

const server = app.listen(0, async () => {
  try {
    const port = server.address().port;
    const response = await fetch(`http://127.0.0.1:${port}/badges.json`);
    const payload = await response.json();
    if (payload.filters.length !== 251) throw new Error("expected 251 filters");
    if (payload.groups.length !== 16) throw new Error("expected 16 groups");

    const byName = new Map(payload.filters.map((filter) => [filter.name, filter]));
    for (const name of ["60 FPS", "120 FPS", "HQ High Quality", "HDR Vivid", "FLAC"]) {
      const filter = byName.get(name);
      if (!filter) throw new Error(`missing ${name}`);
      if (!filter.imageURL.includes("?v=3.0.7")) throw new Error(`stale asset version: ${name}`);
    }

    const aniOne = byName.get("Ani-One");
    const lineTv = byName.get("LINE TV");
    if (!aniOne || !lineTv) throw new Error("missing Ani-One or LINE TV");
    if (!aniOne.imageURL.includes("?v=3.0.7") || !lineTv.imageURL.includes("?v=3.0.7")) {
      throw new Error("stale Ani-One or LINE TV asset version");
    }
    if (!compileFilter(aniOne).test("ANi")) throw new Error("ANi token must match Ani-One");
    if (compileFilter(aniOne).test("Anime") || compileFilter(aniOne).test("Animation") || compileFilter(aniOne).test("ani")) {
      throw new Error("Ani-One short token is too broad");
    }
    if (!compileFilter(lineTv).test("Flaming.Dodgeball-DL.AVC.AAC-LINETV@UBWEB")) {
      throw new Error("LINETV token must match LINE TV");
    }

    const cases = [
      ["Movie.2160p.60fps.HQ.HDRVivid.FLAC", ["60 FPS", "HQ High Quality", "HDR Vivid", "FLAC"]],
      ["Movie.2160p.119.88Hz.HDR-Vivid", ["120 FPS", "HDR Vivid"]],
      ["Movie.1960.WEB-DL.HQMUX.HDR10", []],
    ];
    for (const [value, expected] of cases) {
      const hits = ["60 FPS", "120 FPS", "HQ High Quality", "HDR Vivid", "FLAC"]
        .filter((name) => compile(byName.get(name).pattern).test(value));
      if (JSON.stringify(hits) !== JSON.stringify(expected)) {
        throw new Error(`${value}: expected ${expected}, got ${hits}`);
      }
    }

    const genericHdr = byName.get("HDR (新导入)");
    if (compile(genericHdr.pattern).test("HDR.Vivid")) {
      throw new Error("generic HDR must not duplicate HDR Vivid");
    }
    console.log("configRules.test.js: provider, technical, and conflict rules passed");
  } finally {
    server.close();
  }
});
