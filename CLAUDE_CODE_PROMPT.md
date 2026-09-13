# Prompt for Claude Code

Copy everything below the line into Claude Code, run from the unzipped `attic-reader/` directory.

---

You are taking over **Attic Reader**, a mobile-first web app that photographs or pastes polytonic Ancient Greek and reads it aloud in reconstructed Classical Attic (c. 400 BC) with a natural neural voice. Read `CLAUDE.md` first — it is the full handoff. Then `benchmark-output/SCORECARD.md` and `DEPLOY.md`.

**Where things stand (2026-09-12):**
- Backend (FastAPI, `backend/`) and frontend (Next.js 15, `frontend/`) both run and build clean. `cd backend && pytest -q` → 16 passing.
- The voice milestone is **done and user-accepted**: Kokoro-82M with raw Classical Attic phoneme injection, voice `im_nicola`. MMS was rejected (Modern Greek phonology) and is disabled by default. Do not revisit the provider decision.
- The repo is git-initialized with history but has **no remote**. Nothing is deployed.

**Ground rules:**
- Never let the app fall back to Modern Greek phonology or eSpeak for learner playback.
- Keep the architecture split: Greek → canonical Attic phonemes (`backend/app/greek/g2p.py`) → provider token mapping (`backend/app/tts/kokoro.py`) → audio. Don't put model-specific hacks into the canonical G2P.
- Install torch with the CPU wheel (`pip install torch --index-url https://download.pytorch.org/whl/cpu`) — the default wheel pulls ~3 GB of CUDA.
- `KPipeline(lang_code="i")` is the default; `"a"`/`"b"` additionally need spaCy `en_core_web_sm`.
- No accounts, billing, or saved libraries in v1.
- Commit after each phase with a clear message. Ask me before any step that costs money.

## Phase 1 — Publish to GitHub
1. `gh auth status`; if not authenticated, tell me and stop.
2. `gh repo create attic-reader --public --source=. --remote=origin --push` (use `--private` if I say so).
3. Confirm the repo URL back to me.

## Phase 2 — Deploy and give me a public URL
Follow `DEPLOY.md`. Preferred: backend on **Railway** (Docker, `backend/railway.json`, a volume at `/data`, ≥2 GB RAM), frontend on **Vercel** (root `frontend`, env `NEXT_PUBLIC_API_BASE_URL`).
- Use the Railway CLI (`railway`) and Vercel CLI (`vercel`) if they're installed and logged in; otherwise walk me through the two dashboards step by step, and set env vars exactly as listed in `DEPLOY.md`.
- After both are up: set `CORS_ORIGINS` on Railway to the Vercel domain, redeploy, then run the smoke test in `DEPLOY.md` with `curl`.
- Report the public frontend URL and the backend `/api/tts/status` JSON.

## Phase 3 — Build the learner experience (in this order)
Do these one at a time; run `pytest` and `npm run build` after each; commit each.

1. **Sentence segmentation.** Add `backend/app/greek/segment.py`: split Greek on `.` `;` `·` `!` `?` and newlines, preserving the original text spans. Expose `POST /api/segment` returning `[{index, text, start, end}]`. Tests.
2. **Per-sentence synthesis.** Extend `POST /api/synthesize` to accept `{text, speed?}` and add `POST /api/synthesize/batch` that returns one audio clip per sentence (base64 WAV or multipart). Replace `split_phonemes()`'s character chunking with sentence-based chunking. Pass `speed` through to Kokoro (`KPipeline.generate_from_tokens(..., speed=)`).
3. **Frontend player.** After Generate, show the text as a list of sentences; tap a sentence to play it; ▶/■ per sentence; "play all" with the current sentence highlighted; speed selector 0.6× / 0.75× / 1× / 1.25×; "repeat this sentence" toggle. Keep it usable one-handed on an iPhone. Use a single `<audio>` element and `playsinline`.
4. **PWA polish.** Installable on iOS/Android (manifest icons, `apple-mobile-web-app-capable`, theme color). Keep source text + generated clips in memory only (no storage) for now.
5. **OCR on real pages.** Add `backend/app/ocr_preprocess.py` (grayscale, contrast, deskew via OpenCV) behind `POST /api/ocr`. Ask me for 3–5 phone photos of Athenaze / LOGOS / Loeb pages and build `backend/tests/ocr_regression/` with expected transcriptions. If Tesseract `grc` is poor on real photos, evaluate Kraken and report before switching.
6. **G2P audit (only after 1–5).** Work the linguistic backlog in `CLAUDE.md` Step 6, starting with syllabification and a documented ει/ου policy. Extend `benchmarks/attic_benchmark.json` for every rule you touch and regenerate WAVs with `python scripts/run_voice_benchmark.py --providers kokoro --voices im_nicola`.

## Known open issue to keep in mind
English Kokoro voices insert a linking-R after long ɛː/ɔː before a vowel; `im_nicola` does not. If I later switch to `bm_george`, insert a short silence at those boundaries in the provider mapping layer (not the G2P).

When each phase is done, give me: what changed, the commit hash, and the URL(s) I should open on my phone.
