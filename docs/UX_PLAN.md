# Attic Reader — app structure and usability plan

Status: plan, nothing implemented. Follows `COURSE_PLAN.md` (content) and
the light "Reader" theme (§9.8 there). This plan changes how the app is
organised, not what it teaches.

## 0. The problem, in one paragraph

The app grew page by page: the Reader (the first prototype) is still the
front door, the nav is four flat tabs, and Course, Words and Grammar are
each one long page. A new visitor lands on a text-to-speech tool with no
explanation, cannot tell there is a course, and once inside has no home,
no account, and no sense of "where am I, what next". The content and the
voice are good; the shell around them is not.

## 1. Principles

1. **Home is a dashboard, not a tool.** The first screen answers "what is
   this, where am I, what should I do now".
2. **One job per page.** Library ≠ Reader ≠ Add-a-text. Deck picker ≠
   study session ≠ word browser.
3. **Grouped, not listed.** Every list longer than ~12 items gets sections,
   filters or search: lessons by stage/unit, paradigms by part of speech,
   words by lesson/topic/tier, texts by author/level.
4. **Recommended before browsed.** Each hub opens with 3–6 cards chosen
   from the learner's state (current lesson, due words, weak skills, track);
   full browsing sits below.
5. **The app explains itself.** Onboarding on first visit, a Help page, an
   empty state that says what to do on every screen, and a consistent
   sidebar so every page is one tap from every other.
6. **Same look everywhere.** One layout (sidebar + top bar + content
   column), one card, one section header, one search box, one tab strip.

## 2. Information architecture

```text
/                      Home  · logged out: what the app is + Start / Sign in
                             · logged in: dashboard (continue, today, streak, track)
/start                 Onboarding: goal + level → 0.1, placement, or Library
/learn                 Course hub: stages → units (collapsible), tracks, tests
/learn/unit/[n]        A unit: 4 lessons + test, story blurbs, what you'll learn
/learn/lesson/[id]     Lesson player (existing 10 steps; gains an outline rail)
/learn/test/[id]       Test runner (existing)
/learn/track/[id]      Track page (existing)
/learn/placement       Placement (existing)
/library               Texts: search + filters, collections, recommended, my texts
/library/[id]          Read one text: player, sentences, word panel, coverage
/library/new           Add a text: paste or photograph (the old Reader "1–2")
/practice              Practice hub: Review (today's queue) · Words · Drills
/practice/review       One review session: due words → sentence cloze → weak-skill
                       drill → mistakes; modes read / write / listen / forms
/practice/quick        Quick 5-minute session (timed mix from the queue)
/words                 Words: recommended decks, browse (lesson/topic/tier),
                       search, deck builder (drawer)
/words/study           Study session (existing card UI, own page)
/words/[id]            Word page (existing)
/learn/listen/[unit]   Listen mode: a unit's stories hands-free, with pauses
/grammar               Grammar hub grouped by part of speech; search; "your level"
/grammar/[id]          Paradigm page (existing + "taught in lesson", dual toggle)
/progress              Skills grid, mistakes, tests, activity, streak
/settings              Account, sync, accents policy, English, speed, dual, data
/help                  How the app works (3-minute tour), FAQ, pronunciation
/signin · /signup      Accounts (§5)
```

Renames: **Course → Learn**, **Read → Library** (icon: open book, not
headphones), **Vocab → Words** (inside a **Practice** section, see
`APP_REVIEW.md`). Old URLs redirect (`/course/*` → `/learn/*`,
`/vocab` → `/words`) so deep links, sync codes and the service worker's
saved pages keep working.

## 3. Navigation

### Desktop (≥ 900 px): sidebar

```text
┌──────────────┬───────────────────────────────────────────────┐
│ Attic Reader │ Learn › Unit 3 › Lesson 3.2        [search] [☺]│
│              ├───────────────────────────────────────────────┤
│ ⌂ Home       │                                               │
│ ◎ Learn  ▸   │   page content, one column ≤ 760 px, or a     │
│   Units      │   two-column grid on hubs                     │
│   Tracks     │                                               │
│   Tests      │                                               │
│ ▤ Library    │                                               │
│ ▦ Practice ▸ │                                               │
│   Review     │                                               │
│   Words      │                                               │
│   Drills     │                                               │
│ ☰ Grammar    │                                               │
│ ◔ Progress   │                                               │
│              │                                               │
│ ? Help       │                                               │
│ ⚙ Settings   │                                               │
│ Kostas · 12d │                                               │
└──────────────┴───────────────────────────────────────────────┘
```

- The active section is highlighted; Learn expands to show its sub-pages.
- The top bar carries breadcrumbs (already built), a global search (texts,
  words, paradigms, lessons — one endpoint, §9) and the account menu.
- The sidebar collapses to icons at 900–1100 px.

### Phone (< 900 px): bottom tabs + "More"

Home · Learn · Library · Practice · More. "More" opens a sheet with Grammar,
Progress, Settings, Help, Sign out. The lesson player and the text reader
hide the tab bar behind their own bottom bars (already handled).

### In-page

- Hubs use a **tab strip** for their main views (Words: Recommended ·
  Browse · My decks; Library: Recommended · All texts · My texts).
- Long groups are **collapsible sections** with counts (Stage 1 · 24
  lessons ▾), closed by default except the learner's current one.
- Every page has a **page header**: eyebrow, title, one-line lede, primary
  action on the right.

## 4. Onboarding and help

- **First visit** (no progress, no account): Home shows a three-panel
  explainer (Learn a course · Read real texts · Hear Classical Attic) and
  one button, *Start learning*. `/start` asks two questions:
  1. *Goal*: learn from the start · brush up · just read and listen.
  2. *Level* (if brushing up): a 6-question mini placement → opens the
     right unit (existing placement, shortened).
  Then it opens the first lesson / Library, with a 3-step coach-mark tour
  (sidebar, continue card, help).
- **Help page**: how a lesson works (10 steps, pictures), how decks and
  spaced repetition work, how to read a text (tap word, play sentence,
  speeds), the pronunciation policy (short), offline, accounts and data.
- **Empty states** on every hub ("No mistakes yet — they appear here after
  a lesson check") with a link to the action that fills them.
- **"?" in the top bar** opens the Help section for the current page.

## 5. Accounts

Today progress lives in `localStorage` with an optional sync code. The
user now wants accounts with settings and progress. Options, all free:

| Option | Pros | Cons |
|---|---|---|
| **A. Email + password on our backend** (recommended) | no third party, works with the existing progress store, offline-first stays | we hold password hashes; password reset needs an email sender (can be "contact the owner" at first) |
| B. Google / Apple sign-in (OAuth) | no passwords | console setup per provider; Apple needs a paid developer account; still need a user table |
| C. Passkeys (WebAuthn) | best UX on iPhone | new for most users; recovery is hard without email |

**Recommendation: A now, B (Google) later as a second button.**

Design:
- Backend: SQLite on the Railway volume (`/data/attic.db`): `users(id,
  email, password_hash[argon2], created)`, `sessions(token, user_id,
  expires)`, `progress(user_id, document JSON, updated)`. Routes:
  `POST /api/auth/signup | signin | signout`, `GET /api/me`, `GET/PUT
  /api/me/progress`, `DELETE /api/me` (account + data). HttpOnly secure
  cookie; CORS with credentials (web and API are different origins on
  Railway — set `SameSite=None`, or proxy `/api` through Next to make them
  same-origin, which also simplifies the service worker; **prefer the
  proxy**).
- Frontend: `lib/auth.ts`, `AuthProvider` context, `/signin`, `/signup`,
  account menu. Progress: keep the local document as the working copy;
  when signed in, push after every change (debounced) and pull on load,
  merging with the existing `mergeProgress` rules. Guest mode keeps
  working; a banner offers to save the local progress into a new account
  on sign-up (one-click import). The sync-code feature stays as
  "Import from a sync code" in Settings, then retires.
- Settings page (§7) is the same document's `settings` block plus account
  fields (email, password change, delete account, export JSON).

## 6. Page designs

### 6.1 Home (`/`)

Logged in:
```text
Good evening, Kostas · 12-day streak · 15 / 15 min today · 412 words known
[Quick 5 minutes]
┌ Continue ───────────────────────────┐ ┌ Today ───────────────┐
│ Lesson 3.2 · Ἡ Χρυσὶς ἐν τῇ ἀγορᾷ   │ │ 23 words due   → study│
│ step 6 of 10 · [Resume]             │ │ 2 weak skills  → drill│
└─────────────────────────────────────┘ │ reread 2.4     → open │
┌ Your path ─────────────────────────┐ └───────────────────────┘
│ Stage 1 ●●●●●●●●●○○○○○○○  9/24      │ ┌ Recommended text ────┐
│ Unit 3 test opens in 18 h           │ │ Xenophon, Anab. 1.1  │
│ Track: not chosen (after Unit 9)    │ │ 84 % known · 3 min   │
└─────────────────────────────────────┘ └───────────────────────┘
```
Logged out: hero + three explainer panels + *Start learning* / *Sign in*
+ "or just paste a text" link to `/library/new`.

### 6.2 Learn (`/learn`)

- Header: course title, overall progress bar, [Continue].
- **Stages as collapsible sections**; inside, **unit cards** in a grid
  (title, one-line story blurb, 4 lesson dots, test state). Current stage
  open, others closed. Tracks are their own section with the four cards.
- **Unit page** (new): the unit's story arc in two sentences, the four
  lessons as rows (title, what you'll learn, ~minutes, state), the test,
  the unit's words (link to a deck), the grammar it teaches (links).
- Lesson player: unchanged steps; add a left rail (desktop) listing the
  10 steps with ticks, and "Words in this lesson" / "Grammar" shortcuts.

### 6.3 Library and reading (`/library`, `/library/[id]`, `/library/new`)

Library hub:
- Search box (title, author, work, and the Greek text itself — see §9),
  filter chips: author · level · length · "% known" ≥ 80.
- **Recommended for you**: 3 texts ranked by known-word coverage and level
  vs. the learner's unit; the texts the current unit adapts ("the original
  of Lesson 9.2") first.
- **Collections**: by author (Xenophon 5, Plato 4, …) and by course track;
  each card shows author, work, ref, sentences, minutes, % known, "ready".
- **My texts**: pasted/photographed texts the learner saved (new: store in
  the progress document, ≤ 20, title + text; server-side when signed in).
- [+ Add a text] → `/library/new`: two clear paths, *Paste Greek* and
  *Photograph a page*, then *Check the text* (OCR corrections) → *Read*.

Reading page (`/library/[id]` or `/library/mine/[n]`):
- Header: author/work/ref, level, % known, speed selector, [Play all].
- Sentence list as now (tap to play, word highlight), plus a **word panel**
  on tap (lemma, short gloss, forms link, ▶, "add to deck") — today a word
  tap only highlights.
- Coverage panel (built) moves into a side card on desktop; "Study the N
  new words" stays.
- The pronunciation audit becomes a "Show IPA" toggle in the header.

### 6.4 Words (`/words`)

Tabs: **Recommended · Browse · My decks**.

Recommended (cards, each with count and [Study]):
- *Due today* (SRS), *This lesson* (current lesson's words), *Unit N
  review* (the unit just finished), *Weak words* (lowest ease/most lapses),
  *Mistakes* (from the mistakes deck), *Your track's list* (after 9.4),
  *Next lesson preview* (optional), *Frequency tier* matching the learner's
  level (tier 1 in Stage 1, tier 2 in Stage 2, …).
- Rule set in `lib/decks.ts`: a deck is shown only when it has ≥ 5 cards;
  order = due → this lesson → weak → mistakes → track → tier.

Browse (replaces the chip wall in the screenshot):
- Left: a **grouped tree** — By lesson (Stage 0 › Unit 1 › 1.1 …, tracks),
  By topic, By part of speech, By frequency tier, By reading. Groups are
  collapsible with counts; picking a node shows its words on the right
  with a [Study these] button.
- Right: the word list (headword, short gloss, ▶, tier badge, "known"
  dot from SRS state), with a search box (Greek or English, accent-
  insensitive) and sort (frequency · alphabetical · least known).
- **Deck builder** becomes a drawer ("Custom deck") that combines groups
  with AND/OR, previews the count, and can be saved under a name → *My
  decks* (stored in the progress document).

Study session (`/words/study?deck=…`): the existing card UI on its own
page, with the deck name, progress "7 / 20", and the settings (direction,
card types, session size) in a small popover instead of a settings panel.

### 6.5 Grammar (`/grammar`)

- Hub grouped by **part of speech** (the article · nouns by declension ·
  adjectives · pronouns and numerals · verbs by system) with a short
  description per group and a **"you are here" marker** (the paradigms the
  learner's lessons have reached are normal; later ones are dimmed with
  "taught in Lesson 7.2").
- Each paradigm card: model word, one-line note, "taught in", link.
- Search box (paradigm names, model words, cell labels like "dative
  plural").
- Paradigm page: table (dual toggle), "taught in" lessons, related
  diagrams (the SVGs), a [Practise] button that opens a drill for that
  paradigm's skills (drill generator already supports it).

### 6.6 Progress (`/progress`)

The skills grid (built) plus: streak and activity heat-map (activity
data exists), tests taken with scores, mistakes deck link, words learned
(SRS counts by state), track progress. Filters by stage.

### 6.7 Settings (`/settings`)

Account (email, password, delete, export), Learning (accent policy,
English toggle, default speed, auto-speak, show dual), Data (sync-code
import, offline cache size + clear), About (versions, credits link).

## 7. Design system additions

Keep the tokens. Add components: `AppShell` (sidebar + top bar + content),
`SideNav`, `PageHeader`, `SectionGroup` (collapsible with count), `Tabs`,
`SearchBox`, `FilterChips` (small, wrapping, with a "clear"), `DeckCard`,
`TextCard`, `UnitCard`, `EmptyState`, `Drawer`, `Popover`, `StatTile`
(exists), `Tour` (coach marks). Grid: content max 1100 px on hubs, 760 px
on reading/lesson pages. Motion: none beyond the existing reduced-motion
rules.

## 8. Backend changes

- Auth + user store (§5); progress by user; `/api/me`.
- **Search**: `GET /api/search?q=` over library texts (title, author,
  work, and normalized Greek text), lexicon (lemma, definition), paradigms,
  lessons (titles, Greek and English). Accent-insensitive; returns grouped
  results for the top-bar search.
- **Library index** gains `known_pct` per user (coverage already computed;
  client applies the SRS state), `minutes`, `author_slug`.
- **Saved texts**: part of the progress document (no new table); the
  analysis endpoint already exists.
- Next.js `rewrites` proxy `/api/*` → backend so cookies and the service
  worker see one origin (replaces `NEXT_PUBLIC_API_BASE_URL` in production;
  keep it for local dev).

## 9. Migration and compatibility

- Route redirects (§2); the service worker's precache list updated;
  progress document version 3 (adds `account`, `savedTexts`, `decks`).
- Existing e2e scripts updated to the new routes/selectors; new e2e:
  onboarding, sign-up + import, library search, words hub, grammar hub.

## 10. Phases

| Phase | Deliverable | Est. |
|---|---|---|
| **F1 Shell** | `AppShell` + sidebar + bottom tabs + top bar, renames and redirects, Home (logged-out and dashboard with known-words count, weekly goal, Quick 5 minutes), `/start` onboarding, Help page, empty states, session summary screen, design-system components | 1 session |
| **F2 Accounts** | backend auth + user store + `/api/me/progress`, `/api` proxy, sign-in/up pages, guest → account import, Settings page | 1 session |
| **F3 Library** | `/library` hub (search, filters, recommended, collections, my texts), `/library/[id]` reader with known/learning/new word states and the tap-to-gloss card (Known / Learn this), `/library/new` add flow | 1 session |
| **F3b Listen mode** | `/learn/listen/[unit]`: hands-free unit playlist, repeat and anticipation pauses, speed; optional record-and-compare | ½ session |
| **F4 Practice** | Review hub (one queue: due words → sentence cloze → weak-skill drill → mistakes; modes read / write / listen / forms), sentence-cloze generator (backend), recommended decks engine, Browse tree + list + search, deck builder drawer + saved decks, study page | 1½ sessions |
| **F5 Grammar + Progress + Learn** | grammar hub by part of speech with "you are here", paradigm practise; progress page; Learn hub with collapsible stages and unit pages; lesson outline rail | 1 session |
| **F6 Polish** | global search, coach-mark tour, e2e for every new page, screenshots, docs | ½ session |

Each phase ships behind the current preview URL; F1 alone already fixes
the "opens to Read with no explanation" problem.

## 11. Decisions needed

1. **Accounts**: email + password on our backend (recommended), Google
   sign-in, or both? Password reset by email needs a sender (Resend/
   Postmark free tiers) — OK to start without reset?
2. **Names**: Learn · Library · Words · Grammar · Progress — or keep Course
   · Read · Vocab?
3. **Guest mode**: keep the app fully usable without an account (recommended)
   or require sign-in for the course?
4. **Photo/OCR**: keep it as a secondary path inside "Add a text"
   (recommended) rather than the front door.
5. **Global search** in the top bar: F6 (recommended) or F1?
6. Order: F1 → F2 → F3 → F4 → F5 → F6, or F1 → F4 (Words) first since that
   page annoyed you most?

## 12. Additions from the app review

See `APP_REVIEW.md` §3. Adopted: known-word states and tap-to-gloss in the
reader (LingQ); one Review hub with modes (Babbel); sentence cloze on real
sentences (Clozemaster); known-words counter and weekly goal (LingQ); Quick
5 minutes (Drops); session summary (Babbel/Duolingo); Listen mode with
anticipation pauses (Pimsleur/Glossika); unit guidebook page (Duolingo).
Optional later: record-and-compare, English toggle per story sentence,
Assimil-style active wave, a letters game for Stage 0.
