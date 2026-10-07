---
name: caption-from-video
description: Generate Hebrew (or any language) captions from an MP4/MOV/MP3 file and burn them in with full styling control — font, size, background style, animation type, words-per-chunk, position. Returns SRT + optional captioned video. Triggers - "כתוביות", "captions", "תמלל סרטון", "caption this", "burn subtitles", "תמלול לעברית", or any time the user provides a video file and wants captions.
---

# Caption From Video

Generate styled, burnt-in captions for any video file. Built for Hebrew first, works for any language whisper supports.

## When to use

- User provides a video/audio file path and asks for captions, subtitles, or transcription
- User wants captions in a specific style (font, size, animation, position, background)
- User wants to add captions to a sliders/montage/talking-head video
- Hebrew RTL captions specifically — handles direction, fonts, alignment correctly

## Input

The user provides ONE of:
1. A path to an `.mp4`, `.mov`, `.mp3`, `.wav`, or `.m4a` file
2. A folder of multiple media files for batch processing

Plus OPTIONAL style preferences (defaults shown):
- `language`: `he` (Hebrew) | `en` | `ar` | `auto`
- `model`: `large-v3` (best, slower) | `medium` | `small` | `ivrit-ai/whisper-large-v3-turbo` (Hebrew-optimized)
- `font_name`: `Arial` (default — supports Hebrew on Mac)
- `font_size`: `18` (small/elegant) | `24` (standard) | `32` (large/bold) — default 18
- `background`: `none` (text only with outline) | `box` (semi-transparent box, default) | `solid` (opaque) | `gradient`
- `position`: `bottom` (default) | `top` | `center` | `top-right` | `bottom-left`
- `animation`: `none` | `fade` (default 250ms in/out) | `pop` | `word-highlight` (per-word color shift, requires alignment)
- `words_per_chunk`: `5` (default) — max words per caption shown at once
- `chunk_duration_min`: `0.5s` — minimum on-screen time per chunk
- `chunk_duration_max`: `4s` — maximum on-screen time per chunk
- `text_color`: `#FFFFFF` (default white)
- `outline_color`: `#000000` (default black)
- `bg_color_alpha`: `0xC0` (default 75% opaque)

## Output

By default returns:
1. `<basename>.srt` — caption file (segment-level)
2. `<basename>.ass` — Advanced SubStation Alpha (with styling baked in)
3. `<basename>_captioned.mp4` — original video with burnt-in captions (optional, only if user requests)

If `word-highlight` animation is requested, also produces:
4. `<basename>.words.json` — word-level timestamps from whisperx alignment

## How to run

### Step 1 — Setup check
Required:
- Python 3.9+
- `pip install whisperx==3.7.5` (already includes torch, faster-whisper, pyannote)
- ffmpeg in PATH (or use bundled imageio_ffmpeg)

PyTorch 2.6+ requires this monkey-patch (pyannote checkpoints aren't pure weights):
```python
import torch
_orig = torch.load
def _patched(*a, **kw):
    kw['weights_only'] = False
    return _orig(*a, **kw)
torch.load = _patched
```

If `ffmpeg` not in PATH, symlink imageio's bundled binary:
```bash
FF_DIR="$(python3 -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())' | xargs dirname)"
ln -sf "$FF_DIR/ffmpeg-macos-aarch64-v7.1" "$FF_DIR/ffmpeg"
export PATH="$FF_DIR:$PATH"
```

### Step 2 — Transcribe
```python
import whisperx
device = "cpu"  # or "cuda" if GPU
model = whisperx.load_model(model_name, device, compute_type="int8", language=lang)
audio = whisperx.load_audio(video_path)
result = model.transcribe(audio, batch_size=4)
```

### Step 3 — (Optional) Word-level alignment
For `word-highlight` animation, run alignment to get per-word timestamps:
```python
align_model, metadata = whisperx.load_align_model(
    language_code="he",  # or other
    device=device,
    model_name="imvladikon/wav2vec2-xls-r-300m-hebrew"  # for Hebrew
)
result = whisperx.align(result["segments"], align_model, metadata, audio, device)
# Now result["segments"][i]["words"] has [{"word": ..., "start": ..., "end": ...}, ...]
```

If Hebrew alignment fails or is slow, fall back to chunked segment-level captions (still good UX).

### Step 4 — Split into chunks
```python
import re
def split_chunks(text, max_words=5):
    parts = re.split(r'(?<=[.!?])\s+|\.\.\.\s*', text)
    chunks = []
    for p in parts:
        # also break long parts on commas
        sub = re.split(r',\s+', p) if len(p.split()) > max_words*2 else [p]
        for sp in sub:
            words = sp.strip().rstrip('.,!?').split()
            if not words: continue
            for i in range(0, len(words), max_words):
                chunks.append(' '.join(words[i:i+max_words]))
    return chunks
```
Distribute time per chunk by character count (longer chunks get more time).

### Step 5 — Generate ASS file with style
ASS format gives best control. Key style fields:
```
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginV, ...
Style: Default,{font_name},{font_size},&H00FFFFFF,&H00000000,&H{bg_alpha}000000,1,{border_style},1.5,0.5,2,30,...
```

`BorderStyle`: 1 = outline only (no box), 3 = opaque box (background color used)
`Alignment`: ASS uses numpad layout — 2=bottom-center, 5=middle-center, 8=top-center, 6=middle-right
`PrimaryColour`/`BackColour`: BGR hex prefixed `&H00`/`&HAA` (alpha + BGR), e.g. white = `&H00FFFFFF`

For per-line fade animation: prefix the dialogue text with `{\fad(250,250)}` (fade-in 250ms, fade-out 250ms).

For per-word highlighting (requires word timestamps):
```
Dialogue: 0,{start},{end},Default,,0,0,0,,{\k20}word1 {\k15}word2 {\k30}word3
```
`\k` = karaoke duration in centiseconds. Combine with secondary color for highlight effect.

### Step 6 — Burn with ffmpeg
```bash
ffmpeg -i input.mp4 -vf "ass=output.ass" -c:v libx264 -preset fast -crf 20 -c:a copy output_captioned.mp4
```

Important: escape the path for the ass filter if it contains special chars:
```python
safe = ass_path.replace("'", r"\'").replace(":", r"\:").replace(",", r"\,")
```

## Style presets (suggest these to user)

| Preset | Best for | Settings |
|--------|---------|----------|
| **Subtle** | Documentary, family video | font=18, bg=box (75%), fade 250ms, words_per_chunk=5 |
| **Bold/TikTok** | Social reels | font=32, bg=none with thick outline, animation=word-highlight, words_per_chunk=3 |
| **Karaoke** | Lyric video | font=28, bg=solid, animation=word-highlight, color shifts on each word |
| **Minimal** | Cinematic | font=16, bg=none, fade 500ms, no outline, position=bottom |
| **Cards** | Tutorial / explainer | font=24, bg=gradient, position=top, animation=pop |

## Common pitfalls

- **Hebrew word-level alignment can be flaky** — ivrit-ai's wav2vec is sometimes better than imvladikon. If alignment crashes, fall back to segment-level + manual chunking.
- **VFR videos cause whisperx audio sync drift** — re-encode source to CFR first: `ffmpeg -i in.mp4 -fps_mode cfr -r 30 -c:a copy out.mp4`
- **Multi-language videos**: pass `language=auto` to whisper; for mixed Hebrew+English, transcribe twice and merge by timestamp.
- **Background music interferes with transcription** — extract vocal channel first with `demucs` if available, or set `--vad_filter`.
- **Long videos** (>5 min): batch by 60-second chunks to avoid memory issues, then concat SRTs.

## Quality checks before delivery

1. Open the SRT and verify Hebrew letters render correctly (no `???`).
2. Spot-check 3 timestamps in the video — does the caption match what's spoken?
3. Confirm RTL: Hebrew text should read right-to-left (commas at the LEFT of the line in display).
4. If user asked for word-highlight, verify each word's `start`/`end` is within its segment.

## Reference implementation

A working implementation is in this skill folder: `caption.py`. Run with:
```bash
python3 caption.py /path/to/video.mp4 \
  --language he \
  --font-size 18 \
  --background box \
  --animation fade \
  --words-per-chunk 5 \
  --burn  # optional, also produces _captioned.mp4
```

The script handles all the steps above end-to-end and is the recommended entry point. If the user wants something the script doesn't expose, edit the script — don't rebuild from scratch.

## Asking the user

Before running, if the user didn't specify, ask:
1. Style preset? (Subtle/Bold/Karaoke/Minimal/Cards/custom)
2. Burn into video, or just SRT?
3. Hebrew or other language?

Don't ask if they already specified — just run with sensible defaults.
