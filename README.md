# Attic Reader — Ancient Greek read aloud

Photograph or paste polytonic Greek, correct the OCR, and hear it read in reconstructed Classical Attic (c. 400 BC) by a natural neural voice — never Modern Greek phonology.

Mobile-first web app for turning photographed or pasted polytonic Ancient Greek into natural, non-Modern-Greek audio.

## Product flow

1. Take/upload a photo or paste Greek text.
2. OCR with Tesseract's dedicated `grc` Ancient Greek model.
3. Review/edit the recognized polytonic text.
4. Convert the text to a Classical Attic-oriented phoneme sequence.
5. Synthesize with a neural voice while preserving our pronunciation rules.
6. Play the generated WAV in the browser.

OCR, historical pronunciation, and waveform synthesis are deliberately separate. The valuable core is the deterministic Greek → phoneme layer; neural voice backends can be replaced without rewriting OCR or the reader UI.

## TTS strategy

Provider order:

1. **Kokoro + direct Attic phonemes** — primary experiment. Kokoro's `KPipeline.generate_from_tokens()` accepts a raw phoneme string, so we can bypass a Modern Greek/English G2P and feed our own reconstruction directly.
2. **Meta MMS `facebook/mms-tts-grc`** — comparison baseline. It is a dedicated Ancient Greek (`grc`) VITS checkpoint and accepts Ancient Greek orthography directly.
3. **Piper + Attic phonemes** — optional alternative phoneme-controlled neural path.
4. **eSpeak NG `grc`** — diagnostic only and disabled by default because its waveform is too robotic for learning.

Kokoro is especially useful for this experiment because its published token vocabulary contains the IPA symbols used by the current Attic MVP, including `y`, `ɛ`, `ɔ`, `ŋ`, `ː`, `ʰ`, and stress marks. The one mark we currently strip is the combining non-syllabic marker `̯`; e.g. `ai̯` is sent as `ai`.

MMS being labeled Ancient Greek does **not** prove that its learned pronunciation matches 5th–4th century BC Classical Attic. We therefore compare it against the independent Attic G2P rather than treating the model as the authority.

### Licensing note

Kokoro-82M is published under Apache 2.0. The `facebook/mms-tts-grc` checkpoint is CC-BY-NC 4.0, so MMS is useful for personal/non-commercial evaluation but should not be assumed to be an acceptable commercial production backend.

## Architecture

```text
Next.js PWA
   |
   +--> POST /api/ocr --------> Tesseract grc
   |
   +--> POST /api/phonemize --> Classical Attic G2P
   |
   +--> POST /api/segment ----> sentence spans {index, text, start, end}
   |
   +--> GET  /api/library, /api/library/{id} -> built-in Perseus readings
   |
   +--> GET  /api/tts/status -> neural-provider readiness
   |
   +--> POST /api/synthesize        {text, speed?} -> one WAV
   +--> POST /api/synthesize/batch  {text, speed?} -> one base64 WAV per sentence
             |
             +--> Kokoro (Attic phonemes -> neural WAV)
             |
             +--> MMS grc (Greek text -> neural WAV)
             |
             +--> Piper (Attic phonemes -> neural WAV)
             |
             +--> eSpeak grc (diagnostic, opt-in only)
```

## Reading library

`backend/app/library_data/` holds twelve short Attic passages (history,
philosophy, mythology; beginner and intermediate) taken from Perseus Digital
Library editions in [PerseusDL/canonical-greekLit](https://github.com/PerseusDL/canonical-greekLit)
(CC BY-SA 4.0). `python scripts/build_library.py` regenerates them from
`sources.json`. On start the backend warms Kokoro and then pre-renders every
passage at every learner speed into a disk clip cache (`CLIP_CACHE_DIR`,
`/data/clip-cache` on Railway), so a passage chosen in the app plays at once.
The same cache serves repeated user text. Each clip is stored with Kokoro's
per-token durations, from which the app derives word timings and highlights
the word being spoken.

## Vocabulary and grammar

`backend/app/vocab_data/` carries the [DCC Ancient Greek Core Vocabulary](https://dcc.dickinson.edu/greek-core-list)
(524 words, CC BY-SA; `greek-core-list.csv` is the official export). `python
scripts/build_vocab.py` parses it into `core.json`: principal parts split into
slots, genitives and adjective endings expanded, Classical Attic `-ττ-`
spellings, learner tiers by frequency rank, topic tags (mythology / history /
philosophy / city life / core) from the DCC semantic groups and from the
readings the word occurs in, and the library sentences that contain a form of
it. `overrides.json` holds per-word corrections (suppletive stems, notes);
`cognates.json` is a curated map of English derivatives (λόγος → logic,
dialogue) and inherited cognates (πατήρ ~ father) that powers the "English
cognates" deck tag — add or correct entries there and rebuild.

`backend/app/greek/morph/` is a deterministic Classical Attic morphology
engine: every noun, adjective, pronoun and numeral is declined
(`nominal.py`, hand tables in `tables.py`) and every verb is conjugated in
all tenses, moods and voices from its principal parts (`verb.py`,
`verb_endings.py`, irregulars in `verb_tables.py`). `paradigms.py` is the
grammar section: model words with explanations and example sentences. The
gold tables in `backend/tests/test_morph_*.py` are the reference for what
the engine must produce; anything it gets wrong belongs there first.

The app's **Vocab** tab builds a deck by topic, level, part of speech, DCC
group or reading and studies it with spaced repetition (SM-2, in
`frontend/lib/srs.ts`): Greek → English, English → Greek, a forms drill
("λόγος — genitive plural?") and principal parts. Every card and every table
cell can be heard (`POST /api/speak`, cached like everything else). Progress
lives in the browser (`localStorage`); an optional sync code backs it up on
the server (`PUT/GET /api/progress/{code}`, stored under a hash in
`PROGRESS_DIR`) so it can be restored on another device.

API: `GET /api/vocab`, `GET /api/vocab/{id}` (definition, forms, examples),
`GET /api/grammar`, `GET /api/grammar/{id}`, `POST /api/speak`,
`PUT|GET /api/progress/{code}`.

## Quick start

### 1. Backend

Requirements:
- Python 3.11+
- Tesseract 5 with `grc.traineddata` (Debian/Ubuntu: `apt install tesseract-ocr tesseract-ocr-grc`)
- espeak-ng (Kokoro's non-English pipeline imports it even though we inject phonemes)
- Internet access on the first neural-model run unless weights are already cached

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cpu   # CPU wheel; the default pulls ~3 GB of CUDA
pip install -e '.[kokoro,dev]'
uvicorn app.main:app --reload --port 8000
```

Check Ancient Greek OCR support:

```bash
tesseract --list-langs | grep grc
```

Check voice readiness:

```bash
curl http://localhost:8000/api/tts/status
```

Run tests:

```bash
pytest -q
```

Run the fixed neural-voice benchmark:

```bash
python scripts/run_voice_benchmark.py --providers kokoro mms
```

The runner creates `benchmark-output/manifest.json` and one WAV per successful test/provider. The fixed test set lives in `benchmarks/attic_benchmark.json`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. On mobile, the image input requests the rear camera when the browser supports `capture="environment"`.

## Colab benchmark

`experiments/neural_voice_benchmark_colab.ipynb` is included for the specific case where the local machine cannot download neural dependencies/weights. Upload the project ZIP to Colab, run the notebook, and it will:

- install Kokoro and MMS dependencies,
- run the same 15-case benchmark,
- display Kokoro and MMS audio side-by-side,
- package every generated WAV plus the manifest as `ancient-greek-voice-benchmark.zip`.

## Docker

```bash
docker compose up --build
```

The backend image installs Tesseract's Ancient Greek OCR data plus both Kokoro and MMS Python dependencies. Model weights are cached in the `hf-cache` volume.

## Environment

```bash
cp .env.example .env
```

Important settings:

```bash
ENABLE_KOKORO=true
KOKORO_REPO_ID=hexgrad/Kokoro-82M
KOKORO_VOICE=im_nicola
KOKORO_LANG_CODE=i
KOKORO_SPEED=0.85

ENABLE_MMS=false
MMS_MODEL_ID=facebook/mms-tts-grc
MMS_DEVICE=cpu

# Keep robotic speech off for normal use
ALLOW_ESPEAK_FALLBACK=false

# Flash-card progress backups (sync codes); defaults next to the clip cache
PROGRESS_DIR=/data/progress
```

The British male Kokoro voice is only a first benchmark narrator. We are evaluating whether the model can realize the supplied Attic phonemes naturally; voice selection can be changed later without changing the Greek pronunciation engine.

## Benchmark acceptance criteria

The 15-case benchmark explicitly tests:

- Classical stops `b d g` rather than Modern Greek fricatives
- aspirated `pʰ tʰ kʰ`
- `y` for upsilon
- eta/omega vowel quality and length
- rough breathing `h`
- diphthongs
- gamma nasalization before velars
- geminates
- iota-subscript policy
- short Athenaze/Xenophon-style connected passages

A provider is not accepted merely because it produces audio. It must be (1) natural enough for sustained listening and (2) faithful enough that a beginner should be comfortable imitating it.

## Current linguistic status

The custom G2P is an MVP pronunciation audit, not yet a scholarly final reconstruction. It currently handles:

- polytonic Unicode normalization
- rough breathing
- common Classical diphthongs
- long eta/omega
- aspirated theta/phi/chi
- gamma before velars
- double consonants
- lexical accent rendered as stress for learner mode

Next linguistic work after the voice benchmark passes:

- syllabification
- more robust accent scope
- enclitics/proclitics
- elision/crasis
- long diphthongs/iota-subscript policy
- reconstructed pitch accent
- sentence-level comparison against trusted reconstructed-Attic recordings

## Why eSpeak is not learner-facing

eSpeak NG remains useful as a deterministic Ancient Greek diagnostic/reference engine, but its waveform is too robotic for sustained learning. `ALLOW_ESPEAK_FALLBACK=false` is therefore the default. If no neural provider is available, the API fails clearly instead of silently returning low-quality speech.
