FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# tesseract-ocr-grc: Ancient Greek OCR data. espeak-ng: required by Kokoro's
# non-English pipelines (lang_code "i") even though we inject our own phonemes.
# libglib2.0-0 + libgomp1: runtime deps of the opencv-python-headless wheel on
# a slim image (without them `import cv2` fails and OCR silently degrades).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
         tesseract-ocr tesseract-ocr-grc espeak-ng libgomp1 libglib2.0-0 curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# tessdata_best grc (LSTM float model) reads polytonic pages slightly better
# than the Debian-packaged 2019 model; ~5 MB.
RUN curl -fsSL -o /usr/share/tesseract-ocr/5/tessdata/grc.traineddata \
      https://raw.githubusercontent.com/tesseract-ocr/tessdata_best/main/grc.traineddata

WORKDIR /app
COPY pyproject.toml /app/pyproject.toml
COPY app /app/app

# CPU torch wheel first: the default PyPI wheel drags in ~3 GB of CUDA libraries
# that a CPU host cannot use. MMS (transformers) is not installed: it is
# rejected for Modern Greek phonology and disabled by default.
RUN python -m pip install --upgrade pip \
    && python -m pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && python -m pip install --no-cache-dir '.[kokoro]' \
    && python -c "import cv2, kokoro; print('cv2', cv2.__version__)"

# Railway/Fly/Render inject $PORT; default to 8000 locally.
ENV PORT=8000 \
    HF_HOME=/data/hf-cache \
    ENABLE_MMS=false
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
