"""Offline demo render (not a replacement for MoneyPrinterTurbo)."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import textwrap
from PIL import Image, ImageDraw, ImageFont

W, H = 540, 960  # lightweight vertical preview; upgrade to 1080x1920 in MoneyPrinterTurbo
FONT_CANDIDATES = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf',
    '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
    'C:/Windows/Fonts/arial.ttf',
]


def font(size):
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def break_lines(draw, text: str, ft, width: int) -> list[str]:
    out = []
    for paragraph in text.splitlines():
        if not paragraph.strip():
            continue
        words = paragraph.split()
        line = ''
        for word in words:
            next_line = f'{line} {word}'.strip()
            if draw.textbbox((0, 0), next_line, font=ft)[2] > width and line:
                out.append(line)
                line = word
            else:
                line = next_line
        if line:
            out.append(line)
    return out[:14]


def draw_card(path: Path, headline: str, body: str, index: int, total: int):
    palettes = [((12, 23, 49), (43, 91, 131)), ((17, 53, 63), (43, 121, 131)), ((42, 27, 68), (111, 59, 119))]
    top, bottom = palettes[index % len(palettes)]
    image = Image.new('RGB', (W, H))
    pix = image.load()
    for y in range(H):
        t = y / (H - 1)
        rgb = tuple(round(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        for x in range(W):
            pix[x, y] = rgb
    d = ImageDraw.Draw(image)
    d.rounded_rectangle((35, 46, W - 35, 105), radius=20, fill='#ffffff25', outline='#5ec8c7', width=2)
    d.text((59, 60), 'SOCIAL FACTORY  /  DEMO', font=font(19), fill='#a5eee9')
    hft, bft = font(44), font(29)
    lines = break_lines(d, headline, hft, W - 92)[:5]
    y = 220
    for ln in lines:
        d.text((45, y), ln, font=hft, fill='#ffffff', stroke_width=1, stroke_fill='#102337')
        y += 59
    y = max(520, y + 58)
    for ln in break_lines(d, body, bft, W - 90)[:8]:
        d.text((45, y), ln, font=bft, fill='#e5fbfc')
        y += 43
    d.rounded_rectangle((42, H-94, W-42, H-82), fill='#5f7d8a', radius=6)
    seg = (W - 84) * (index + 1) / total
    d.rounded_rectangle((42, H-94, 42+round(seg), H-82), fill='#42e1cb', radius=6)
    d.text((45, H-65), f'DEMO PREVIEW  •  SLIDE {index+1}/{total}', fill='#acbfc9', font=font(17))
    image.save(path)


def render_demo(topic: str, script: str, dst: Path) -> Path:
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        raise RuntimeError('FFmpeg is required. Install ffmpeg or use Docker.')
    dst.parent.mkdir(parents=True, exist_ok=True)
    pieces = [x.strip() for x in re.split(r'(?<=[.!?])\s+|\n\n+', script) if x.strip()]
    snippets = [' '.join(pieces[i::3])[:220] for i in range(3)]
    headlines = [topic[:75], 'Three things to consider', 'Check, improve, and share']
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        files = []
        for i, (headline, text) in enumerate(zip(headlines, snippets)):
            image = base / f'card{i}.png'
            clip = base / f'clip{i}.mp4'
            draw_card(image, headline, text, i, 3)
            cmd = [ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-loop', '1', '-i', str(image),
                   '-t', '3', '-r', '24', '-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p',
                   '-movflags', '+faststart', str(clip)]
            subprocess.run(cmd, check=True, capture_output=True, timeout=110)
            files.append(clip)
        manifest = base / 'concat.txt'
        manifest.write_text(''.join(f"file '{c}'\n" for c in files), encoding='utf-8')
        subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0',
                        '-i', str(manifest), '-c', 'copy', '-movflags', '+faststart', str(dst)],
                       check=True, capture_output=True, timeout=60)
    return dst


def render_mpt(script: str) -> Path:
    import json
    import os
    command = shutil.which('mpt')
    if not command:
        raise RuntimeError('MoneyPrinterTurbo not found. Install with pip install mpt; configure in mpt webui.')
    proc = subprocess.run([command, 'cli', '--video-script', script, '--stop-at', 'video'],
                          capture_output=True, text=True, timeout=900,
                          env=os.environ.copy())
    if proc.returncode:
        raise RuntimeError(f'MoneyPrinterTurbo failed: {proc.stderr[-700:]}')
    # The MPT CLI prints a JSON task summary; output keys may change between versions.
    try:
        last = next(ln for ln in reversed(proc.stdout.splitlines()) if ln.strip().startswith('{'))
        summary = json.loads(last)
    except (StopIteration, ValueError, json.JSONDecodeError):
        raise RuntimeError('MoneyPrinterTurbo finished but its JSON output could not be parsed. Inspect the MPT task storage directory.')
    def walk(o):
        if isinstance(o, dict):
            for v in o.values(): yield from walk(v)
        elif isinstance(o, list):
            for v in o: yield from walk(v)
        elif isinstance(o, str) and o.lower().endswith('.mp4'):
            yield Path(o).expanduser()
    for p in walk(summary):
        if p.exists() and p.is_file():
            return p
    raise RuntimeError('MPT generated a task, but no MP4 path was found in CLI JSON. Find the MP4 under MPT_HOME/storage/tasks and attach it manually.')
