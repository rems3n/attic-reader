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
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageOps

try:  # OpenCV is optional at import time so the API still starts without it.
    import cv2
except ImportError:  # pragma: no cover - exercised only on hosts without OpenCV
    cv2 = None  # type: ignore[assignment]

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
