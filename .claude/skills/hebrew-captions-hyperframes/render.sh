#!/usr/bin/env bash
# render.sh - render the caption layers and composite onto the footage -> final.mp4
# Run build.sh first. Not render-theme.sh: that re-runs make-theme.cjs (losing the
# Hebrew patch) and applies _postfx.sh (grain over the whole a-roll).
set -euo pipefail
cd "$(dirname "$0")"
SKILL="${EMBEDDED_CAPTIONS_SKILL:-$HOME/.claude/skills/embedded-captions}"
# fg = pure rail, nothing to occlude, skips a full matte re-encode of the a-roll.
export CAPTION_LAYER_FLAG="${CAPTION_LAYER_FLAG:-fg}"
bash "$SKILL/scripts/render-and-composite.sh" .
