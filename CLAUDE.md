# Ancient Greek Reader — Handoff Plan

## Read this first

You are taking over an in-progress prototype for a mobile/web Ancient Greek reading app.

The user is a beginner learning Ancient Greek with **Athenaze** and **LOGOS / Lingua Graeca per se illustrata** and wants to read texts such as **Xenophon**. The key requirement is audio that sounds natural **without sounding like Modern Greek**.

The current target is:

> **Reconstructed Classical Attic, roughly Athens c. 400 BC, optimized first for a learner.**

The user initially mentioned Erasmian pronunciation, but that is not the actual requirement. Do not optimize around a generic national-school “Erasmian” convention. The user mainly wants pronunciation appropriate to Classical Attic/Athenaze/Xenophon and clearly distinct from Modern Greek.

The user cannot yet speak Ancient Greek reliably, so **do not require pronunciation recordings from the user**. The app should teach the user, not learn pronunciation from him.

The desired product flow is:

```text
Photo of physical book OR pasted Greek text
        ↓
Ancient Greek OCR
        ↓
Editable/reviewable polytonic Greek
        ↓
Deterministic Classical Attic G2P
        ↓
Natural neural TTS
        ↓
Sentence-level playback in a mobile-friendly web app
```

The user rejected the eSpeak result as far too robotic. Do not return to eSpeak as a learner-facing solution.

---

# Product requirements

## MVP user experience

The app should work on desktop and mobile, preferably as a PWA.

A user should be able to:

1. Take a photo of printed Ancient Greek on a phone.
2. Upload an existing image.
3. Paste polytonic Greek copied from the web.
4. See OCR output before synthesis.
5. Correct OCR errors manually.
6. Generate natural-sounding Ancient Greek audio.
7. Play/replay the result easily.
8. Eventually play sentence-by-sentence and change playback speed.

For v1, do **not** overbuild accounts, saved books, billing, social features, etc. Voice quality is the core blocker.

## Non-negotiable pronunciation goals

The output must not silently fall back to Modern Greek phonology. The current Classical Attic learner target includes, approximately:

- β → /b/
- γ → /g/
- δ → /d/
- θ → /tʰ/
- φ → /pʰ/
- χ → /kʰ/
- η → /ɛː/
- ω → /ɔː/
- υ → /y/
- αι → /ai̯/
- οι → /oi̯/
- αυ → /au̯/
- ευ → /eu̯/
- rough breathing → /h/
- γγ → /ŋg/
- γκ → /ŋk/
- γχ → /ŋkʰ/
- gamma before ξ → nasalized velar sequence
- preserve relevant vowel length and geminates

The exact historical policy for ει, ου, long diphthongs, iota subscript, ζ, pitch accent, and some period-sensitive details is **not final**. Treat the current G2P as an MVP that must be audited, not as scholarly ground truth.

Current learner mode renders lexical accent primarily as stress. Reconstructed pitch accent is a later feature.

---

# Current architecture

```text
frontend/                 Next.js + TypeScript + mobile-first UI
     |
     +--> POST /api/ocr
     |         ↓
     |      Tesseract `grc`
     |
     +--> POST /api/phonemize
     |         ↓
     |      deterministic Attic G2P
     |
     +--> GET /api/tts/status
     |
     +--> POST /api/synthesize
               ↓
        neural-provider adapter
               ↓
        Kokoro first
        MMS comparison
        Piper optional experiment
        eSpeak diagnostic only
```

Backend is Python/FastAPI. Frontend is Next.js.

The important design choice is that **Greek → phonemes is separate from phonemes → waveform**. Preserve that separation.

---

# Repository map

## Important files

- `README.md` — setup and architecture overview.
- `CLAUDE.md` — this handoff document.
- `.env.example` — TTS/OCR configuration.
- `docker-compose.yml` — local Docker path.
- `benchmarks/attic_benchmark.json` — fixed 15-case voice/pronunciation benchmark.
- `benchmark-output/manifest.json` — last benchmark attempt; currently contains provider-install errors rather than neural WAVs.
- `experiments/neural_voice_benchmark_colab.ipynb` — intended easiest way to download/run Kokoro + MMS in an internet-enabled environment.
- `experiments/mms_grc_voice_test.ipynb` — earlier MMS-specific notebook.

## Backend

- `backend/app/greek/g2p.py` — current deterministic Classical Attic G2P MVP.
- `backend/app/greek/normalize.py` — Unicode/polytonic normalization.
- `backend/app/ocr.py` — Tesseract Ancient Greek OCR.
- `backend/app/tts/kokoro.py` — preferred direct-phoneme neural experiment.
- `backend/app/tts/mms.py` — Meta MMS Ancient Greek comparison.
- `backend/app/tts/piper.py` — optional raw-phoneme Piper path.
- `backend/app/tts/espeak.py` — robotic diagnostic fallback only.
- `backend/app/tts/providers.py` — provider priority/fallback logic.
- `backend/scripts/run_voice_benchmark.py` — produces a WAV per benchmark/provider plus manifest.
- `backend/tests/` — current automated tests.

## Frontend

- `frontend/app/page.tsx` — current single-page workflow.
- `frontend/lib/api.ts` — backend calls.
- `frontend/app/manifest.ts` — PWA metadata baseline.

---

# Current status

## What is working

### 1. Classical Attic G2P MVP

There is a deterministic rule-based phonemizer in `backend/app/greek/g2p.py`.

It currently handles:

- polytonic Unicode decomposition/normalization
- rough breathing
- common diphthongs
- eta/omega as long vowels
- classical stop values for β/γ/δ
- aspirated θ/φ/χ
- upsilon /y/
- gamma nasalization before velars
- geminates through repeated graphemes
- a provisional iota-subscript policy
- lexical accent rendered as learner-friendly stress

### 2. Ancient Greek OCR path

The project uses Tesseract’s dedicated `grc` trained data, not Modern Greek `ell`.

A synthetic polytonic Greek image was successfully OCR’d exactly in the development environment. That proves the basic pipeline, but **real physical-book photos still need systematic testing** under perspective distortion, uneven lighting, page curvature, small type, Loeb formatting, etc.

### 3. FastAPI endpoints

Implemented:

- `GET /health`
- `POST /api/ocr`
- `POST /api/phonemize`
- `GET /api/tts/status`
- `POST /api/synthesize`

### 4. Mobile-first frontend

The Next.js UI currently supports:

- camera/image upload
- paste/edit Greek text
- OCR
- pronunciation preview
- audio generation
- audio playback
- display of G2P audit output
- provider status

### 5. Automated tests

At handoff time:

```text
14 passed
```

Run from `backend/`:

```bash
pytest -q
```

### 6. Benchmark suite

`benchmarks/attic_benchmark.json` contains 15 tests covering:

- aspirates
- classical stops
- long vowels
- upsilon
- rough breathing
- αι / οι / αυ / ευ
- gamma nasalization
- geminates
- iota subscript policy
- short Athenaze-style phrases
- Xenophon-style passages

---

## Session log — 2026-09-12 (neural voice milestone)

- 45 neural WAVs now exist in `benchmark-output/` (15 cases × Kokoro/bm_george, Kokoro/im_nicola, MMS-grc). See `benchmark-output/SCORECARD.md` and `listening_sheet.html`.
- MMS grc is **REJECTED** on objective grounds: phone recognition shows Modern Greek phonology on every case. Do not spend more time on it.
- Kokoro raw-phoneme injection **works** and provisionally passes the Classical contrasts (stops, aspiration duration, long vowels, geminates, /h/, diphthongs, /zd/).
- Bug fixed: ASCII `g` was not in Kokoro's vocab, so every γ was silently dropped. Fixed in the provider mapping layer + tests (16 passing).
- Open issue: English voices insert a linking-R after ɛː/ɔː before a vowel. `im_nicola` (Italian) does not, and renders /y/ and /h/ correctly — leading voice candidate.
- `run_voice_benchmark.py` now takes `--voices`; manifest keys are consistently provider IDs on success and failure.
- Install notes: use the CPU torch wheel on small-disk hosts (`--index-url https://download.pytorch.org/whl/cpu`); `KPipeline(lang_code="b")` needs spaCy `en_core_web_sm` even though we bypass G2P.
- **User listened (2026-09-12): voice quality accepted.** Liked im_nicola and bm_george; chose **im_nicola** as the default to stay focused. MMS confirmed rejected.
- Defaults now `KOKORO_VOICE=im_nicola`, `KOKORO_LANG_CODE=i` (README, .env.example, docker-compose, kokoro.py).

# What has NOT been proven yet

This is the most important section.

## 1. No neural voice has passed the listening benchmark yet

The prior execution environment could not download/install the required neural packages/model weights. Therefore:

- **Kokoro has not yet been heard with our Classical Attic phoneme strings.**
- **MMS Ancient Greek has not yet been heard in this project benchmark.**
- Do not claim either model has passed.

The current `benchmark-output/manifest.json` intentionally records errors such as “Kokoro is not installed” / “MMS is not installed.”

## 2. Kokoro raw-phoneme compatibility is an implementation hypothesis, not final proof

The project uses `KPipeline.generate_from_tokens()` in `backend/app/tts/kokoro.py` to bypass Kokoro’s normal G2P and inject our phoneme string.

The reasoning is good: Kokoro’s token set appears to contain many symbols needed by our MVP, and direct phoneme control is ideal.

But the actual acoustic result must be tested. A model can accept symbols without producing convincing Classical Greek timing or coarticulation.

Pay particular attention to:

- /y/
- /ɛː/
- /ɔː/
- /pʰ tʰ kʰ/
- vowel quantity
- geminate duration
- diphthongs
- /ŋ/ + velar sequences
- whether stress marks create bizarre English-like prosody

## 3. MMS pronunciation may be wrong for the target period

`facebook/mms-tts-grc` is useful because it is a dedicated Ancient Greek model and likely sounds much more natural than eSpeak.

However, “Ancient Greek” in a model label does not establish 5th–4th century BC Classical Attic pronunciation. It must be evaluated independently.

Also note licensing: the MMS checkpoint is CC-BY-NC 4.0 and should not be assumed suitable for a commercial product.

## 4. Frontend production build has not been fully validated in the original sandbox

The frontend source exists, but the prior environment had npm/network limitations. Run `npm install`, `npm run build`, and fix any TypeScript/Next.js issues before deployment.

## 5. Real-book OCR quality is not validated

Synthetic OCR worked. Real photos from Athenaze/LOGOS/Loeb are a separate test.

---

# Immediate next steps — do these in order

## Step 1 — Run the existing code before changing architecture

From `backend/`:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e '.[kokoro,mms,dev]'
pytest -q
```

Verify Tesseract Ancient Greek:

```bash
tesseract --list-langs
```

Confirm `grc` appears.

Then run:

```bash
python scripts/run_voice_benchmark.py --providers kokoro mms
```

If local model download/setup is painful, use `experiments/neural_voice_benchmark_colab.ipynb` instead.

## Step 2 — Produce actual neural WAVs

Success means `benchmark-output/` contains WAV files for the benchmark cases, not just errors in `manifest.json`.

Do not proceed to substantial UI work until actual neural audio exists.

## Step 3 — Evaluate Kokoro and MMS separately on two dimensions

For every provider, distinguish:

### A. Naturalness

- Does it sound like a human narrator?
- Can someone listen for several minutes without “robot voice” fatigue?
- Is pacing calm and pedagogical rather than announcer-like or English-like?

### B. Pronunciation fidelity

- Are β/γ/δ stops rather than Modern Greek fricatives?
- Are θ/φ/χ aspirated stops rather than modern fricatives?
- Is upsilon plausibly /y/?
- Are rough breathings audible?
- Are η/ω distinct and plausibly long?
- Are diphthongs preserved?
- Are geminates/durations plausible?

A provider passes only if it is acceptable on both dimensions.

## Step 4 — Prefer Kokoro only if raw phoneme injection actually sounds good

If Kokoro produces natural audio from our phoneme strings, make it the primary backend.

Then:

- choose 2–4 candidate voices, not just `bm_george`
- benchmark a male and female voice
- tune speed and punctuation
- evaluate whether stress marks should be removed/changed
- test duration control for long vowels and geminates
- validate chunks/pauses across sentence boundaries

Do not optimize for sounding specifically like Luke Ranieri’s identity/voice. The user likes the high-level qualities of his recordings: reconstructed Classical pronunciation, deliberate scholarly narration, clarity, and pedagogical pacing. Use a distinct synthetic voice unless permission exists for an actual clone.

## Step 5 — If Kokoro fails phonetic fidelity, do not endlessly patch it

Try the following decision tree:

```text
Kokoro raw phonemes natural + faithful?
  ├─ YES → use Kokoro for MVP
  └─ NO
      ↓
MMS natural + sufficiently Classical?
  ├─ YES (personal prototype only) → use as temporary prototype
  └─ NO
      ↓
Test another phoneme-controllable open neural backend / Piper
      ↓
If still poor → train/fine-tune a dedicated Classical Attic voice
```

The value already built is the deterministic G2P + OCR + app shell. Replacing TTS should not require rewriting those pieces.

## Step 6 — Audit and harden the G2P after the acoustic backend proves viable

Do not mistake the current G2P for a finished scholarly reconstruction.

Recommended linguistic backlog:

1. formalize the exact target period (late 5th / early 4th c. BC Attic)
2. syllabification
3. distinguish vowel length more systematically
4. revisit ει / ου policy by period/context
5. revisit ζ reconstruction
6. long diphthongs / iota subscript policy
7. word-final and cross-word sandhi
8. elision and crasis
9. enclitics/proclitics
10. phrase-level accent/prosody
11. eventually add reconstructed pitch-accent mode

Keep two modes:

- **Learner:** clear word boundaries, slower pacing, stress-like accent cue, exaggerated quantity where useful.
- **Reconstructed/Natural:** more historical connected speech and pitch-accent behavior.

## Step 7 — Test OCR on real pages

Ask for or use representative photos from:

- Athenaze
- LOGOS / Cultura Clásica
- Loeb Xenophon

Build a small OCR regression set with expected transcription.

Add preprocessing as needed:

- crop/page detection
- grayscale/contrast
- deskew
- perspective correction
- denoise/sharpen only if it helps

If Tesseract `grc` is insufficient, evaluate Kraken and specialized polytonic Greek OCR models.

## Step 8 — Finish product experience only after voice passes

Next UX features, in order:

1. sentence segmentation
2. one-tap play/replay sentence
3. 0.6x / 0.75x / 1x / 1.25x playback
4. synchronized sentence highlighting
5. “repeat sentence” learning mode
6. preserve source text + generated audio locally
7. saved reading library
8. optional word-tap pronunciation later

No auth is needed until saving/syncing becomes important.

---

# Known code issues / cleanup items

These are not necessarily blockers but should be checked.

## Frontend messaging

The frontend was updated in this handoff to describe Kokoro as the preferred phoneme-controlled path. Verify there are no stale MMS-first messages elsewhere.

## Benchmark manifest keys

On failure, `run_voice_benchmark.py` currently stores errors under the requested short provider key (`kokoro`, `mms`), whereas successful files are stored under provider IDs (`kokoro-attic`, `mms-grc`). This is acceptable for now but should be normalized if a consumer parses the manifest.

## Kokoro API compatibility

Confirm the installed Kokoro version still supports the exact `KPipeline` constructor and `generate_from_tokens()` signature used in `backend/app/tts/kokoro.py`.

If the library API changed, update the adapter rather than changing the G2P architecture.

## Prosody and tokenization

`split_phonemes()` chunks by character count and punctuation. This is a prototype. Once audio works, chunk by sentence/phrase and perhaps syllable/phoneme token count rather than raw characters.

## IPA is not necessarily the model’s ideal token representation

The project calls the output “IPA,” but a neural model may respond better to a model-specific phoneme spelling while preserving the same historical distinctions. It is fine to add a provider-specific phoneme mapping layer:

```text
Greek → canonical Attic representation → provider-specific token mapping → waveform
```

Do not contaminate the canonical linguistic representation just to satisfy one TTS model.

---

# Acceptance criteria for the voice milestone

Before calling the core problem solved, all of these should be true:

- [ ] 15 benchmark cases generate neural WAVs reliably.
- [ ] Voice sounds natural enough for sustained reading.
- [ ] No obvious Modern Greek β/γ/δ/θ/φ/χ behavior.
- [ ] Rough breathing is represented where expected.
- [ ] Upsilons and major vowel/diphthong distinctions are usable for learning.
- [ ] Long vowels do not collapse entirely into short ones.
- [ ] Geminates are at least perceptibly distinct or handled by a documented learner policy.
- [ ] Athenaze-style full sentence sounds coherent, not like isolated phoneme concatenation.
- [ ] Xenophon-style sentence remains intelligible and natural across clauses.
- [ ] User listens to samples and explicitly says the voice quality is acceptable.

The final acceptance test is subjective: **the user must want to listen to it.** The prior eSpeak sample failed this immediately.

---

# Deployment target after voice validation

Preferred MVP deployment:

- Next.js frontend: Vercel or equivalent
- FastAPI/TTS backend: container host with enough RAM/CPU (or GPU if needed)
- model cache persisted between starts
- no login initially
- no permanent photo storage initially
- PWA installable on iPhone/Android

If the chosen TTS backend is light enough, consider a single container deployment for simplicity.

---

# Safety / licensing / data notes

- Do not clone Luke Ranieri or another identifiable person’s voice without permission.
- It is fine to target high-level non-identifying qualities such as scholarly narration, slow pedagogical pacing, clear articulation, and reconstructed Classical Attic pronunciation.
- Kokoro is the preferable licensing direction for a product if technically successful; verify exact model/code licenses at implementation time.
- MMS `facebook/mms-tts-grc` is currently treated as a non-commercial evaluation baseline.
- Ancient Greek source text such as Xenophon is public-domain text, but do not ship copyrighted modern translations or scan entire copyrighted editions into the product.
- For photo OCR, default to transient processing and avoid storing user book photos unless the product later needs a saved library and the user opts in.

---

# Recommended first session for the next agent

Do not redesign the app first.

Do this:

```text
1. Read README.md and this file.
2. Run backend tests.
3. Install Kokoro + MMS dependencies.
4. Run the 15-case benchmark.
5. Fix any Kokoro adapter API mismatch.
6. Generate WAVs.
7. Compare Kokoro vs MMS.
8. Make a provider decision based on naturalness + Classical fidelity.
9. Only then improve G2P/prosody/UI.
```

If internet/model downloads are available, the most useful concrete deliverable is a folder containing the 15 Kokoro WAVs, 15 MMS WAVs, the manifest, and a short scorecard of which phonetic contrasts each model passed or failed.

---

# User-facing definition of done for the MVP

A beginner can open the site on an iPhone, photograph a paragraph from Athenaze or Xenophon, correct any OCR errors, press one button, and hear a natural human-like reading in a defensible Classical Attic learner pronunciation that does not sound Modern Greek.

---

## Session log — 2026-09-13 (publish + learner experience)

- Repo published: https://github.com/rems3n/attic-reader (work on branch
  `claude/attic-reader-handoff-wvfavt`; `main` not pushed by the agent).
- **Environment limits in that session:** the sandbox egress policy blocked
  `download.pytorch.org` and `huggingface.co`, so Kokoro could not run there.
  Synthesis is covered by tests with a fake pipeline (`tests/conftest.py`);
  real audio must be checked on the deployed backend or a local machine.
- New API: `POST /api/segment`; `POST /api/synthesize` takes `{text, speed?}`
  (speed = learner multiplier 0.5–1.5 on `KOKORO_SPEED`);
  `POST /api/synthesize/batch` returns one base64 WAV per sentence with span,
  IPA and duration. `split_phonemes()` is now one chunk per sentence.
- Frontend: sentence list player (tap to play, ▶/■, play all with highlight,
  0.6/0.75/1/1.25× with neural re-render per speed, repeat toggle), single
  `<audio playsinline>`, fixed bottom bar with safe-area padding. PWA:
  icons, standalone metadata, theme colour. Memory only, no storage.
- OCR: `app/ocr_preprocess.py` (OpenCV shading removal, CLAHE, median
  denoise, projection-profile deskew) behind `/api/ocr`;
  `tests/ocr_regression/` harness with CER threshold per case. Only the
  synthetic sample is in it — **real Athenaze / LOGOS / Loeb photos still
  needed** before judging Tesseract vs Kraken.
- Deploy: Dockerfile installs CPU torch and drops the MMS extra. **Deployed
  on Railway** (project `attic-reader`, services `backend` + `web`, both from
  the handoff branch): https://web-production-a1ef.up.railway.app and
  https://backend-production-d55b3.up.railway.app. Vercel not used yet.
  The sandbox could not reach `*.up.railway.app`, so the end-to-end audio
  smoke test on the deployed URL is the user's to confirm.
- **OCR on a real page (Loeb Memorabilia 1.1, iPhone photo)**: first attempt
  on the deployed app was garbage. Root cause was *not* preprocessing but
  Tesseract's layout stage: on polytonic text it splits rows of accents off as
  separate "lines", and whether it does so flips chaotically with image scale
  (CER 0.03 → 0.65 between neighbouring resolutions; a 4032-px phone upload
  hit the bad case). Fix (`app/ocr_preprocess.py` + `app/ocr.py`): detect
  text lines from the ink profile (fixed ink level 110 on the flattened
  image; accent rows merged into their line; page-edge shadow excluded by a
  column crop) and recognise each line with `--psm 7` in a thread pool with
  `OMP_THREAD_LIMIT=1` (Tesseract's OpenMP makes parallel runs take minutes).
  Result: CER 0.028–0.047 across 1200–4032 px uploads, ~1–2.5 s/page. The
  Loeb photo is now a regression case (`max_cer` 0.06). Remaining misses:
  the all-caps title, a few breathings (οὓς→οὗς), line-start artefacts.
- **First Generate on the deployed app timed out**: the batch request took
  121 s server-side (HF download + model load + 10 sentences on CPU) and iOS
  Safari aborts silent requests at ~60 s (499 in the Railway proxy log). Fix:
  (1) Kokoro warm-up thread at startup (`KOKORO_WARMUP`, default on; status
  note shows `model cold|warming|ready`); (2) `POST /api/synthesize/stream`
  (NDJSON: start / clip per sentence / done) and the frontend consumes it,
  so the first sentence is tappable within seconds and rows fill in as they
  render. Per-sentence timing (`rtf`) is logged; check it after the next
  deploy to know the real CPU speed on Railway.
- **User feedback: reading too fast.** Base pace `KOKORO_SPEED` 0.92 → 0.85
  (code, docs, Railway variable); selector is now 0.5× / 0.6× / 0.75× / 1×
  with 0.75× the default (nothing faster than 1× offered). Effective Kokoro
  speed at the default is 0.64. Warm-up log on Railway: pipeline load 24.5 s,
  first synthesis ~87 s (!) — first-synthesis cost on this host needs a look
  (`attic.*` loggers are now INFO so per-sentence `rtf` lines appear).
- **Reading library** (user request): 12 Attic passages (4 history, 4
  philosophy, 4 mythology; beginner/intermediate) from Perseus TEI editions
  via `scripts/build_library.py` + `app/library_data/sources.json` →
  `app/library_data/*.json` (committed). Plato dialogues keep speaker
  labels as "Σωκράτης: …" lines (Perseus `<said who>`); a colon, not ano
  teleia, so the label does not become its own sentence. `GET /api/library`,
  `GET /api/library/{id}`. Disk **clip cache** (`app/tts/clip_cache.py`,
  key = provider|voice|model speed|phonemes, dir `/data/clip-cache`) used by
  all Kokoro rendering; **pre-render job** (`app/tts/prerender.py`) runs
  after warm-up over passages × speeds (0.75 first), yielding to user
  requests via a render lock + pending counter. Frontend: "Choose a reading"
  card with tabs, level badges, "ready" marker, attribution line. Herodotus /
  Homer deliberately excluded (not Attic) per user; Aesop is not in
  canonical-greekLit.
- **Spoken-word highlighting** (user request): Kokoro returns `pred_dur`
  (frames per input token: BOS + one per phoneme char + EOS); audio samples
  ≈ frames × hop, so `app/tts/timing.py` scales cumulative frames to the
  clip length and maps space-separated phoneme tokens onto the Greek words
  of the sentence (same order; punctuation-only tokens skipped; any count
  mismatch → no highlight rather than a wrong one). Stream `clip` events
  carry `words: [{start, end, t0, t1}]` (offsets into the sentence text).
  Clip cache stores `pred_dur` in a `.json` sidecar; key version bumped to
  v2, so the library re-renders once after deploy. Frontend renders word
  spans and follows `audio.currentTime` with requestAnimationFrame.
- Not started: Step 6 G2P audit (syllabification, ει/ου policy). Still want
  Athenaze / LOGOS photos for the regression set.

## Session log — 2026-09-14 (vocabulary, morphology, grammar)

- User request: flash cards with spaced repetition + grammar tables from the
  DCC Greek Core List, categorised by topic/level/frequency, all forms, and
  the ability to focus on mythology / history / philosophy / city life.
  Decisions with the user: progress in the browser + optional **sync code**
  backup on the server (no accounts); **complete** verb tables; DCC glosses
  from the official CSV (the user uploaded it; `dcc.dickinson.edu` is
  egress-blocked from the sandbox). Nothing new costs money.
- Lexicon: `backend/app/vocab_data/greek-core-list.csv` (official export,
  CC BY-SA) → `scripts/build_vocab.py` → `core.json` (524 entries).
  Parser handles DCC's abbreviated endings (`–ου`, `–ή –όν`), principal-part
  labels, alternatives, Koine `-σσ-` → Attic `-ττ-` (θάλαττα, πράττω,
  τέτταρες). Quirks: two words share rank 384 and no 385; στρατιώτης and
  ποιητής are labelled 2nd declension by DCC (overridden to 1st);
  πᾶς/πολύς/μέγας are filed under nouns (overridden to adjectives).
  `overrides.json` is keyed by rank. Topics come from the DCC semantic
  group (rules in `build_vocab.py`) plus the category of any reading the
  word occurs in; 264 of 524 words occur in the 12 passages and carry the
  matching sentences as examples.
- Morphology engine `backend/app/greek/morph/`: `accent.py` (syllables,
  persistent/recessive accent, law of limitation, final -αι/-οι short except
  in the optative, macrons used internally for hidden length),
  `nominal.py` + `tables.py`, `verb.py` + `verb_endings.py` +
  `verb_tables.py`, `paradigms.py` (grammar section, 67 model paradigms with
  examples). Uses `greek-accentuation` only for syllabification. Known
  simplifications: no dual; perfect subjunctive/optative shown periphrastic;
  consonant-stem perfect middle 3 pl periphrastic; contract futures assumed
  for `-ῶ`/`-οῦμαι` futures; long vowels of a few stems hard-coded
  (`LONG_STEMS`, `LONG_VERB_STEMS`). Suppletive/odd verbs get `verb`
  overrides (`aorist_stem`, `aorist_passive_stem`, `no_augment`,
  `contract: "eta"`, `deponent`, `tables` = hand tables per tense/voice/mood).
  ~190 gold cells for nouns/adjectives/pronouns and ~150 for verbs in
  `tests/test_morph_nominal.py` / `test_morph_verb.py`; every entry must
  conjugate/decline without error. Forms are labelled "generated" in the UI
  with a request to report errors.
- API: `/api/vocab`, `/api/vocab/{id}` (forms + examples), `/api/grammar`,
  `/api/grammar/{id}`, `POST /api/speak` (single word/phrase WAV, ≤300
  chars, clip-cached), `PUT/GET /api/progress/{code}` (`app/progress.py`,
  sha256(code).json under `PROGRESS_DIR`, 2 MB cap). Pre-render job now also
  renders the 524 headwords at 0.75× after the library.
- Frontend: `components/AppNav.tsx` (Read · Vocab · Grammar, sticky),
  `app/vocab/page.tsx` (deck builder chips → SM-2 study session; card types
  recognition / production (optional typed answer, accent-insensitive) /
  forms drill / principal parts; settings: new per day, card types, sync
  code push/pull, JSON export/import, reset), `app/vocab/[id]/page.tsx`
  (word page: FormsTable with tap-to-speak, examples with "open in reader"
  deep link `/?reading=<id>&sentence=<n>`), `app/grammar/`,
  `lib/srs.ts` (pure, vitest-tested: `npm test`), `lib/progress.ts`
  (`localStorage` key `attic.srs.v1`, merge = newer `updated` per card).
- Verified locally end to end with the fake-Kokoro API and headless
  Chromium (`scratchpad/e2e_vocab.py`): deck filters, study/grade, persistence
  across reload, sync push → clear → pull, word/verb pages, grammar,
  deep link. Backend tests: 337 passing; frontend: 6 vitest.
- Not done / next: real-voice check of single-word clips on Railway (the
  headword pre-render adds ~524 short clips after the library);
  dual number; ἵστημι/τέθνηκα short perfect forms are notes only.
- **English cognates tag** (user request, same day): `vocab_data/cognates.json`
  (lemma → `derivatives` = English words from the Greek word, `cognates` =
  inherited IE relatives; 301 words) → `entry.cognates`, `entry.tags =
  ["cognates"]`, facet `tags` (`vocab.TAGS`). Deck builder "Extras" chip,
  cognate line on card backs and word pages. Curated by hand — correct there.
- **Proofread of generated forms** (user request): all 524 entries' tables
  dumped and read against Smyth/LSJ. Nominal fixes: γῆ hand table; nominative
  and vocative = lemma (πρᾶξις) and hidden length kept in acc/voc sg
  (πρᾶξιν); `ADVERB_OVERRIDE` (πρότερον, μακράν, πάλαι, ἰδίᾳ, none for
  νέος/φίλος…), `NO_COMPARISON_EXTRA`, `NO_VOCATIVE` (ἕκαστος, ἐμός…).
  Verb fixes: εἰ-augment (εἴων, εἰργαζόμην, εἱπόμην), pluperfect stems of
  compounds (συνεβεβήκη, κατειλήφη, ἀπωλωλέκη, ἀφίγμην; prefix shape chosen
  by the simplex's initial, breathing restored), macrons survive `join` →
  `_floor` (ἀφῖγμαι), sigma-aorist stem override `aorist_stem_1` (ἆραι,
  κρῖναι), `aorist_stem`/`no_augment`/`imperfect_stem`/`pluperfect_stem`
  overrides, alias entries (εἶδον → ἰδών), σχές/παράσχες, no aorist middle
  for ἀπόλλυμι/ἀποθνῄσκω. Lemma-keyed overrides allowed (θνῄσκω shares rank
  384). 21 new verb gold tables + γῆ/πρᾶξις; 360 backend tests.
- **Speak button on every card** (user request): ▶ on the front of
  recognition / forms / principal-parts cards and on the back of production
  cards; each alternative form and each principal part is its own ▶ chip
  (`SpeakList`); verbs get "▶ all parts" (whole headword); ▶ in the word
  list; ▶ never flips the card. Setting "Speak cards automatically" (off by
  default; iOS may block the first auto-play until a tap) speaks the Greek
  when a card appears and the answer on reveal.
- **Study UX** (user request): session is shuffled (`shuffleSession` in
  `lib/srs.ts`, Fisher–Yates + a pass that keeps the two directions of one
  word apart); "Test" chips on the deck screen choose Greek → English /
  English → Greek / Both (+ Forms drill, + Principal parts as extras);
  "Cards this session" slider + number (`settings.sessionSize`, default 20;
  `pickSession` now takes a total size — due cards first, never dropped for
  new ones). The daily new-card limit is gone; old settings documents are
  migrated (`migrateSettings` in `lib/progress.ts`). Revealed cards show one
  example sentence from the readings (`CardExample`: shortest ≤ 160 chars,
  form highlighted, ▶, source) — only the 264 words that occur in the 12
  passages have one; the rest show nothing (hand-written examples would be
  the next step). Shared `components/Highlight.tsx`.


## Session log — 2026-09-25 (course plan)

- User request: a trackable beginner course (Athenaze / LOGOS / Reading
  Greek style) with lessons, exercises, quizzes, tests, interest tracks
  (mythology, philosophy, history, politics) and images throughout.
- Deliverable: `docs/COURSE_PLAN.md` — plan only, nothing implemented.
  Covers stages/units/lessons syllabus, original story (Acharnae, 432 BC,
  own cast), exercise engine (17 types, morph-engine-generated drills),
  assessment ladder, skill mastery + spiral review, data model, API,
  routes, build pipeline, image plan, phases A–E, and open decisions (§9).
- User decisions (same day): Athens setting (potter's family, Kydathenaion
  / Kerameikos), Creative Commons images only with an "Attic pottery"
  visual identity, and yes to the other recommendations (Greek-first with
  English toggle, politics track, lenient accents until Unit 4, tracks
  after Unit 9, stress cue). Plan updated. Three style mockups (Museum,
  Workbook, Night Reader; phone + desktop) delivered as a design canvas
  artifact; style choice still open (§9.8).
- Start Phase A (skeleton + Stage 0 + Unit 1) next; assume the Museum
  palette until the user picks a style.

## Session log — 2026-09-25 (course Phase A built)

- **Backend** `app/course/` (`data.py` loader/resolver, `normalize.py`
  answer normalization, `grade.py` reference grader, `drill.py` generated
  morphology items, `validate.py` authoring rules) + `scripts/build_course.py`.
  Content in `app/course_data/`: `course.json` (stages/units/tracks, proper
  names), `skills.json`, `vocab_extra.json` (27 course-only words in
  lexicon shape; κύων carries a hand table via the new `morph.table`
  override in `nominal.py`), `images/manifest.json` (74 placeholder records;
  real CC images replace them), `lessons/0.1–0.4, 1.1–1.4`,
  `tests/unit-1.json` (generated forms section, seeded per attempt).
  Routes: `/api/course`, `/lesson/{id}`, `/test/{id}?seed`, `/drill`,
  `/images`, `POST /check` (morph-aware feedback). `/api/vocab` now
  includes course words (`source: "course"`) and a `lessons` facet.
  Pre-render job renders course stories at 0.75/0.6 + words + item audio.
  G2P maps « » → curly quotes. 378 backend tests.
- **Authoring rules enforced by tests**: every story token must be a form
  of an already-taught word (engine-generated), a listed proper name,
  glossed once in the lesson, or in `allow`; ≤ 12 new words per lesson
  (Stage 0 exempt); typed answers must match the engine; every lesson
  skill needs an exercise; quiz 5–10 items; images must exist. Run
  `python scripts/build_course.py --stats`.
- **Answer policy**: lenient until Unit 4 (accents, macrons, iota subscript
  and *smooth* breathing ignored; rough breathing always counts), strict
  from Unit 4 or per user setting. Python and TS normalizers share
  fixtures (`frontend/lib/normalize.fixtures.json`, regenerate with
  `scripts/export_normalize_fixtures.py`).
- **Frontend**: `lib/course.ts` (grading, skill mastery), `lib/courseState.ts`
  (gating, test unlock 24 h after the unit, reread schedule 1/3/7/21 d,
  continue = lesson after the last done), progress v2 (`course` section,
  migration, merge for sync), `components/course/*`, pages `/course`,
  `/course/lesson/[id]`, `/course/test/[id]`, `/course/review`; Course tab;
  vocab deck filter "Words from a course lesson". Workbook theme in
  `globals.css` (fonts via Google Fonts link; system fallbacks offline).
  45 vitest tests; `next build` clean.
- **Verified**: `backend/scripts/e2e/` (fake-voice API + Playwright walk:
  Lesson 1.1 all steps with every item answered from the data → done →
  reload → Unit 1 test unlocked and passed → review page → vocab filter;
  phone and desktop). Screenshots in `docs/screenshots/`.
- **Known gaps / next**: images are placeholders (Phase B image pass);
  Google Fonts blocked in the sandbox (fallback fonts render); real-voice
  check of the story clips on Railway; Units 2–6 content; placement test;
  `/check` feedback not yet surfaced in the UI; the two summarised
  Athenaze student books are scanned PDFs without text (handbooks were
  used instead; see `docs/reference/`).

## Session log — 2026-09-26 (course Phase B: Stage 1 content)

- **Units 2–6 authored** by five parallel agents on disjoint files, then
  validated and spot-read: `lessons/2.1–6.4`, `tests/unit-2..5`, `gate-1`
  (unseen Deucalion & Pyrrha), `vocab_extra-u2..u6.json` (~90 course-only
  words, all engine-conjugated or hand-tabled), `images/manifest-u2..u6.json`
  (260 placeholder records). `build_course.py --stats` → 0 problems;
  backend 399 tests; frontend 49 vitest; `next build` clean. Browser walks:
  `scripts/e2e/e2e_placement.py` (pass + beginner paths),
  `scripts/e2e/e2e_stage1.py` (Lesson 6.3 all exercises, gate-1 passed).
  Story lengths grow from ~150 (Unit 1) to 200–310 tokens (Units 4–5);
  AUTHORING.md updated. Cast additions: Θρᾷττα (slave, 2.2), Σίμων (Chian
  metic, 4.2), Δίων/Φίλιππος (school, 4.3), Φιλῖνος (Koan doctor, 5.4),
  Θεόδωρος (Milesian merchant, 6.2). Myths: Prometheus (2.3, 6.4 review),
  Apollo & Daphne (5.3); Salamis as Kleinias' memory (5.2).
- **Placement test**: `GET /api/course/placement?seed=` → per-unit blocks
  (≤ 8 forms + sentence items from each unit test, no vocab/reading/self
  items); `/course/placement` runs blocks in order, stops after 3 misses in
  a row or a block < 60 %, marks every earlier lesson `skipped`, records
  `course.placement`, opens the next authored lesson. `?seed=` pins a run.
  `placementDecision()` in `lib/course.ts` (vitest).
- **Images**: `scripts/build_images.py` (`report | resolve | verify | fetch |
  process | manifest | all`, `--only`), `images/sources.csv` (70 rows for
  Stage 0/Unit 1; `search:<query>|<title regex>` refs resolve to object ids
  in `resolved.json`; `verified.json` caches licence/credit/URL). Sources:
  Met, Cleveland, AIC, Smithsonian (`SMITHSONIAN_API_KEY`), Wikimedia
  Commons, manual. Only CC0 / PD / CC BY / CC BY-SA pass. Output WebP ≤ 60 KB,
  3:2 or 1:1, cream field, 12 % padding, mild grade →
  `frontend/public/course/pics/<id>.webp`; `manifest` fills the record in
  place. **Egress-blocked here: run locally**, then commit pics + manifests.
  Diagrams (4 + per-unit) are our own SVGs, not sourced. `/course/credits`
  lists every image; the licence badge on a picture links there.
- **Engine fixes from the authoring pass**: `aorist_stem` overrides written
  with the compound prefix are stripped (ἐξελθεῖν, not ἐξεξελθεῖν);
  ὑφαίνω marked `compound: false` (was ὑπο + αἵνω → ὑφαῖναι; now ὑφῆναι);
  drill generator matches `noun.decl3.(cons|sigma|iota|eus).*` and
  `noun.decl3.cons.pl`, and `verb.*.mp/mid` skills draw deponents first and
  read either `middle` or `middle/passive` tables; validator flags a lemma
  in two `vocab_extra-*.json` files and an image id in two manifests;
  `scripts/dedupe_course_data.py` keeps the lowest unit's record.
  Typed-item misses in lessons show "You typed the genitive singular of
  οἶκος" via `/api/course/check` (`scope` prop on `ExerciseRunner`).
- **Reported, not fixed** (agents' notes): comparatives/superlatives are
  not generated (glossed with `<`); participles exist only as nom. sg. (+
  gen. m) cells; `verb-impersonal` (ἔξεστι) and -εσ- stem masc./fem.
  (τριήρης), -υ neuter (ἄστυ), ἰχθύς need hand tables; ἵστημι's root
  aorist cells are keyed `"root aorist.…"` so drills cannot reach them;
  compound verbs augment the prefix unless `imperfect_stem` is given
  (ἀναγιγνώσκω, ὠνέομαι); `course_tools.py check` breaks on a closed pipe.
- **Open for the user**: live link — point Railway `web`/`backend` at this
  branch or open a PR to `main` (Railway deploys `main`). Real-voice check
  of the new story clips on Railway; the pre-render plan is now ~28
  stories × 2 speeds + words + item audio.
- **Theme switched to style C, light** (user request, 2026-09-26: "go back
  to C but use light mode"). `globals.css` tokens rewritten: paper
  `#f6f4ee`, stone `#eeebe3`, ink `#1c2024`, sage `#a3b18a` (fills) /
  `#4e6136` (text, buttons), Literata + IBM Plex Sans (Google Fonts link in
  `layout.tsx`), 1 px borders, no offset shadows; PWA theme colour
  `#f6f4ee`. All text pairs ≥ 5.2:1. Class names unchanged, so no component
  logic moved. Screenshots with the real fonts: fonts fetched from npm
  (`@fontsource-variable/literata`, `@fontsource/ibm-plex-sans`) and routed
  in Playwright in place of Google Fonts (egress-blocked here).

## Session log — 2026-09-26 (course Phase C: Stage 2)

- **Engine**: `morph/participle.py` declines every participle from its four
  principal forms (gold tables for 12 models); course form lookup adds
  `tense.voice.participle.<case>.<num>.<g>`, `comp.*`/`sup.*` and `adv`
  cells (cached per entry). Overrides: `"drop": ["future.middle"]` removes a
  system; ἔρχομαι future/imperfect from εἶμι (εἶμι, ᾔειν), ἀποθνῄσκω perfect
  τέθνηκα, λέγω perfect mp εἴρημαι, ἐρωτάω aorist ἠρώτησα, no bogus
  passives for ζάω/πάσχω/ἀποθνῄσκω, θᾶττον. Periphrastic cells (with a
  space) are skipped; paired entries (μέν…δέ, εἴτε…εἴτε) match each half;
  spacing koronis → elision apostrophe in `normalize_polytonic`.
- **Drills**: `verb.ptc.<t>.<v>[.<case>][.<num>]`, `syntax.gen-abs`,
  `adj.comp`/`adj.sup`, perfect/pluperfect, passives (present passive =
  middle/passive table, deponents excluded; second/root aorist labels),
  lemma skills (`verb.mi.didomi`, `verb.phemi`, `verb.oida`, …). skills.json
  333 skills (144+ drill-backed).
- **Originals**: `course_data/texts/` (9 Perseus passages: Thuc. 2.13, 2.14,
  2.16, 2.21, 2.35, 2.47, Lysias 1.6–7, Apollodorus 1.9.28, Anabasis
  3.1.4–5) via `scripts/build_course_texts.py`; library passages usable by
  id. Lesson `original: {text, note}`, story sentences `orig: [n]`; test
  sections `passage_from`, `glosses` (shown under the passage), `passage_note`.
  Frontend `OriginalText` panel in the Read step.
- **Content**: Units 7–12 by six parallel agents (brief: AUTHORING.md
  "Stage 2"), vocabulary pre-allocated in `stage2_vocab.json`
  (`course_tools.py alloc`; `prune-allow` removed ~230 temporary allows).
  Chronology fix: Unit 7 = City Dionysia of spring 431 (Medea), Panathenaea
  inside the walls in 9.3, Unit 12 epilogue c. 370. Validator now checks
  unit-test passages, every elision mark and aspirated elision (ἐφ’).
- **Diagrams**: 47 own SVG components (`components/course/diagrams`,
  CSS-variable colours) for every diagram record, incl. schematic maps;
  `lib/diagrams.test.ts`; records `svg: true`, CC BY-SA.
- **Verified**: build_course 0 problems; backend 429 tests; frontend 99
  vitest; `next build`; e2e `e2e_course`, `e2e_placement` (12 units, 6
  items each), `e2e_stage1`, `e2e_stage2` (original panel, diagram, 11.3
  exercises, gate II passed); screenshots 11–13 in `docs/screenshots/`.
- **Known gaps**: no dual or verbal adjectives in the engine (glossed);
  ἵστημι short perfects; photographs still placeholders; Phase D (tracks).

## Session log — 2026-09-26 (course Phase D + Phase E)

- **Tracks (Stage 3)**: `course.json` tracks list 7 lessons (`myth.*`,
  `phil.*`, `hist.*`, `pol.*`) + gate (`gate-<prefix>`), `side_after` 9.4
  (lessons 1–3), `full_after` 12.4. `data.py`: `main_lesson_ids()` (Stage
  0–2 order) vs `lesson_ids()` (+ tracks); a track lesson's scope = main
  course through its `requires` + the track's earlier lessons (tracks never
  see each other); `resolve_track`, `lesson_summary`. Validator: ≤ 15 new
  words, lessons 4+ accept every DCC form (`_core_forms`), gates validated.
  Per-track files so authors never share one: `vocab_extra-<p>.json`,
  `skills-<p>.json` (loaded by `load_skills`), `texts/sources-<p>.json`,
  `images/manifest-<p>.json`, `images/sources-<p>.csv`. 4 agents wrote the
  content (AUTHORING.md "Stage 3"). Palaephatus and the Old Oligarch are not
  in canonical-greekLit (replaced). Hand fixes in `texts/apollod-epit-1.7`,
  `-1.12` and `plato-rep-360a` (rebuilding brings the Perseus typos back).
- **Frontend**: `/course/track/[id]` (ladder, gate, texts, track words),
  course-home track cards + "your track", `trackLessonStatus`/`trackGate`
  in `courseState.ts` (vitest). Track lessons are strict on accents.
- **Guided reading (Stage 4)**: `app/course/analyze.py` (form index over
  all lexicon entries → coverage, entries, unknown); `POST /api/analyze`,
  `GET /api/analyze/library`; `WordCoverage` panel under the Reader text;
  `/vocab?words=a,b&from=label` deck.
- **Phase E by agents**: skills grid `/course/skills` + `GET
  /api/course/skill/{id}`; mistakes deck `/course/review?mode=mistakes` +
  `POST /api/course/items` (ErrorEntry `right`/`cleared`); offline service
  worker `public/sw.js` (story streams and `/api/speak` cached under
  synthetic GET keys, `offline.html`, `lib/offline.ts` prefetch); navigation
  (bottom tab bar ≤ 640 px, `Crumbs`, `SiteFooter`, `PageState`), axe-clean
  a11y pass (`e2e_nav.py`, `axe-core` dev dep). `NEXT_DIST_DIR` lets a
  second build live beside `.next` (it rewrites `next-env.d.ts`: restore it).
- **Engine** (merged from a worktree branch): author-reported fixes (-σον
  imperative accent, compound imperatives, -ων non-comparatives, γχ/ν
  perfect middles, σκοπέω, ἔχω compounds, Attic futures in -αύνω/-άζω,
  assimilated prefixes, πλοῦς, πλήρης, κεῖμαι compounds, ἑστώς, οὕτω,
  οἶμαι, ἔγωγε); **dual** everywhere (separate `dual` block; FormsTable
  "show dual"; course cells `nom.du`, `…2du`); **verbal adjectives**
  `vadj.tos`/`vadj.teos` (override `"vadj": false|{tos,teos}`).
- **Fixes found by e2e**: generated parse items for infinitives asked for a
  person (now tense + voice); story ▶ needed two taps (load resolves on the
  sentence list; clips looked up in the list just loaded).
- **Images**: `build_images.py` gained query relaxation + cross-source
  fallback, `doctor`, `failures.json`, host circuit breaker, browser UA for
  museum CDNs; Commons licence check crashed on numeric metadata (fixed);
  Met search needs `q` last. `scripts/images_retry.sh` (python3 venv of its
  own, macOS bash 3.2 safe) runs the pass locally and pushes pictures +
  `failures.json` + `doctor.json` + `last-run.log`.
- **Verified**: build_course 0 problems; backend 654 passed; vitest 126;
  `next build`; e2e course, placement, stage1, stage2, tracks, skills, nav
  (offline e2e by its agent).
- **Open**: photographs (user's local image run); quiz and questions items
  share the `q` id prefix (388 collisions; the mistakes deck disambiguates);
  ἐμαυτοῦ/σεαυτοῦ have tables but no lexicon entries; λύω shows θνῄσκω's
  note (shared DCC rank 384 in overrides); content review by a second reader.
