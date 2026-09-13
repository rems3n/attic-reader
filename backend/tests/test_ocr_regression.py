"""Full OCR pipeline (preprocess → Tesseract grc) on the regression images."""

import io
import json
from pathlib import Path

import pytest
from PIL import Image

from app import ocr_preprocess as pp
from app.ocr import recognize_ancient_greek_with_report
from ocr_support import cer, degrade, tesseract_has_grc, to_png_bytes

ROOT = Path(__file__).parent / "ocr_regression"
CASES = json.loads((ROOT / "cases.json").read_text("utf-8"))

pytestmark = pytest.mark.skipif(not tesseract_has_grc(), reason="Tesseract with grc not installed")


def _load_case(case: dict) -> tuple[bytes, str]:
    image_path = ROOT / case["image"]
    expected = (image_path.with_suffix(".txt")).read_text("utf-8")
    data = image_path.read_bytes()
    if case.get("degrade"):
        if not pp.opencv_available():
            pytest.skip("degraded cases need OpenCV preprocessing")
        image = Image.open(io.BytesIO(data))
        data = to_png_bytes(degrade(image, **case["degrade"]))
    return data, expected


@pytest.mark.parametrize("case", CASES, ids=[c["source"][:40] for c in CASES])
def test_ocr_regression(case):
    data, expected = _load_case(case)
    text, report = recognize_ancient_greek_with_report(data)
    rate = cer(expected, text)
    assert rate <= case["max_cer"], (
        f"CER {rate:.3f} > {case['max_cer']} for {case['source']}\n"
        f"report={report}\nexpected:\n{expected}\ngot:\n{text}"
    )


def test_ocr_endpoint_reads_synthetic_sample():
    from fastapi.testclient import TestClient
    from app.main import app

    data = (ROOT / "synthetic-clean.png").read_bytes()
    response = TestClient(app).post("/api/ocr", files={"file": ("page.png", data, "image/png")})
    assert response.status_code == 200
    assert cer((ROOT / "synthetic-clean.txt").read_text("utf-8"), response.json()["text"]) == 0.0
