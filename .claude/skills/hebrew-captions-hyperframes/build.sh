#!/usr/bin/env bash
# build.sh - compile the caption layers for a Hebrew embedded-captions project.
#
#   HE_FONT=... LAT_FONT=... bash build.sh     # compile + Hebrew/RTL patch
#
# Runs the Hebrew/RTL pass BETWEEN make-theme.cjs and the render (render-theme.sh
# chains them directly, which throws the patch away). Also re-installs the
# project's DNA into the skill on every run - skills/embedded-captions/themes/
# is a managed mirror the hyperframes CLI wipes on update.
set -euo pipefail
cd "$(dirname "$0")"
SKILL="${EMBEDDED_CAPTIONS_SKILL:-$HOME/.claude/skills/embedded-captions}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cp "$HERE/inkhand.json" "$SKILL/themes/inkhand.json"
node "$SKILL/scripts/make-theme.cjs" .
node "$HERE/patch-he.cjs" .
# The compiler emits a plate-reaction pass that still applies `noise=alls=5` even
# with plate.grain:0 in the DNA - film grain over the whole a-roll. Captions
# only, footage untouched: drop it. Deliverable is final.mp4.
rm -f _postfx.sh
echo "[build] ok - index.html (bg) + rail.html (fg) ready; preview or render next"
