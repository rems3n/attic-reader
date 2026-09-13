from __future__ import annotations

import io
import os
import shutil
import subprocess
import tempfile
from dataclasses import asdict

from PIL import Image, ImageFilter, ImageOps

from .ocr_preprocess import PreprocessReport, preprocess


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


def run_tesseract(image: Image.Image, *, psm: int | None = None) -> str:
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
        )

    if proc.returncode != 0:
        raise OCRUnavailable(proc.stderr.strip() or "Tesseract OCR failed")
    return _clean_ocr(proc.stdout)


def recognize_ancient_greek_with_report(data: bytes) -> tuple[str, dict[str, object]]:
    image, report = prepare_image(data)
    return run_tesseract(image), asdict(report)


def recognize_ancient_greek(data: bytes) -> str:
    text, _ = recognize_ancient_greek_with_report(data)
    return text


def _clean_ocr(text: str) -> str:
    lines = [" ".join(line.split()) for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines).strip()
