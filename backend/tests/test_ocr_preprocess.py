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


def test_detect_text_lines_finds_every_rendered_line_with_diacritics():
    page = render_page(LINES, width=1600, font_size=60, margin=120)
    gray = pp.flatten_illumination(np.asarray(page, dtype=np.uint8))
    lines, median = pp.detect_text_lines(gray)
    assert len(lines) == len(LINES)
    assert median > 20
    # Each span must include the accents above the x-height: spans are taller
    # than a bare x-height and do not overlap.
    assert all(e - s > 0.6 * median for s, e in lines)
    assert all(lines[i][1] <= lines[i + 1][0] for i in range(len(lines) - 1))


def test_detect_text_columns_ignores_page_edge_shadow():
    page = np.asarray(render_page(LINES, width=1800, font_size=60, margin=150), dtype=np.uint8).copy()
    page[:, -60:] = 20  # dark page-edge / gutter stripe down the whole height
    x0, x1 = pp.detect_text_columns(page)
    ink_cols = np.nonzero((page[:, :-60] < pp.INK_LEVEL).any(axis=0))[0]
    assert x1 <= page.shape[1] - 60  # stripe excluded
    assert x0 <= ink_cols.min() and x1 >= ink_cols.max()  # text block fully inside


def test_crop_lines_returns_one_image_per_line():
    page = np.asarray(render_page(LINES, width=1600, font_size=60, margin=120), dtype=np.uint8)
    crops = pp.crop_lines(page)
    assert len(crops) == len(LINES)
    assert all(c.shape[1] < page.shape[1] for c in crops)
