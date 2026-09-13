# OCR regression set

Each case is an image plus a `.txt` with the expected polytonic transcription
(same basename). `test_ocr_regression.py` runs the full `/api/ocr` pipeline
(OpenCV preprocessing → Tesseract `grc`) on every image and asserts the
character error rate stays under the threshold in `cases.json`.

Add a case:

1. Drop `athenaze-p12.jpg` (a real phone photo; keep it under ~3 MB) here.
2. Write `athenaze-p12.txt` with the exact printed text, one line per printed
   line, polytonic Unicode (NFC).
3. Add an entry to `cases.json`:
   `{"image": "athenaze-p12.jpg", "source": "Athenaze I p.12", "max_cer": 0.15}`
4. Run `pytest -q tests/test_ocr_regression.py -rs`.

Photos wanted (3–5): Athenaze, LOGOS, Loeb — hand-held phone shots with the
usual problems (slight tilt, shadow, page curvature).

Tests skip (not fail) when Tesseract `grc` is not installed.
