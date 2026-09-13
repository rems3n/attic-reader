"""Photo → OCR-ready page image.

Phone photos of textbook pages arrive rotated, unevenly lit and slightly
skewed.  This module normalizes them with OpenCV before Tesseract sees them:

1. EXIF orientation + grayscale
2. scale so the text is large enough for Tesseract (long side ~2600 px)
3. illumination flattening (divide by a heavily blurred background) + CLAHE
4. light denoise that keeps breathings/accents intact
5. deskew by projection-profile search (text lines become horizontal)

Deliberately *no* hard binarization: Tesseract's own Otsu step does better on
the normalized grayscale, and thresholding is what erases thin diacritics.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageOps

log = logging.getLogger("attic.ocr")

try:  # OpenCV is optional at import time so the API still starts without it.
    import cv2
except ImportError as exc:  # pragma: no cover - exercised only on hosts without OpenCV
    cv2 = None  # type: ignore[assignment]
    # Loud on purpose: the Pillow fallback reads real book photos badly (CER ~0.5
    # vs ~0.04 on the Loeb regression page). Deployed images must ship OpenCV.
    log.error("OpenCV unavailable (%s); OCR will use the low-quality Pillow fallback", exc)

TARGET_LONG_SIDE = 2600
MAX_LONG_SIDE = 4000
MAX_SKEW_DEGREES = 12.0


@dataclass(frozen=True)
class PreprocessReport:
    width: int
    height: int
    scale: float
    skew_degrees: float
    deskewed: bool
    engine: str


# Ink threshold on the flattened grayscale (paper ~250, ink ~30-80). A fixed
# level, unlike Otsu, ignores verso bleed-through and page-edge shadow.
INK_LEVEL = 110


def detect_text_columns(gray: np.ndarray, ink_level: int = INK_LEVEL) -> tuple[int, int]:
    """Horizontal extent [x0, x1) of the text block, excluding page-edge shadows.

    A shadow or gutter is a narrow, very dark, page-tall stripe; text columns
    are wide and only partially inked. We keep columns whose ink coverage is
    between 0.5 % and 60 % of the page height, then take the widest run.
    """
    h, w = gray.shape[:2]
    cover = (gray < ink_level).sum(axis=0) / float(max(h, 1))
    # Smooth over ~2.5 % of the width so word spaces that happen to line up
    # across a few lines do not split the text block into fragments.
    window = max(15, w // 40)
    cover = np.convolve(cover, np.ones(window) / window, mode="same")
    ok = (cover > 0.003) & (cover < 0.6)
    best = (0, w)
    best_len = 0
    start = None
    for x in range(w + 1):
        on = x < w and ok[x]
        if on and start is None:
            start = x
        if not on and start is not None:
            if x - start > best_len:
                best, best_len = (start, x), x - start
            start = None
    if best_len < w * 0.3:
        return 0, w
    pad = int(0.02 * w)
    return max(0, best[0] - pad), min(w, best[1] + pad)


def detect_text_lines(gray: np.ndarray, ink_level: int = INK_LEVEL) -> tuple[list[tuple[int, int]], float]:
    """Row spans [y0, y1) of text lines and the median line height.

    Uses the horizontal ink profile. Short bands (a row of accents/breathings,
    or descender fragments) are attached to the nearest tall band so every
    returned span carries its diacritics; that is what stops Tesseract from
    reading an accent row as a line of its own.
    """
    h, w = gray.shape[:2]
    x0, x1 = detect_text_columns(gray, ink_level)
    profile = (gray[:, x0:x1] < ink_level).sum(axis=1).astype(np.float64)
    reference = float(np.percentile(profile, 95))
    if reference < 10:
        return [], 0.0
    threshold = max(3.0, 0.05 * reference)
    inked = profile > threshold
    raw: list[list[int]] = []
    start = None
    for y, on in enumerate(inked):
        if on and start is None:
            start = y
        if not on and start is not None:
            raw.append([start, y])
            start = None
    if start is not None:
        raw.append([start, h])
    if not raw:
        return [], 0.0
    heights = np.array([e - s for s, e in raw], dtype=np.float64)
    tall = heights[heights >= 0.5 * heights.max()]
    median = float(np.median(tall))
    lines: list[list[int]] = []
    i = 0
    while i < len(raw):
        s, e = raw[i]
        if (e - s) < 0.4 * median:
            prev = lines[-1] if lines else None
            nxt = raw[i + 1] if i + 1 < len(raw) else None
            gap_prev = s - prev[1] if prev else float("inf")
            gap_next = nxt[0] - e if nxt else float("inf")
            if min(gap_prev, gap_next) < 0.5 * median:
                if gap_next <= gap_prev and nxt is not None:
                    nxt[0] = s  # accents sit above their line
                elif prev is not None:
                    prev[1] = e  # descender fragments hang below theirs
            i += 1
            continue
        lines.append([s, e])
        i += 1
    return [(s, e) for s, e in lines if (e - s) >= 0.4 * median], median


def crop_lines(gray: np.ndarray, pad_frac: float = 0.3) -> list[np.ndarray]:
    """One image per text line (with its diacritics), trimmed to the text column."""
    lines, median = detect_text_lines(gray)
    if not lines:
        return []
    x0, x1 = detect_text_columns(gray)
    pad = int(pad_frac * median)
    h = gray.shape[0]
    return [gray[max(0, s - pad) : min(h, e + pad), x0:x1] for s, e in lines]


def opencv_available() -> bool:
    return cv2 is not None


def load_grayscale(data: bytes) -> np.ndarray:
    image = Image.open(io.BytesIO(data))
    image = ImageOps.exif_transpose(image)
    return np.asarray(image.convert("L"), dtype=np.uint8)


def rescale(gray: np.ndarray, target: int = TARGET_LONG_SIDE, maximum: int = MAX_LONG_SIDE) -> tuple[np.ndarray, float]:
    long_side = max(gray.shape[:2])
    if long_side <= 0:
        return gray, 1.0
    if long_side < target:
        scale = target / long_side
        interpolation = cv2.INTER_CUBIC
    elif long_side > maximum:
        scale = maximum / long_side
        interpolation = cv2.INTER_AREA
    else:
        return gray, 1.0
    size = (max(1, int(round(gray.shape[1] * scale))), max(1, int(round(gray.shape[0] * scale))))
    return cv2.resize(gray, size, interpolation=interpolation), scale


def flatten_illumination(gray: np.ndarray) -> np.ndarray:
    """Remove page-scale shading (shadow of the hand, lamp fall-off)."""
    kernel = max(31, (min(gray.shape[:2]) // 20) | 1)
    background = cv2.GaussianBlur(gray, (kernel, kernel), 0).astype(np.float32)
    background = np.maximum(background, 1.0)
    normalized = gray.astype(np.float32) / background
    normalized = np.clip(normalized * 255.0 * 0.98, 0, 255).astype(np.uint8)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(normalized)


def denoise(gray: np.ndarray) -> np.ndarray:
    # A 3px median kills sensor speckle but leaves 4–6 px diacritics alone.
    return cv2.medianBlur(gray, 3)


def _projection_score(binary: np.ndarray, angle: float) -> float:
    h, w = binary.shape[:2]
    matrix = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), angle, 1.0)
    rotated = cv2.warpAffine(binary, matrix, (w, h), flags=cv2.INTER_NEAREST, borderValue=0)
    profile = rotated.sum(axis=1, dtype=np.float64)
    # Sharp, separated text lines maximise the variance of the row profile.
    return float(np.var(profile))


def estimate_skew(gray: np.ndarray, max_degrees: float = MAX_SKEW_DEGREES) -> float:
    """Angle (degrees, counter-clockwise positive) by which text lines are tilted."""
    work = gray
    long_side = max(work.shape[:2])
    if long_side > 1000:
        factor = 1000.0 / long_side
        work = cv2.resize(work, None, fx=factor, fy=factor, interpolation=cv2.INTER_AREA)
    _, binary = cv2.threshold(work, 0, 1, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    if binary.sum() < 50:
        return 0.0

    def best(angles: np.ndarray) -> float:
        scores = [_projection_score(binary, float(a)) for a in angles]
        return float(angles[int(np.argmax(scores))])

    # `best` returns the rotation that straightens the lines; the tilt of the
    # text is its negative.
    coarse = best(np.arange(-max_degrees, max_degrees + 0.01, 0.5))
    fine = best(np.arange(coarse - 0.5, coarse + 0.51, 0.1))
    return round(-fine, 2)


def rotate(gray: np.ndarray, degrees: float) -> np.ndarray:
    h, w = gray.shape[:2]
    matrix = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), degrees, 1.0)
    cos, sin = abs(matrix[0, 0]), abs(matrix[0, 1])
    new_w = int(h * sin + w * cos)
    new_h = int(h * cos + w * sin)
    matrix[0, 2] += new_w / 2.0 - w / 2.0
    matrix[1, 2] += new_h / 2.0 - h / 2.0
    # Fill with the page colour (white-ish) so the border does not become "ink".
    border = int(np.percentile(gray, 90))
    return cv2.warpAffine(gray, matrix, (new_w, new_h), flags=cv2.INTER_CUBIC, borderValue=border)


def preprocess(data: bytes, *, deskew: bool = True) -> tuple[Image.Image, PreprocessReport]:
    """Return an OCR-ready grayscale PIL image and what was done to it."""
    gray = load_grayscale(data)
    if cv2 is None:
        image = Image.fromarray(gray)
        image = ImageOps.autocontrast(image, cutoff=1)
        report = PreprocessReport(image.width, image.height, 1.0, 0.0, False, "pillow")
        return image, report

    gray, scale = rescale(gray)
    gray = flatten_illumination(gray)
    gray = denoise(gray)

    skew = 0.0
    deskewed = False
    if deskew:
        skew = estimate_skew(gray)
        if abs(skew) >= 0.2:
            gray = rotate(gray, -skew)
            deskewed = True

    image = Image.fromarray(gray)
    report = PreprocessReport(image.width, image.height, scale, skew, deskewed, "opencv")
    return image, report
