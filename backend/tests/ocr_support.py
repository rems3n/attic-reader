"""Helpers shared by the OCR tests: synthetic page rendering, photo-like
degradation, and a character error rate."""

from __future__ import annotations

import io
import shutil
import subprocess
import unicodedata

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    "/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf",
]


def tesseract_has_grc() -> bool:
    exe = shutil.which("tesseract")
    if not exe:
        return False
    try:
        out = subprocess.run([exe, "--list-langs"], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return False
    return "grc" in (out.stdout + out.stderr).split()


def _font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    raise RuntimeError("No serif TTF with polytonic Greek found for the OCR test")


def render_page(lines: list[str], *, width: int = 1400, font_size: int = 56, margin: int = 90) -> Image.Image:
    font = _font(font_size)
    line_h = int(font_size * 1.6)
    height = margin * 2 + line_h * len(lines)
    page = Image.new("L", (width, height), 245)
    draw = ImageDraw.Draw(page)
    for i, line in enumerate(lines):
        draw.text((margin, margin + i * line_h), line, font=font, fill=20)
    return page


def degrade(image: Image.Image, *, rotate: float = 0.0, shade: bool = False, noise: float = 0.0, seed: int = 1) -> Image.Image:
    """Make a clean render look like a hand-held phone photo."""
    gray = image.convert("L")
    if rotate:
        gray = gray.rotate(rotate, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=245)
    arr = np.asarray(gray, dtype=np.float32)
    if shade:
        h, w = arr.shape
        yy, xx = np.mgrid[0:h, 0:w]
        # Lamp fall-off across the page plus a soft "hand shadow" on one side.
        gradient = 1.0 - 0.45 * (xx / max(w - 1, 1)) - 0.15 * (yy / max(h - 1, 1))
        arr = arr * gradient
    if noise:
        rng = np.random.default_rng(seed)
        arr = arr + rng.normal(0, noise, arr.shape)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def to_png_bytes(image: Image.Image) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def cer(expected: str, actual: str) -> float:
    """Character error rate on NFC, whitespace-normalized text."""
    norm = lambda s: " ".join(unicodedata.normalize("NFC", s).split())  # noqa: E731
    e, a = norm(expected), norm(actual)
    if not e:
        return 0.0 if not a else 1.0
    return _levenshtein(e, a) / len(e)
