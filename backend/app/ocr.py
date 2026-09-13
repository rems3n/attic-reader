from __future__ import annotations

import io
import os
import shutil
import subprocess
import tempfile

from PIL import Image, ImageFilter, ImageOps


class OCRUnavailable(RuntimeError):
    pass


def _prepare_image(data: bytes) -> Image.Image:
    image = Image.open(io.BytesIO(data))
    image = ImageOps.exif_transpose(image)
    image = image.convert("L")

    # Modern textbook pages usually benefit from modest enlargement and contrast
    # normalization without aggressive thresholding that can erase breathings.
    if image.width < 2200:
        scale = min(2.0, 2200 / max(image.width, 1))
        image = image.resize(
            (int(image.width * scale), int(image.height * scale)),
            Image.Resampling.LANCZOS,
        )

    image = ImageOps.autocontrast(image, cutoff=1)
    image = image.filter(ImageFilter.SHARPEN)
    return image


def recognize_ancient_greek(data: bytes) -> str:
    command = os.getenv("TESSERACT_COMMAND", "tesseract")
    executable = shutil.which(command)
    if executable is None:
        raise OCRUnavailable(f"Tesseract executable not found: {command}")

    image = _prepare_image(data)

    with tempfile.NamedTemporaryFile(suffix=".png") as temp:
        image.save(temp.name, format="PNG")
        proc = subprocess.run(
            [
                executable,
                temp.name,
                "stdout",
                "-l",
                "grc",
                "--psm",
                "6",
                "--oem",
                "1",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

    if proc.returncode != 0:
        raise OCRUnavailable(proc.stderr.strip() or "Tesseract OCR failed")

    return _clean_ocr(proc.stdout)


def _clean_ocr(text: str) -> str:
    lines = [" ".join(line.split()) for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines).strip()
