# Handoff prompt — Attic Reader UX rebuild

Paste everything below the line into a coding agent that has access to
the GitHub repository `rems3n/attic-reader`. It is written to stand alone.

---

You are taking over development of **Attic Reader**, a web app for
learning to read Classical Attic Greek: a beginner course with an
illustrated story, real texts (Xenophon, Plato, Thucydides, Apollodorus…),
flash cards, a full morphology engine, and a neural voice in reconstructed
Classical Attic pronunciation. Repository: `https://github.com/rems3n/attic-reader`,
default branch `main` (everything below is already merged there).

Your job is to carry out `docs/UX_PLAN.md` — a full rework of the app's
structure and usability (home page, accounts, sidebar navigation, and
redesigned Library, Practice, Grammar and Learn hubs) — in the phases
F1 → F2 → F3 → F3b → F4 → F5 → F6 listed in its §10, using the decisions
in its §11 and the additions in its §12 / `docs/APP_REVIEW.md` §3.
The content and the voice are good; do not rework them. The shell around
them is what changes.

## Read first, in this order

1. `CLAUDE.md` — the project handoff document with a session log per
   feature (read the four "Session log — 2026-09-25/26" entries at the end
   with care; they describe the course, engine, tracks, offline mode,
   navigation and known open issues).
2. `docs/UX_PLAN.md` — what to build. §2 information architecture, §3
   navigation, §5 accounts, §6 page designs, §8 backend changes, §10
   phases, §11 decisions, §12 additions.
3. `docs/APP_REVIEW.md` — why (comparison with Pimsleur, Babbel, LingQ,
   Drops) and the eight adopted features.
4. `docs/COURSE_PLAN.md` — the course design (skim; §5 data model and
   §7 frontend routes matter).
5. `README.md` — setup.

## Repository map (what exists today)

```text
backend/                     FastAPI (Python 3.11)
  app/main.py                every route (/api/course/*, /api/vocab, /api/grammar,
                             /api/library, /api/speak, /api/synthesize/stream,
                             /api/analyze, /api/progress/{code}, /api/ocr …)
  app/course/                course loader (data.py), validator, drills, grading,
                             analyze.py (word coverage of a text)
  app/course_data/           course.json, skills*.json, lessons/*.json (Stage 0–2:
                             0.1–12.4; tracks myth.1–7, phil.*, hist.*, pol.*),
                             tests/*.json, vocab_extra*.json, texts/, images/
  app/greek/morph/           the morphology engine (nominal, verb, participle,
                             accent, paradigms); every form of every word
  app/vocab_data/            DCC core list (524 words) → core.json, overrides
  app/library_data/          12 reading-library passages
  app/tts/                   Kokoro voice adapter, clip cache, pre-render job
  app/progress.py            sync-code progress store (JSON files, 2 MB cap)
  scripts/build_course.py    course validator: must report "0 problem(s)"
  scripts/e2e/               Playwright walks + fake_server.py (a fake voice, so
                             no model download is needed for tests)
  tests/                     pytest (654 tests)
frontend/                    Next.js 15 (app router), TypeScript, no UI library
  app/                       / (Reader), /course, /course/lesson/[id], /course/test/[id],
                             /course/track/[id], /course/placement, /course/review,
                             /course/skills, /course/credits, /vocab, /vocab/[id],
                             /grammar, /grammar/[id]
  app/globals.css            the whole theme (CSS custom properties; light "Reader"
                             style: paper #f6f4ee, card #fff, stone #eeebe3, ink
                             #1c2024, muted #5a6168, line #dcd8ce, accent #4e6136,
                             sage #a3b18a; Literata + IBM Plex Sans; 1 px borders,
                             no offset shadows). Keep this look.
  components/                AppNav (top bar + bottom tab bar), Crumbs, SiteFooter,
                             PageState, ServiceWorker, Speak, FormsTable, WordCoverage,
                             course/* (StoryReader, ExerciseRunner, diagrams/*)
  lib/                       api.ts (every backend call), course.ts (grading, mastery),
                             courseState.ts (lesson/test/track gating), progress.ts
                             (the learner document: localStorage key attic.srs.v1,
                             version 2, migrations, merge for sync), srs.ts (SM-2),
                             skills.ts, offline.ts, normalize.ts
  public/sw.js               service worker (offline pages, audio, images)
docs/                        plans, authoring guide, screenshots
```

## How to run and verify

```bash
# backend (no voice model needed for development)
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
python -m pytest -q                       # 654 passed expected
python scripts/build_course.py --stats    # must end with "0 problem(s)"

# frontend
cd frontend && npm install
npx tsc --noEmit -p . && npx vitest run   # 126 tests
npm run build                             # must be clean

# browser walks (fake voice API on :8000, built frontend on :3000)
cd backend && source .venv/bin/activate
python scripts/e2e/fake_server.py &                       # E2E_API_PORT to change
(cd ../frontend && npm start &)                           # after npm run build
pip install playwright && playwright install chromium     # if not present
python scripts/e2e/e2e_course.py      # lesson 1.1 + unit test
python scripts/e2e/e2e_placement.py
python scripts/e2e/e2e_stage1.py
python scripts/e2e/e2e_stage2.py
python scripts/e2e/e2e_tracks.py
python scripts/e2e/e2e_skills.py
python scripts/e2e/e2e_nav.py         # axe-core: no serious/critical violations
python scripts/e2e/e2e_offline.py     # starts its own servers
```

Every phase must leave all of the above green, and the e2e scripts must
be updated when routes or selectors change (they are the regression
suite). Add a new e2e script per new page.

`NEXT_PUBLIC_API_BASE_URL` points the frontend at the backend (default
`http://localhost:8000`). Google Fonts is linked in `layout.tsx`; system
fonts render when it is unreachable.

## Deployment

Railway project `attic-reader`: services `web` and `backend` deploy from
`main` (production: https://web-production-a1ef.up.railway.app and
https://backend-production-d55b3.up.railway.app). Two preview services
(`web-preview`, `backend-preview`, https://web-preview-production-79af.up.railway.app)
followed the old feature branch; point them at your working branch or
delete them. The backend keeps a volume at `/data` (clip cache, progress,
and — for F2 — the SQLite user database).

## Conventions

- Work on a branch (e.g. `ux/f1-shell`), open a pull request per phase
  against `main`, and merge when the checks above are green. Never
  force-push `main`.
- Commit messages: a short imperative title, a body that says what and
  why. Do not put model or tool names in commits, code or docs.
- Keep the code style of the surrounding files (React function components,
  CSS classes in `globals.css` or a CSS module next to the page, no new UI
  library, no Tailwind). No new paid services; free tiers only.
- Greek text gets `lang="grc"`. Accessibility must stay at the current
  level: `e2e_nav.py` runs axe-core and fails on serious/critical issues.
- Course content rules are enforced by `scripts/build_course.py`; do not
  edit lesson JSON except to fix a real error, and never weaken the
  validator.
- Update `CLAUDE.md` with a short session-log entry at the end of each
  phase (what changed, how verified, what is open), and `docs/UX_PLAN.md`
  phase table (mark DONE).
- Don't touch: the morphology engine (`app/greek/morph`), the G2P/voice
  code (`app/greek/g2p.py`, `app/tts`), the course validator, unless a
  phase explicitly needs it.

## Decisions already taken (do not re-open)

- Accounts: email + password on our backend (argon2, HttpOnly cookie,
  SQLite at `/data/attic.db`) **and** Google sign-in (OAuth; the owner
  will create the Google Cloud client and set `GOOGLE_CLIENT_ID/SECRET`
  as Railway variables — build it behind those env vars and show the
  button only when they are set). No password reset by email yet.
  Guest mode stays fully usable; on sign-up, offer a one-click import of
  the local progress document. Keep the old sync-code import in Settings.
  Proxy `/api/*` through Next.js rewrites so cookies and the service
  worker see one origin (keep `NEXT_PUBLIC_API_BASE_URL` for local dev).
- Names and routes: Home `/`, `/start`, Learn `/learn/*` (was `/course`),
  Library `/library/*` (was `/`), Practice `/practice/*` (Review · Words ·
  Drills; words at `/words/*`, was `/vocab`), Grammar, Progress, Settings,
  Help, `/signin`, `/signup`. Old routes redirect. Library's icon is an open
  book, not headphones.
- Photo/OCR lives inside "Add a text" (`/library/new`), not on the front
  door. Global search is F6.
- Theme: keep the light Reader style and its tokens exactly.

## Phases (from `docs/UX_PLAN.md` §10; details in §6)

| Phase | Deliverable | Done when |
|---|---|---|
| **F1 Shell** | `AppShell` (sidebar ≥ 900 px, bottom tabs Home · Learn · Library · Practice · More below), top bar with breadcrumbs and account menu, renames + redirects, Home (logged-out explainer with *Start learning*; dashboard with Continue, Today, your path, known-words count, weekly goal, *Quick 5 minutes*), `/start` onboarding (goal + level → first lesson / short placement / Library) with a 3-step coach-mark tour, Help page, empty states on every hub, a shared session-summary screen after lessons/tests/decks | all old flows work at the new routes; e2e scripts updated; new `e2e_shell.py` covers home, onboarding, summary, sidebar/tabs at 390 and 1280 px |
| **F2 Accounts** | backend users/sessions/progress tables and `/api/auth/*`, `/api/me`, `/api/me/progress`; Google OAuth behind env vars; `/signin`, `/signup`, account menu, `/settings` (account, learning, data); guest → account import; progress push (debounced) / pull / merge | `e2e_accounts.py`: sign up, progress survives a cleared browser, import, settings save, sign out |
| **F3 Library** | `/library` hub (search over title/author/work/Greek text, filters author · level · length · % known, recommended, collections by author and track, my texts), `/library/[id]` reader with known / learning / new word colouring from SRS state, tap-to-gloss card (lemma, meaning, ▶, forms, *Known* / *Learn this*), coverage side panel; `/library/new` paste-or-photograph flow | `e2e_library.py`: search, filter, open a text, mark a word, deck link, add a pasted text |
| **F3b Listen** | `/learn/listen/[unit]`: hands-free playlist of a unit's stories, repeat ×2, anticipation pause (cue → pause → Greek), speed; optional record-and-compare | `e2e_listen.py` |
| **F4 Practice** | Review hub with one queue (due words → sentence cloze → weak-skill drill → mistakes) and modes read / write / listen / forms; backend sentence-cloze generator from corpus and story sentences; Words: recommended decks engine (Due today, This lesson, Unit review, Weak words, Mistakes, Your track, Your tier — shown only with ≥ 5 cards), Browse tree (by lesson/topic/part of speech/tier/reading) + searchable list, deck builder drawer + saved decks; `/words/study` page | `e2e_practice.py` |
| **F5 Grammar · Progress · Learn** | Grammar hub by part of speech with "you are here", paradigm page with *taught in* and *Practise*; Progress page (skills grid, known/learning/new, activity, tests, weekly goals); Learn hub with collapsible stages, unit cards, new unit page (guidebook), lesson outline rail | `e2e_grammar.py`, `e2e_learn.py` |
| **F6 Polish** | global search in the top bar (`GET /api/search`), coach marks, docs, screenshots in `docs/screenshots/` | all e2e green; CLAUDE.md updated |

Ship each phase as its own pull request. F1 alone fixes the worst problem
(the app opens on a tool with no explanation), so do it first and
completely before starting F2.

## Known open issues (not yours unless a phase touches them)

- Photographs: every course picture is still a placeholder until the
  owner runs `bash backend/scripts/images_retry.sh` locally (museum sites
  are needed); results land in `frontend/public/course/pics/` and
  `backend/app/course_data/images/`. Do not spend time on this.
- Lesson `questions` and `quiz` items share the `q` id prefix (388
  collisions); the mistakes deck disambiguates by answer shape. A proper
  fix changes item ids and stored error logs — leave it unless the owner
  asks.
- λύω's word page shows θνῄσκω's note (two words share DCC rank 384 in
  `vocab_data/overrides.json`). ἐμαυτοῦ/σεαυτοῦ have engine tables but no
  lexicon entries.
- A second reader has not reviewed the Greek content; the real voice has
  not been checked on every story clip.

## When you report back

For each phase: the pull request link, what changed (by page), the test
counts, which e2e scripts ran, screenshots at 390 × 844 and 1280 × 900 of
every new page, and anything you could not do or had to decide yourself.
