# How Attic Reader compares with language-learning apps

Written 2026-09-26 from working knowledge of the apps (the sandbox cannot
reach their sites, so nothing here is quoted from them; check any detail
that matters against the app itself). Companion to `UX_PLAN.md`; the
additions adopted from this review are listed in its §12.

## 1. What each app does well

| App | Method | Features worth noting |
|---|---|---|
| **Pimsleur** | Audio-first, 30-minute lessons; *graduated interval recall* (a phrase comes back at growing gaps inside the lesson and across lessons); *anticipation drill* (prompt → pause → you say it → you hear it) | one lesson a day; hands-free/driving mode; quick "speed round" review; reading lessons separate from audio; streak |
| **Babbel** | 10–15-minute lessons built around a dialogue; grammar explained in context right after you meet it | a single **Review manager** over everything learned, with modes (flashcards, listening, speaking, writing); a placement test; a daily plan; podcasts and live classes; end-of-lesson summary |
| **LingQ** | Comprehensible input: read and listen to any text; every word is *new* (blue), *learning* (yellow, levels 1–4) or *known*; the **known-words count** is the progress metric | import anything; % new words shown per text; sentence mode (one sentence + audio + gloss); playlists; SRS on saved words; daily goals; courses made of lessons |
| **Drops** | Five-minute timed sessions of visual vocabulary; no typing at first; swipe / match / drag games | topic packs; streak; "Dojo" review of weak words; a separate alphabet app (Scripts); a hard 5-minute cap that makes starting easy |
| Duolingo | A single path of units with checkpoints; short gamified exercises | per-unit *guidebook* (what the unit teaches); streak, daily quests; stories; a clear "you are here" |
| Anki / Memrise | Spaced repetition over cards | Anki: cards made from what you read; Memrise: SRS plus short clips of native speakers |
| Clozemaster | Cloze sentences from a real corpus, ordered by word frequency | sentence-level review; typed or multiple-choice; frequency tiers |
| Readlang / Language Reactor / Beelinguapp | Tap-to-gloss reading with parallel translation; words go to SRS | parallel text; karaoke-style highlighting with audio |
| Glossika / Assimil | Mass sentence repetition; passive then active "wave" | listen–repeat drills; after some weeks, translate old lessons back into the language |

## 2. Where we stand

**Stronger than any of them, for this language**
- Real texts from the first stage, adapted then original, with the source shown beside the adaptation.
- A morphology engine that generates every form of every word (no consumer app has this), with drills and morph-aware feedback ("you typed the genitive").
- A neural voice in reconstructed Classical Attic with word-level highlighting; every story, word and exercise has audio.
- A controlled-vocabulary course (every story word already taught or glossed) with unit tests, reading gates, placement, tracks by interest.
- Skill mastery per grammar point, a mistakes deck, offline use, no cost, no ads.

**Where we lag** (and which app does it best)

| Gap | Best example | Why it matters for our content |
|---|---|---|
| No home, onboarding or daily plan | Babbel, Duolingo | already in `UX_PLAN.md` |
| The reader does not know which words you know | LingQ | we compute coverage but do not colour words or let you mark them; the tap-to-gloss + "add to deck" loop is the heart of input-based learning |
| No headline progress number | LingQ (known words) | we have SRS states and skills but show none as one number |
| Review is split three ways (word decks, skills drills, mistakes) | Babbel Review manager | one Review hub with modes is easier to understand and to open daily |
| No sentence-level review | Clozemaster | we have 264 corpus example sentences plus ~80 stories: cloze on real sentences by frequency is cheap for us and better than isolated cards |
| No hands-free / audio-only mode | Pimsleur, Glossika | our voice is our best asset; a "listen to the unit" playlist with anticipation pauses turns commutes into practice |
| No 5-minute entry point | Drops | a capped quick session lowers the cost of opening the app |
| No end-of-session summary | Babbel, Duolingo | words learned, accuracy, streak, next step — a closing screen per lesson, test and deck |
| No unit overview ("what will I learn") | Duolingo guidebook | planned as the unit page |
| No parallel translation | Beelinguapp, Readlang | we chose Greek-first; a hidden per-sentence English toggle would help beginners without changing that |
| No speaking loop | Pimsleur, Babbel | no speech recognition exists for Ancient Greek, but *record yourself and compare* with the voice is feasible and fits "the app teaches the user" |
| Alphabet practice is four lessons, not a game | Drops Scripts | Stage 0 could gain a letters/breathings/accents mini-drill for the first week |

**Deliberately not adopting**: hearts/lives, leagues and leaderboards, coins, speech-recognition scoring, live classes, chatbots, video clips of native speakers, push-notification nagging. They either don't exist for a dead language or work against a calm reading app.

## 3. What to add (mapped to the UX plan)

Ordered by value ÷ cost; each fits the content we already have.

1. **Known-word states in the reader** (LingQ). Every word in a library text or story is coloured *new / learning / known* from the SRS state (the coverage endpoint already maps forms to entries). Tap a word → gloss card (lemma, short meaning, ▶, forms) with *Known* / *Learn this* (adds the card). Marking words updates the coverage numbers live. → `UX_PLAN` F3 (Library).
2. **One Review hub with modes** (Babbel). *Practice* replaces *Words* in the sidebar: tabs **Review** (today's queue: due words → sentence cloze → weak-skill drill → mistakes, in one session), **Words** (decks and browse, as planned), **Drills** (grammar drills by skill). Modes inside review: read (Greek → meaning), write (meaning → Greek, typed), listen (audio → pick/type), forms. → F4.
3. **Sentence cloze review** (Clozemaster). Backend generator: for a target word, take an example sentence (corpus or story) the learner has seen, blank the form, offer typed or 4-choice; graded like other items, feeds the word's SRS card. → F4 (backend + item type).
4. **Known words counter + weekly goal** (LingQ). One number on Home and Progress: words with a card in the *known* state (interval ≥ 21 days), plus "learning". Weekly goal in words, alongside the minutes goal. → F1/F5.
5. **Quick session (5 min)** (Drops). A Home button that runs a timed mix from the review queue and stops at five minutes with a summary. → F1 (uses the review queue from 2 once it exists; until then, due words only).
6. **Session summary screen** (Babbel/Duolingo). After a lesson check, test, deck or quick session: accuracy, words met/learned, skills moved, streak, minutes, one suggested next step. Shared component. → F1.
7. **Listen mode** (Pimsleur/Glossika). `/learn/listen/[unit]` or a per-lesson "Listen" tab: plays a unit's stories sentence by sentence; options *repeat each sentence twice*, *pause after each sentence* (anticipation: the sentence's picture/English cue first, then the Greek), speed; works with the screen off on iOS as far as the PWA allows. Reuses the stream API and the clip cache. → new phase F3b, after Library.
8. **Unit page / guidebook** (Duolingo). Already planned (F5): arc, lessons, grammar points with links, the unit's words, estimated time.

Optional, after the above:
- **Record and compare** (Pimsleur): in Listen mode and on read-aloud items, record with `MediaRecorder`, play back next to the voice; no scoring. Small.
- **English toggle per story sentence** (Beelinguapp): needs translations of ~80 stories written by agents and checked by a reader; keep hidden by default, respecting the Greek-first decision. Content work, one session.
- **Active wave** (Assimil): lessons finished four or more weeks ago come back as *compose-grc* items (English cue → type the Greek sentence). Fits the reread schedule.
- **Letters game** (Drops Scripts): a tap-first drill for the alphabet, breathings and accents, offered during Stage 0 and to anyone who fails a spelling item.

## 4. Changes this makes to `UX_PLAN.md`

- Sidebar: **Practice** (Review · Words · Drills) instead of Words.
- Home adds the known-words number, the weekly goal and *Quick 5 minutes*.
- F1 adds the session summary and the quick session; F3 adds word states and the tap-to-gloss card; a new **F3b Listen mode**; F4 becomes the Review hub + sentence cloze + decks.
- Progress gets the known/learning/new split and the weekly goal history.
