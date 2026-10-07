---
name: hebrew-captions-hyperframes
description: Hebrew (RTL) captions on a talking-head video through HyperFrames' embedded-captions skill. The upstream skill is LTR/English-only - this adds the four fixes it needs for Hebrew (whisper in Hebrew, RTL word order, a Hebrew font paired with a Latin hand, no grain over the footage) plus a ready "inkhand" theme and build/render scripts. Use whenever the user wants Hebrew subtitles/captions burned into a vertical or horizontal video with HyperFrames. Triggers - Hebrew - "כתוביות בעברית", "כתוביות ל-HyperFrames", "כתוביות כתב יד", "תוסיף כתוביות לסרטון"; English - "Hebrew captions", "RTL captions hyperframes", "Hebrew subtitles embedded-captions". Requires the upstream `embedded-captions` skill (npx skills add heygen-com/hyperframes).
---

# Hebrew captions with HyperFrames (embedded-captions, fixed for RTL)

`embedded-captions` is excellent and completely LTR. Run it on a Hebrew clip as-is and the output is **silently wrong**, not broken: confident fabricated English transcript, lines that read backwards, a system sans instead of the font you chose, and film grain over footage you asked to leave untouched. This skill is the checklist and the scripts that fix all four, learned on a real 71-second vertical.

## Prerequisites

- The upstream pack: `npx skills add heygen-com/hyperframes` (gives `/embedded-captions`, `/hyperframes-cli` and friends).
- FFmpeg + Node 20+. `npx hyperframes doctor` must pass.
- A Hebrew font file. Handwriting: any `ot-hayim` face (free). Sans: Heebo / Assistant (Google Fonts, OFL).
- Optional Latin companion: `Caveat-Variable.ttf` from Google Fonts. Hebrew handwriting faces often carry **zero Latin glyphs**, so English words mid-sentence drop to Arial without it.

## The four fixes (in order)

1. **Transcription.** `hyperframes init --video` auto-runs whisper `small.en`. On Hebrew audio it produces confident fabricated English. Delete `transcript.json` and re-run:
   ```bash
   WHISPER_LANG=he WHISPER_MODEL=large-v3 npx hyperframes transcribe source.mp4
   ```
   Fix brand names **inside transcript.json**, not as caption substitutions - that keeps word timings exact and the compiler's verbatim gate happy.
2. **RTL.** The theme compiler emits every word as an inline span in spoken order. In an LTR container the first spoken word lands leftmost, so the line reads backwards. `patch-he.cjs` injects `direction:rtl; unicode-bidi:isolate` on `.rail` / `#stl-w` after every compile. Latin runs inside the Hebrew then place themselves correctly through normal bidi.
3. **Fonts.** No Hebrew face is bundled. `patch-he.cjs` inlines your Hebrew font (and the Latin companion) as base64 `@font-face`, and turns off synthesized bold - single-weight handwriting faces smear under browser bold.
4. **Untouched footage.** `_postfx.sh` applies `noise=alls=5` over the whole a-roll even with `plate.grain:0` in the DNA. `build.sh` deletes it. Deliver `final.mp4`.

## Workflow

```bash
# 1. scaffold from the footage (downscale 4K to 1080 first - matting is CPU-bound)
npx hyperframes init my-captions --video source.mp4
cd my-captions

# 2. Hebrew transcript (see fix 1), then review transcript.json by hand

# 3. copy this skill's files into the project
cp ~/.claude/skills/hebrew-captions-hyperframes/{build.sh,render.sh,patch-he.cjs,inkhand.json} .

# 4. compile + patch
HE_FONT=/path/OHRonShemer-Regular.woff2 LAT_FONT=/path/Caveat-Variable.ttf bash build.sh

# 5. look before rendering
npx hyperframes preview

# 6. render + composite -> final.mp4
bash render.sh
```

`inkhand.json` is a rail DNA tuned for 1080x1920 vertical + RTL: near-black handwriting just below center, a cream paper-glow halo instead of a background band, one climax word settling behind the subject. Edit `palette`, `fontPx`, `bottomPx` to taste. The `fonts` entries must match `HE_FAMILY` (default `HebrewHand`) or the face name you set.

## Hard limits

- The stroke-drawn setpieces (chalkboard, graffiti, brush, neonsign) **cannot write Hebrew** - their Hershey stroke fonts have 0 Hebrew glyphs. Hebrew handwriting must come from a real font.
- Matting is CPU-only: ~74 minutes for 71s @1080x1920/60fps, ~22GB of frame dumps. Use `CAPTION_LAYER_FLAG=fg` (pure rail) whenever the subject fills the frame - nothing to occlude, no matte pass.
- If the skill's scripts complain "set HYPERFRAMES_ROOT", they expect a built hyperframes checkout; point `HYPERFRAMES_ROOT` at a local clone with `packages/cli/dist/cli.js` built, or use the CLI commands directly.

## Managed-mirror warning

`~/.claude/skills/embedded-captions/themes/` is wiped on every `hyperframes skills update`. That is why `inkhand.json` lives in this skill and `build.sh` copies it in on every run. Keep your own DNA here, never only in the mirror.
