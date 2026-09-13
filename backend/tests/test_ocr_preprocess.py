import numpy as np
import pytest

from app import ocr_preprocess as pp
from ocr_support import degrade, render_page, to_png_bytes

LINES = [
    "ὁ Δικαιόπολις αὐτουργός ἐστιν.",
    "ἐν τοῖς ἀγροῖς οἰκεῖ καὶ πονεῖ.",
    "Ἐπεὶ δὲ ὁ Κῦρος ἐτελεύτησε,",
    "Τισσαφέρνης διαβάλλει τὸν Κῦρον.",
]

pytestmark = pytest.mark.skipif(not pp.opencv_available(), reason="OpenCV not installed")


@pytest.mark.parametrize("angle", [3.0, -2.5, 6.0])
def test_estimate_skew_recovers_rotation(angle):
    page = degrade(render_page(LINES), rotate=angle)
    gray = np.asarray(page, dtype=np.uint8)
    assert pp.estimate_skew(gray) == pytest.approx(angle, abs=0.3)


def test_estimate_skew_is_zero_for_straight_page():
    gray = np.asarray(render_page(LINES), dtype=np.uint8)
    assert abs(pp.estimate_skew(gray)) <= 0.2


def test_preprocess_deskews_and_reports():
    data = to_png_bytes(degrade(render_page(LINES), rotate=3.0, shade=True, noise=5))
    image, report = pp.preprocess(data)
    assert report.engine == "opencv"
    assert report.deskewed is True
    assert report.skew_degrees == pytest.approx(3.0, abs=0.3)
    assert image.mode == "L"
    # After correction the residual tilt is negligible.
    assert abs(pp.estimate_skew(np.asarray(image))) <= 0.3


def test_preprocess_flattens_uneven_lighting():
    shaded = degrade(render_page(LINES), shade=True)
    before = np.asarray(shaded, dtype=np.float32)
    image, _ = pp.preprocess(to_png_bytes(shaded), deskew=False)
    after = np.asarray(image, dtype=np.float32)
    # Compare the paper brightness on the far left vs far right margin strips.
    def margin_gap(a):
        h, w = a.shape
        left = np.median(a[:, : w // 20])
        right = np.median(a[:, -w // 20 :])
        return abs(left - right)
    assert margin_gap(before) > 60
    assert margin_gap(after) < 12


def test_preprocess_upscales_small_photos():
    small = render_page(LINES[:1], width=700, font_size=28, margin=30)
    image, report = pp.preprocess(to_png_bytes(small), deskew=False)
    assert max(image.size) >= pp.TARGET_LONG_SIDE - 2
    assert report.scale > 1.0


def test_preprocess_falls_back_to_pillow_without_opencv(monkeypatch):
    monkeypatch.setattr(pp, "cv2", None)
    image, report = pp.preprocess(to_png_bytes(render_page(LINES[:1])))
    assert report.engine == "pillow"
    assert image.mode == "L"
