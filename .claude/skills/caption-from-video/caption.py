#!/usr/bin/env python3
"""caption-from-video — generate styled captions for any video file.

Usage:
  python3 caption.py /path/to/video.mp4 [options]

Options:
  --language he|en|ar|auto    Source language (default: he)
  --model MODEL               whisper model: large-v3 / medium / small / ivrit-ai/whisper-large-v3-turbo (default: large-v3)
  --font FONT                 Font name (default: Arial)
  --font-size N               Font size in pt (default: 18)
  --background STYLE          none / box / solid / gradient (default: box)
  --position POS              bottom / top / center / top-right / bottom-left (default: bottom)
  --animation TYPE            none / fade / pop / word-highlight (default: fade)
  --words-per-chunk N         Max words per caption (default: 5)
  --text-color HEX            #RRGGBB (default: #FFFFFF)
  --outline-color HEX         #RRGGBB (default: #000000)
  --bg-alpha 0-255            Background transparency (default: 192 = 75% opaque)
  --burn                      Also produce <basename>_captioned.mp4
  --out-dir DIR               Output directory (default: same as input)
  --preset NAME               Use preset: subtle / bold / karaoke / minimal / cards
  --no-align                  Skip word-level alignment (faster but no word-highlight)

Outputs (in --out-dir):
  <basename>.srt              Caption file
  <basename>.ass              Styled subtitle file
  <basename>_captioned.mp4    Burnt-in video (only if --burn)
"""
import os, sys, re, json, time, subprocess, argparse, warnings
warnings.filterwarnings('ignore')

# PyTorch 2.6+ compat for pyannote checkpoints
import torch
_orig_load = torch.load
def _patched_load(*a, **kw):
    kw['weights_only'] = False
    return _orig_load(*a, **kw)
torch.load = _patched_load

# Bundled ffmpeg
def _ensure_ffmpeg():
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        ff_dir = os.path.dirname(ffmpeg_exe)
        symlink = os.path.join(ff_dir, "ffmpeg")
        if not os.path.exists(symlink):
            os.symlink(ffmpeg_exe, symlink)
        os.environ['PATH'] = ff_dir + ':' + os.environ.get('PATH', '')
        return ffmpeg_exe
    except ImportError:
        return "ffmpeg"

FF = _ensure_ffmpeg()

PRESETS = {
    'subtle':   dict(font_size=18, background='box',     animation='fade', words_per_chunk=5, position='bottom'),
    'bold':     dict(font_size=32, background='none',    animation='word-highlight', words_per_chunk=3, position='bottom'),
    'karaoke':  dict(font_size=28, background='solid',   animation='word-highlight', words_per_chunk=4, position='bottom'),
    'minimal':  dict(font_size=16, background='none',    animation='fade', words_per_chunk=6, position='bottom'),
    'cards':    dict(font_size=24, background='gradient', animation='pop',  words_per_chunk=4, position='top'),
}

POS_TO_ALIGN = {  # ASS numpad alignment
    'bottom': 2, 'top': 8, 'center': 5,
    'bottom-left': 1, 'bottom-right': 3,
    'top-left': 7, 'top-right': 9,
    'middle-left': 4, 'middle-right': 6,
}

def hex_to_ass_color(hex_color, alpha_hex='00'):
    """ '#RRGGBB' → '&H{alpha}{BB}{GG}{RR}' (ASS uses BGR)."""
    h = hex_color.lstrip('#')
    rr, gg, bb = h[0:2], h[2:4], h[4:6]
    return f"&H{alpha_hex}{bb}{gg}{rr}".upper()

def fmt_srt_time(t):
    h = int(t // 3600); m = int((t % 3600) // 60); s = t % 60
    return f"{h:02d}:{m:02d}:{int(s):02d},{int((s - int(s)) * 1000):03d}"

def fmt_ass_time(t):
    h = int(t // 3600); m = int((t % 3600) // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def split_chunks(text, max_words=5):
    text = text.replace('\n', ' ').strip()
    parts = re.split(r'(?<=[.!?])\s+|\.\.\.\s*', text)
    chunks = []
    for p in parts:
        sub = re.split(r',\s+', p) if len(p.split()) > max_words * 2 else [p]
        for sp in sub:
            words = sp.strip().rstrip('.,!?').split()
            if not words: continue
            for i in range(0, len(words), max_words):
                chunks.append(' '.join(words[i:i+max_words]))
    return chunks

def distribute_chunks(chunks, t_start, t_end, min_dur=0.5, max_dur=4.0):
    if not chunks: return []
    weights = [max(len(c), 1) for c in chunks]
    total_w = sum(weights); span = t_end - t_start
    out = []; t = t_start
    for c, w in zip(chunks, weights):
        d = max(min_dur, min(max_dur, span * w / total_w))
        out.append((t, t + d, c)); t += d
    return out

def transcribe(video_path, language='he', model_name='large-v3', do_align=True):
    import whisperx
    print(f"⏳ Loading model {model_name}...", flush=True)
    t0 = time.time()
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    compute_type = 'float16' if device == 'cuda' else 'int8'
    model = whisperx.load_model(model_name, device, compute_type=compute_type, language=language)
    print(f"   Model loaded in {time.time()-t0:.1f}s", flush=True)

    print(f"⏳ Loading audio...", flush=True)
    audio = whisperx.load_audio(video_path)
    audio_dur = len(audio) / 16000
    print(f"   Audio: {audio_dur:.1f}s", flush=True)

    print(f"⏳ Transcribing...", flush=True)
    t1 = time.time()
    result = model.transcribe(audio, batch_size=4)
    print(f"   Done in {time.time()-t1:.1f}s ({(time.time()-t1)/audio_dur:.2f}x rt), {len(result['segments'])} segments", flush=True)

    if do_align:
        try:
            align_model_name = {
                'he': 'imvladikon/wav2vec2-xls-r-300m-hebrew',
                'en': 'WAV2VEC2_ASR_LARGE_LV60K_960H',
                'ar': 'jonatasgrosman/wav2vec2-large-xlsr-53-arabic',
            }.get(language)
            if align_model_name:
                print(f"⏳ Aligning words ({align_model_name})...", flush=True)
                align_model, metadata = whisperx.load_align_model(
                    language_code=language, device=device, model_name=align_model_name
                )
                result = whisperx.align(result["segments"], align_model, metadata, audio, device)
                print(f"   ✅ Word-level timestamps available", flush=True)
        except Exception as e:
            print(f"   ⚠️ Alignment failed ({e}); using segment-level", flush=True)
    return result

def build_ass(segments, output_path, *,
              font='Arial', font_size=18, background='box', position='bottom',
              animation='fade', text_color='#FFFFFF', outline_color='#000000',
              bg_alpha=192, words_per_chunk=5, video_w=1280, video_h=720,
              language='he', has_words=False):
    primary = hex_to_ass_color(text_color)
    outline = hex_to_ass_color(outline_color)
    back_alpha = f"{(255 - bg_alpha):02X}"  # ASS alpha: 00 opaque, FF transparent
    back = hex_to_ass_color('#000000', back_alpha)
    border_style = {'none': 1, 'box': 3, 'solid': 3, 'gradient': 3}.get(background, 1)
    align = POS_TO_ALIGN.get(position, 2)
    margin_v = 30 if 'bottom' in position else (30 if 'top' in position else 360)

    fade_ms = 250 if animation == 'fade' else 0

    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {video_w}",
        f"PlayResY: {video_h}",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Default,{font},{font_size},{primary},&H000000FF,{outline},{back},"
        f"1,0,0,0,100,100,0,0,{border_style},2,1,{align},30,30,{margin_v},1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    # Convert segments → chunks
    if has_words and animation == 'word-highlight':
        # Per-segment line, with karaoke timing per word
        for seg in segments:
            words = seg.get('words') or []
            if not words: continue
            # Group into chunks of N words
            for i in range(0, len(words), words_per_chunk):
                grp = words[i:i+words_per_chunk]
                start = grp[0].get('start', seg['start'])
                end = grp[-1].get('end', seg['end'])
                k_text = ""
                for w in grp:
                    dur_cs = max(1, int(round(((w.get('end', end) - w.get('start', start)) * 100))))
                    word_text = w.get('word', '').strip()
                    k_text += f"{{\\k{dur_cs}}}{word_text} "
                lines.append(f"Dialogue: 0,{fmt_ass_time(start)},{fmt_ass_time(end)},Default,,0,0,0,,{k_text.strip()}")
    else:
        # Chunk by max_words then distribute time across chunks
        for seg in segments:
            text = seg.get('text', '').strip()
            if not text: continue
            chunks = split_chunks(text, max_words=words_per_chunk)
            timed = distribute_chunks(chunks, seg['start'], seg['end'])
            for s, e, t in timed:
                fade_tag = f"{{\\fad({fade_ms},{fade_ms})}}" if fade_ms else ""
                lines.append(f"Dialogue: 0,{fmt_ass_time(s)},{fmt_ass_time(e)},Default,,0,0,0,,{fade_tag}{t}")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

def build_srt(segments, output_path, words_per_chunk=5):
    with open(output_path, 'w', encoding='utf-8') as f:
        idx = 1
        for seg in segments:
            text = seg.get('text', '').strip()
            if not text: continue
            chunks = split_chunks(text, max_words=words_per_chunk)
            timed = distribute_chunks(chunks, seg['start'], seg['end'])
            for s, e, t in timed:
                f.write(f"{idx}\n{fmt_srt_time(s)} --> {fmt_srt_time(e)}\n{t}\n\n")
                idx += 1

def burn_in(video_path, ass_path, out_path):
    safe = ass_path.replace("'", r"\'").replace(":", r"\:").replace(",", r"\,")
    cmd = [FF, "-y", "-i", video_path,
           "-vf", f"ass='{safe}'",
           "-c:v", "libx264", "-preset", "fast", "-crf", "20",
           "-c:a", "copy", out_path]
    print(f"⏳ Burning captions → {os.path.basename(out_path)}...", flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Burn failed: {r.stderr[-500:]}")
    return out_path

def get_video_dimensions(video_path):
    try:
        cmd = [FF, "-i", video_path]
        r = subprocess.run(cmd, capture_output=True, text=True)
        m = re.search(r'(\d{2,5})x(\d{2,5})', r.stderr)
        if m: return int(m.group(1)), int(m.group(2))
    except Exception: pass
    return 1280, 720

def main():
    p = argparse.ArgumentParser()
    p.add_argument('video', help='Path to video/audio file')
    p.add_argument('--language', default='he')
    p.add_argument('--model', default='large-v3')
    p.add_argument('--font', default='Arial')
    p.add_argument('--font-size', type=int, default=18)
    p.add_argument('--background', default='box', choices=['none','box','solid','gradient'])
    p.add_argument('--position', default='bottom')
    p.add_argument('--animation', default='fade', choices=['none','fade','pop','word-highlight'])
    p.add_argument('--words-per-chunk', type=int, default=5)
    p.add_argument('--text-color', default='#FFFFFF')
    p.add_argument('--outline-color', default='#000000')
    p.add_argument('--bg-alpha', type=int, default=192)
    p.add_argument('--burn', action='store_true')
    p.add_argument('--out-dir', default=None)
    p.add_argument('--preset', default=None, choices=list(PRESETS.keys()))
    p.add_argument('--no-align', action='store_true')
    args = p.parse_args()

    # Apply preset (overrides defaults but not explicit CLI args)
    if args.preset:
        for k, v in PRESETS[args.preset].items():
            attr = k.replace('-', '_')
            # Only apply if user didn't explicitly set
            if attr in args and getattr(args, attr) == p.get_default(attr):
                setattr(args, attr, v)

    if not os.path.exists(args.video):
        print(f"❌ File not found: {args.video}"); sys.exit(1)

    out_dir = args.out_dir or os.path.dirname(args.video) or '.'
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(args.video))[0]
    srt_path = os.path.join(out_dir, base + '.srt')
    ass_path = os.path.join(out_dir, base + '.ass')
    burnt_path = os.path.join(out_dir, base + '_captioned.mp4')

    # Word-highlight needs alignment
    do_align = not args.no_align and args.animation == 'word-highlight'

    print(f"\n🎬 caption-from-video")
    print(f"   in:  {args.video}")
    print(f"   out: {out_dir}")
    print(f"   preset: {args.preset or 'custom'} | font {args.font} {args.font_size}pt | bg {args.background} | anim {args.animation} | chunks {args.words_per_chunk} words")
    print()

    result = transcribe(args.video, args.language, args.model, do_align=do_align)
    has_words = any('words' in s and s['words'] for s in result['segments'])

    print(f"\n⏳ Writing SRT → {os.path.basename(srt_path)}", flush=True)
    build_srt(result['segments'], srt_path, words_per_chunk=args.words_per_chunk)

    print(f"⏳ Writing ASS → {os.path.basename(ass_path)}", flush=True)
    w, h = get_video_dimensions(args.video)
    build_ass(
        result['segments'], ass_path,
        font=args.font, font_size=args.font_size, background=args.background,
        position=args.position, animation=args.animation,
        text_color=args.text_color, outline_color=args.outline_color,
        bg_alpha=args.bg_alpha, words_per_chunk=args.words_per_chunk,
        video_w=w, video_h=h, language=args.language, has_words=has_words,
    )

    if args.burn:
        burn_in(args.video, ass_path, burnt_path)
        print(f"✅ Captioned video: {burnt_path}")

    print(f"\n✅ Done.")
    print(f"   SRT: {srt_path}")
    print(f"   ASS: {ass_path}")
    if args.burn: print(f"   MP4: {burnt_path}")

if __name__ == '__main__':
    main()
