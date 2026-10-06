"""Common helpers: paths, ffmpeg, Arabic text shaping for PIL."""
import os, re, subprocess
import arabic_reshaper
from bidi.algorithm import get_display
from PIL import ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # .../bermuda-video
IMG = os.path.join(ROOT, 'images')
AUD = os.path.join(ROOT, 'audio')
OUT = os.path.join(ROOT, 'output')
BLD = os.path.join(ROOT, 'build')
OV  = os.path.join(BLD, 'overlays')
_repo_fonts = os.path.join(ROOT, 'fonts')
_ws_fonts = os.path.join(os.path.dirname(os.path.dirname(ROOT)), 'fonts')
FONTS = _repo_fonts if os.path.isdir(_repo_fonts) else _ws_fonts
os.makedirs(OV, exist_ok=True)

import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()

FPS = 25
W, H = 1920, 1080

FONT_BODY = os.path.join(FONTS, 'Vazir.ttf')
FONT_HEAD = os.path.join(FONTS, 'Sahel.ttf')
FONT_SERIF = os.path.join(FONTS, 'Parastoo.ttf')


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise RuntimeError('ffmpeg failed:\n' + ' '.join(cmd[:12]) + '\n' + r.stderr[-3000:])
    return r


def ffprobe_dur(path):
    r = subprocess.run([FF, '-i', path], capture_output=True, text=True)
    m = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', r.stderr)
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def ar(text):
    """Reshape + reorder Arabic for PIL drawing."""
    return get_display(arabic_reshaper.reshape(text))


def font(path, size):
    return ImageFont.truetype(path, size)


def blocks():
    """Parse narration.md -> list of (id, text)."""
    t = open(os.path.join(ROOT, 'narration.md'), encoding='utf-8').read()
    parts = re.split(r'\[\[(B\d+)\]\]\n', t)
    return [(a, b.strip()) for a, b in zip(parts[1::2], parts[2::2])]
