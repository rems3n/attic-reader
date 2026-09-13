from __future__ import annotations

import io
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import asdict

from concurrent.futures import ThreadPoolExecutor

import numpy as np
from PIL import Image, ImageFilter, ImageOps

from .ocr_preprocess import PreprocessReport, crop_lines, opencv_available, preprocess


class OCRUnavailable(RuntimeError):
    pass


def _prepare_image_basic(data: bytes) -> Image.Image:
    """Pillow-only path kept for hosts without OpenCV (OCR_PREPROCESS=basic)."""
    image = Image.open(io.BytesIO(data))
    image = ImageOps.exif_transpose(image)
    image = image.convert("L")

    if image.width < 2200:
        scale = min(2.0, 2200 / max(image.width, 1))
        image = image.resize(
            (int(image.width * scale), int(image.height * scale)),
            Image.Resampling.LANCZOS,
        )

    image = ImageOps.autocontrast(image, cutoff=1)
    image = image.filter(ImageFilter.SHARPEN)
    return image


def prepare_image(data: bytes) -> tuple[Image.Image, PreprocessReport]:
    mode = os.getenv("OCR_PREPROCESS", "opencv").lower()
    if mode == "basic":
        image = _prepare_image_basic(data)
        return image, PreprocessReport(image.width, image.height, 1.0, 0.0, False, "pillow-basic")
    return preprocess(data, deskew=mode != "nodeskew")


def _tesseract_env() -> dict[str, str]:
    env = dict(os.environ)
    # Tesseract's OpenMP threading is counter-productive: a single page is
    # ~2 s single-threaded but minutes when several instances fight for cores.
    env.setdefault("OMP_THREAD_LIMIT", "1")
    return env


def run_tesseract(image: Image.Image, *, psm: int | None = None, clean: bool = True) -> str:
    command = os.getenv("TESSERACT_COMMAND", "tesseract")
    executable = shutil.which(command)
    if executable is None:
        raise OCRUnavailable(f"Tesseract executable not found: {command}")

    psm = psm if psm is not None else int(os.getenv("TESSERACT_PSM", "6"))
    with tempfile.NamedTemporaryFile(suffix=".png") as temp:
        image.save(temp.name, format="PNG")
        proc = subprocess.run(
            [executable, temp.name, "stdout", "-l", "grc", "--psm", str(psm), "--oem", "1"],
            capture_output=True,
            text=True,
            timeout=120,
            env=_tesseract_env(),
        )

    if proc.returncode != 0:
        raise OCRUnavailable(proc.stderr.strip() or "Tesseract OCR failed")
    return _clean_ocr(proc.stdout) if clean else proc.stdout


def run_tesseract_by_line(line_images: list[np.ndarray], *, workers: int = 4) -> str:
    """Recognise each pre-segmented line in single-line mode (psm 7).

    Tesseract's own layout analysis tends to split a row of polytonic
    diacritics off as a separate line; handing it one line at a time removes
    that failure mode entirely. Lines are independent, so they run in parallel.
    """
    crops = [Image.fromarray(arr) for arr in line_images]
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        texts = list(pool.map(lambda im: run_tesseract(im, psm=7, clean=False), crops))
    return _clean_ocr("\n".join(" ".join(t.split()) for t in texts))


MIN_LINES_FOR_LINE_MODE = 3


def recognize_ancient_greek_with_report(data: bytes) -> tuple[str, dict[str, object]]:
    image, report = prepare_image(data)
    info: dict[str, object] = asdict(report)
    mode = os.getenv("OCR_LINE_MODE", "auto").lower()  # auto | lines | page
    lines: list[np.ndarray] = []
    if mode != "page" and opencv_available() and report.engine == "opencv":
        lines = crop_lines(np.asarray(image))
    if lines and (len(lines) >= MIN_LINES_FOR_LINE_MODE or mode == "lines"):
        workers = int(os.getenv("OCR_WORKERS", str(min(4, os.cpu_count() or 1))))
        text = run_tesseract_by_line(lines, workers=workers)
        info.update(mode="lines", lines=len(lines))
    else:
        text = run_tesseract(image)
        info.update(mode="page", lines=len(lines))
    return text, info


def recognize_ancient_greek(data: bytes) -> str:
    text, _ = recognize_ancient_greek_with_report(data)
    return text


_GREEK_RE = re.compile(r"[\u0370-\u03ff\u1f00-\u1fff]")
_STRAY_TOKEN_RE = re.compile(r"^[\]\[|/\\)(}{~_=\-—–\.,:;·'\u2019\u02bc\u1fbd\u1fbf\u1ffe\u0384\u0385\u00b4\u02b9\u02bb`^\"\u201c\u201d\u2018\u2026\s]+$")


def _clean_ocr(text: str) -> str:
    """Whitespace normalization plus conservative fixes for Tesseract-grc habits.

    - ``:`` between Greek letters is the ano teleia (printed Greek uses ``·``;
      a Latin colon essentially never occurs in an edition).
    - Lines without a single Greek letter are layout noise (rows of accents
      that were split off from their text line, margin marks, page furniture).
    - Trailing tokens made only of brackets/pipes/quotes are page-edge artefacts.
    """
    out: list[str] = []
    for raw in text.splitlines():
        line = " ".join(raw.split())
        if not line or not _GREEK_RE.search(line):
            continue
        line = re.sub(r"(?<=[\u0370-\u03ff\u1f00-\u1fff])\s*:", "·", line)
        tokens = line.split(" ")
        while tokens and _STRAY_TOKEN_RE.match(tokens[-1]):
            tokens.pop()
        while tokens and _STRAY_TOKEN_RE.match(tokens[0]):
            tokens.pop(0)
        if tokens:
            out.append(" ".join(tokens))
    return "\n".join(out).strip()
