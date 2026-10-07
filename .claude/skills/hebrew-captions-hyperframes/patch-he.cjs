#!/usr/bin/env node
/*
 * patch-he.cjs - Hebrew/RTL post-pass over the layers embedded-captions generates.
 *
 *   HE_FONT=/path/to/hebrew.woff2 LAT_FONT=/path/to/latin.ttf node patch-he.cjs [project-dir]
 *
 * The embedded-captions theme engine is LTR-only and ships no Hebrew font, so
 * three things have to be added after every compile, before preview/render:
 *
 *   1. @font-face for a Hebrew face, inlined as base64 - the renderer only
 *      auto-supplies its own canonical families, so without this the captions
 *      silently fall back to a system font.
 *   2. direction:rtl on the caption containers. Words are emitted as inline
 *      spans in spoken order; in an LTR container the FIRST spoken word lands
 *      leftmost, i.e. the line reads backwards. rtl restores spoken order.
 *   3. Ink-on-bright fixes the DNA can't express: the hero's hardcoded dark
 *      text-shadow becomes a paper-glow halo, and synthesized faux-bold is off
 *      (handwriting faces usually ship Regular only; browser bold smears them).
 *
 * Idempotent - re-running replaces the injected block.
 */
const fs = require("fs");
const path = require("path");

const PROJECT = path.resolve(process.argv[2] || ".");
const HE = process.env.HE_FONT;
const LAT = process.env.LAT_FONT;
if (!HE || !fs.existsSync(HE)) {
  console.error("[patch-he] set HE_FONT to a Hebrew .woff2/.ttf (e.g. an ot-hayim face)");
  process.exit(2);
}
// Many Hebrew handwriting faces carry Hebrew letters + digits and ZERO Latin
// letters, so "Seedance" / "AI" would fall through to a generic sans. Pair a
// character-matched Latin hand (Caveat from Google Fonts works well).
const HAS_LAT = LAT && fs.existsSync(LAT);
const HE_FAMILY = process.env.HE_FAMILY || "HebrewHand";
const MARKER = "he-rtl-patch";
const GLOW =
  "0 0 18px rgba(255,252,244,0.95), 0 0 7px rgba(255,252,244,0.98), 0 1px 2px rgba(255,252,244,0.9)";

const fmt = (p) => (p.endsWith(".woff2") ? ["font/woff2", "woff2"] : p.endsWith(".woff") ? ["font/woff", "woff"] : ["font/ttf", "truetype"]);
const face = (family, p, extra = "") => {
  const [mime, f] = fmt(p);
  const b64 = fs.readFileSync(p).toString("base64");
  return `@font-face { font-family:'${family}'; font-style:normal; font-weight:400;
  src:url(data:${mime};base64,${b64}) format('${f}'); ${extra} font-display:block; }`;
};

const BLOCK = `<style id="${MARKER}">
${face(HE_FAMILY, HE)}
${HAS_LAT ? face("LatinHand", LAT, "font-variation-settings:'wght' 650; size-adjust:132%;") : ""}
/* Latin runs fall through to the matched hand, not the system sans */
.rail, .rail .w, #stl-w { font-family:'${HE_FAMILY}'${HAS_LAT ? ",'LatinHand'" : ""},sans-serif !important; }
/* spoken order == visual order: the spans are emitted in transcript order */
.rail, #stl, #stl-w { direction: rtl; unicode-bidi: isolate; }
/* one weight - never let the browser synthesize a bold */
.rail .w, .rail .w.em, #stl-w { font-weight: 400 !important; }
.rail .w { margin: 0 0.12em !important; }
/* dark ink needs a light halo, not the engine's dark drop shadow */
#stl-w { text-shadow: ${GLOW} !important; }
</style>`;

let patched = 0;
for (const f of ["index.html", "rail.html"]) {
  const p = path.join(PROJECT, f);
  if (!fs.existsSync(p)) continue;
  let html = fs.readFileSync(p, "utf8");
  html = html.replace(new RegExp(`<style id="${MARKER}">[\\s\\S]*?</style>\\n?`), "");
  if (!html.includes("</head>")) {
    console.error(`[patch-he] ${f}: no </head> - cannot inject`);
    process.exit(2);
  }
  fs.writeFileSync(p, html.replace("</head>", BLOCK + "\n</head>"));
  patched++;
  console.log(`[patch-he] ${f}: font + rtl + ink-glow injected`);
}
if (!patched) {
  console.error("[patch-he] nothing to patch - run make-theme.cjs first");
  process.exit(2);
}
