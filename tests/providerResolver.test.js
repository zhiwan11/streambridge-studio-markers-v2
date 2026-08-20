"use strict";

const assert = require("node:assert/strict");
const provider = require("../lib/streamingProvider");

function resolve(filename, itemStudios = [], seriesStudios = []) {
  return provider.resolveBadgeFilename(filename, itemStudios, seriesStudios);
}

const appleFilename = resolve(
  "2160p.AppleTV.WEB-DL.DV.H.265.DDP.5.1.Atmos-HiveWeb",
  [],
  [{ Name: "Apple TV+" }],
);
assert.equal(appleFilename.provider, "Apple TV");
assert.equal(appleFilename.source, "filename");
assert.equal(appleFilename.badgeFilename, appleFilename.rawFilename);

const appleSeries = resolve(
  "2160p.WEB-DL.DV.H.265.DDP.5.1.Atmos-HiveWeb",
  [],
  [{ Name: "Apple TV+" }],
);
assert.equal(appleSeries.provider, "Apple TV+");
assert.equal(appleSeries.source, "series-studio");
assert.notEqual(appleSeries.badgeFilename, appleSeries.rawFilename);

const netflixConflict = resolve(
  "2160p.NF.WEB-DL.DV.H.265.DDP.5.1.Atmos-CHDWEB",
  [],
  [{ Name: "Apple TV+" }],
);
assert.equal(netflixConflict.provider, "Netflix");
assert.equal(netflixConflict.source, "filename");
assert.equal(netflixConflict.badgeFilename, netflixConflict.rawFilename);

const netflixStudio = resolve(
  "2160p.WEB-DL.HDR10.H.265.DDP.5.1.Atmos-CHDWEB",
  [{ Name: "Netflix" }],
);
assert.equal(netflixStudio.provider, "Netflix");
assert.equal(netflixStudio.source, "item-studio");

const amazonStudio = resolve(
  "2160p.WEB-DL.H.265.DDP.5.1.Atmos",
  [{ Name: "Amazon Studios" }],
);
assert.equal(amazonStudio.provider, "Amazon Prime Video");

const unknownStudio = resolve(
  "2160p.WEB-DL.H.265.DDP.5.1",
  [{ Name: "普通影视制作公司" }],
);
assert.equal(unknownStudio.provider, null);
assert.equal(unknownStudio.badgeFilename, unknownStudio.rawFilename);

const iqiyiItem = resolve(
  "The.Mad.Monk.Reincarnation.WEB-DL.HDR.H.265.DDP5.1",
  [{ Name: "iQIYI" }],
);
assert.equal(iqiyiItem.provider, "爱奇艺");
assert.equal(iqiyiItem.source, "item-studio");

const iqiyiSeries = resolve(
  "The.Mad.Monk.Reincarnation.WEB-DL.HDR.H.265.DDP5.1-HHWEB",
  [],
  [{ Name: "iQIYI" }],
);
assert.equal(iqiyiSeries.provider, "爱奇艺");
assert.equal(iqiyiSeries.source, "series-studio");

const crunchyroll = resolve(
  "WEB-DL.H.264.AAC-UBWEB",
  [],
  [{ Name: "Crunchyroll Studios" }],
);
assert.equal(crunchyroll.provider, "Crunchyroll");

const itemBeforeSeries = resolve(
  "2160p.WEB-DL.H.265.DDP5.1",
  [{ Name: "Netflix" }],
  [{ Name: "Apple TV+" }],
);
assert.equal(itemBeforeSeries.provider, "Netflix");
assert.equal(itemBeforeSeries.source, "item-studio");

const alreadyMarked = resolve(
  appleSeries.badgeFilename,
  [],
  [{ Name: "Apple TV+" }],
);
assert.equal(alreadyMarked.provider, "Apple TV+");
assert.equal(alreadyMarked.badgeFilename, appleSeries.badgeFilename);

console.log("providerResolver.test.js: 11 cases passed");
