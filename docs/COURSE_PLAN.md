# Beginner Course — Implementation Plan

Status (2026-09-26): **Phases A and B implemented** (see §10): course
backend, all of Stage 0 and Stage 1 (28 lessons, five unit tests, Reading
gate I), placement test, image-sourcing pipeline (placeholders until the
image pass runs with network access), the course frontend and the light
Reader theme, verified end to end in headless Chromium with the fake voice
(`backend/scripts/e2e/`). Phases C–E remain. Sections below describe the
full design; where they say "exists" it predates this work.

Decisions taken with the user (2026-09-25): setting is **the city of
Athens** (not a farm deme); images are **Creative Commons only** with one
consistent visual identity; Greek-first UI with an English toggle; politics
is its own track; accents lenient until Unit 4; tracks unlock after Unit 9;
stress cue for accent for now. Three visual-style mockups (Museum,
Workbook, Night Reader) were delivered as a design canvas; the user chose
**B, Workbook** (§9.8), then on 2026-09-26 switched to **C, Night
Reader, in a light palette**.

Goal: a trackable beginner-to-reader course inside Attic Reader, in the
spirit of Athenaze, LOGOS (*Lingua Graeca per se illustrata*), *Reading
Greek* and "Alpha with Angela": illustrated continuous story, Greek-first
input, explicit grammar after noticing, lots of retrieval practice, and a
fork into interest tracks (mythology, philosophy, history, politics/city
life) once the basics are in place. End state: the learner opens Xenophon
or Plato in the Reader tab and reads.

---

## 0. Summary

- **Shape:** 4 stages · 15 units · ~90 lessons · 15 unit tests · 3 reading
  gates · 4 interest tracks of 8 lessons each.
- **Every lesson:** illustrated story with audio → vocabulary (auto-enrolled
  in the existing SRS) → grammar note → 15–25 exercises (mixed, ~30 % review
  of older material) → lesson check (6–8 items). Greek questions about the
  Greek text (LOGOS style) from lesson 1.
- **Retention:** SRS for words (exists), skill-level mastery for grammar,
  delayed unit tests, spiral review in every lesson, audio-first passes,
  free recall, retake schedule.
- **Content is original.** Athenaze, LOGOS and *Reading Greek* are
  copyrighted; we copy the *method*, not the text. Original stories for
  stages 0–2; public-domain Perseus texts (already in the library) for the
  tracks, adapted then unadapted.
- **Images throughout, all Creative Commons:** a picture dictionary (~150
  pictures for concrete Stage 1 words), 2–3 story images per lesson, CC0
  museum photographs for culture boxes, inline SVG for grammar diagrams.
  One visual identity: CC0/CC BY vase paintings and museum objects, plus
  our own CC BY-SA line drawings and SVG in a matching palette. Greek
  captions only in Stage 1; no English inside pictures.
- **Reuses what exists:** DCC 524-word lexicon with topic tags, morphology
  engine (generates drills and checks answers), 67 grammar paradigms,
  Kokoro audio + word highlighting, clip cache and pre-render job,
  localStorage progress + sync code, SM-2 SRS.
- **Build order:** skeleton + Stage 0 + Unit 1 end to end first (proves the
  lesson format, exercise engine and progress tracking), then content in
  bulk.

---

## 1. Pedagogical design

### 1.1 Principles (and where each comes from)

| Principle | Source model | How it shows up |
|---|---|---|
| Continuous story, familiar cast, Athens c. 431 BC | Athenaze, LOGOS | One family across 48 story lessons; the war reaches them in Stage 2 |
| Greek explained in Greek, pictures carry meaning | LOGOS, Alpha with Angela | Marginal Greek glosses + pictures before any English; ἐρωτήματα in Greek |
| Explicit grammar, but after exposure | Athenaze, Reading Greek | "Notice" box in the story, then an English grammar note + paradigm |
| Controlled vocabulary, ~10 new words per lesson, frequency-ordered | LOGOS, DCC list | Build script rejects unglossed words not yet introduced |
| Retrieval > re-reading | retention research | Quiz before re-read; production exercises; free recall |
| Spacing and interleaving | retention research | Spiral review items, delayed unit tests, SRS |
| Dual coding | Alpha with Angela | Word + picture + audio; picture-only comprehension checks |
| Read real texts early | Reading Greek | Adapted Xenophon/Apollodorus from Unit 7; originals in tracks |

### 1.2 Lesson anatomy (fixed template)

1. **Εἰκών** — cover panel, title in Greek, one-line Greek summary.
2. **Ἀκούσατε** — audio-first pass (story played, text hidden, 2 picture
   questions). Optional but recommended by the UI.
3. **Ἀνάγνωσις** — illustrated story, 80–150 words (Stage 1) → 250–400
   (Stage 2). Margin glosses in Greek (synonym, picture, antonym,
   ἀντίθετον/= notation as in LOGOS). Tap any word: gloss + ▶ + link to
   the word page. Sentence ▶ with word highlighting (exists).
4. **Λέξεις** — new vocabulary (8–12), each with picture where concrete,
   audio, DCC gloss; one tap adds all to the SRS deck (default on).
5. **Παρατηρήσατε** — "Notice" box: 3–5 highlighted sentences from the
   story showing the new pattern, no English.
6. **Γραμματική** — grammar note in English (short, with the paradigm
   table from `paradigms.py` embedded and speakable) + an SVG diagram
   where useful.
7. **Μελετήματα** — 15–25 exercises, mixed types (see §4), ~70 % on this
   lesson, ~30 % spiral review chosen from weak skills. Fixed spine from
   LOGOS: Α endings cloze → Β word-bank cloze → Γ Greek questions; then
   Athenaze-style items: find-the-forms in the story, transformations,
   parse, paired mirror sentences, Word Building.
8. **Ἐρωτήματα** — 4–6 comprehension questions *in Greek* with Greek
   answers (typed or chosen).
9. **Πολιτισμός** — culture box (English) with one museum photograph.
10. **Ἔλεγχος** — lesson check: 6–8 items, all types, immediate feedback,
    pass ≥ 75 % to mark the lesson complete (retake allowed, always).

### 1.3 Assessment ladder

| Level | When | Items | Feedback | Pass |
|---|---|---|---|---|
| Lesson check | end of each lesson | 6–8 | immediate | 75 % |
| Unit test | unlocked ≥ 1 day after the last lesson in the unit | 25–35, includes an unseen short passage | at the end, with explanations | 80 % |
| Retake | 7 days after passing a unit test, prompted | 12 items drawn from the misses + new | immediate | none (diagnostic) |
| Reading gate | end of Stage 1, Stage 2, each track | unseen passage (adapted → original), 10 Greek questions, 5 parses, 3 translations | at the end | 80 % |
| Placement | optional, on first visit | adaptive, 20–40 items | none | places into a unit |

### 1.4 Retention features (recommendations, all included in the plan)

- **Vocabulary SRS** (exists): lesson words auto-enrolled; deck filter
  "this unit / this stage / this track".
- **Skill mastery** (new): every exercise item is tagged with skills
  (§5.3). Per skill keep `correct, total, streak, last, ewma`. Mastered =
  ewma ≥ 0.85, total ≥ 8, seen on ≥ 2 days ≥ 2 days apart. Weak skills
  feed spiral review and the review quiz.
- **Spiral review**: 30 % of each lesson's exercises are drawn live from
  weak/unpracticed skills of earlier lessons (generated drills, §4.3).
- **Delayed testing**: unit tests unlock after a day; retake after a week.
- **Reread schedule**: the course home suggests one old story to reread
  (with questions) at 1 d, 3 d, 7 d, 21 d after first reading.
- **Audio-first**: "listen before you read" step; dictation exercises.
- **Free recall**: after each unit, "retell the story" with a word bank
  (self-checked against a model summary), and "write 3 sentences about
  the picture".
- **Production ramps**: recognition-heavy early, production-heavy later.
- **Error log**: every miss stored with the item and the learner's answer;
  a "my mistakes" review deck.
- **Light streak / daily goal**: minutes per day chosen by the learner; no
  gamified currency.

---

## 2. Course structure

### 2.1 Overview

```text
Stage 0  Στοιχεῖα      4 lessons   alphabet, breathings, accents, pronunciation, typing
Stage 1  Θεμέλια       Units 1–6   24 lessons + 6 unit tests + reading gate I
Stage 2  Γέφυρα        Units 7–12  24 lessons + 6 unit tests + reading gate II
Stage 3  Ὁδοί (tracks) 4 tracks    8 lessons each + track gate
Stage 4  Ἀναγνώστης    graduation  guided use of the Reader on full texts
```

Tracks unlock after Unit 9 as optional "side readings" and fully after
Unit 12. A learner may do one, several or all tracks.

### 2.2 The story

Setting: **the city of Athens**, 432–431 BC, the eve of the Peloponnesian
War. The family lives in the deme **Κυδαθήναιον**, the central city deme
between the Agora and the Acropolis (Aristophanes' deme), and Ariston's
workshop is in the **Kerameikos**, the potters' quarter. A potter's family
is deliberately chosen: the Agora, Acropolis, Piraeus, Assembly and law
courts are all a walk away, and Attic pottery is the richest source of
Creative Commons imagery for the course (§3.2), so the pictures and the
story share one world.

Cast (original names; nothing shared with Athenaze):

| Name | Role | Notes |
|---|---|---|
| Ἀρίστων | father, potter (κεραμεύς), ~40 | hoplite in Stage 2 |
| Χρυσίς | mother | weaving, household, religion |
| Λύσις | son, 12 | school, palaestra, the learner's stand-in |
| Ἐλπίς | daughter, 9 | Arrephoria / Panathenaea thread |
| Κλεινίας | grandfather | veteran of Salamis; tells myths (feeds the mythology track) |
| Σύρος | enslaved workshop hand | present honestly; culture box on slavery in Unit 2 |
| Λάβρος | the dog | |
| Δημόκριτος | neighbour, chatterbox | politics thread; assembly, law court |
| Ξένος from Miletus | merchant at Piraeus | Ionia, the sea, geography |
| Φιλίππη and her family | cousins from Acharnae | arrive as refugees in 431 (Stage 2) |

Arc: Stage 1 — daily life in the city (house and courtyard, the workshop,
the Agora, school, the Acropolis, a festival, the road to Piraeus, the
harbour). Stage 2 — the Panathenaea, the Assembly debates the war,
Ariston is called up, the Acharnian cousins are evacuated into the city
and lodge with the family, Lysis listens to a philosopher in the Agora, a
law-court scene, the plague year foreshadowed, and finally Lysis reads his
first page of Xenophon.

### 2.3 Stage 0 — Στοιχεῖα (4 lessons)

| Lesson | Content | Exercises |
|---|---|---|
| 0.1 | Alphabet (24 letters, names, Classical Attic values as in the app's G2P), upper/lower, final sigma | letter ↔ sound picture match, listen and pick the letter, type what you hear |
| 0.2 | Vowels and length, diphthongs, breathings, /h/ | minimal pairs by ear (ὁ/ὀ, η/ε, ω/ο), read aloud with audio model |
| 0.3 | Accents (acute, grave, circumflex) as stress cue for now, iota subscript, punctuation, capitalization | mark the accented syllable, type words with accents (keyboard tutorial) |
| 0.4 | Reading whole words and names; first 20 words by picture (ἄνθρωπος, γυνή, οἶκος, ἀγρός…); numbers 1–10 | picture ↔ word, dictation, read-aloud along with audio |

Keyboard note: users have a polytonic layout. Lesson 0.3 includes a short
layout-agnostic drill (type ἄ, ἡ, ῷ, ῥ) and the app accepts NFC or NFD
input.

### 2.4 Stage 1 — Θεμέλια (Units 1–6, 24 lessons)

Grammar sequence follows Athenaze/LOGOS order; vocabulary follows DCC
frequency tiers (tier 1 = ranks 1–125 across Stage 1).

| Unit | Lesson | Story beat | Grammar | Vocabulary focus | Paradigm ids (exist) |
|---|---|---|---|---|---|
| **1 Ἡ ἀγορά** | 1.1 | ὁ Ἀρίστων κεραμεύς ἐστιν | nominative; article; εἰμί 3 sg; οὐ, καί, ἀλλά; τίς/ποῦ | people, house, city | `article`, `logos`, `eimi` |
| | 1.2 | ὁ Ἀρίστων ἐν τῷ ἐργαστηρίῳ πονεῖ | present indicative 3 sg/pl of -ω verbs; ἐν + dat; masc/neut 2nd decl nom/acc/dat | verbs of work, the workshop | `logos`, `doron` |
| | 1.3 | ὁ Λύσις καὶ ὁ Λάβρος ἐν τῇ ἀγορᾷ | accusative object; full 2nd decl sg; adjective agreement (masc/neut) | animals, market goods | `agathos` |
| | 1.4 | ἡ Χρυσὶς ἐν τῷ οἴκῳ | 1st decl -η/-α sg; feminine article and adjectives; εἰς/ἐκ | household, courtyard | `timi`, `chora` |
| **2 Ὁ οἶκος** | 2.1 | ἡ ἡμέρα | present 1/2 sg (ἐγώ, σύ); questions with ἆρα; μέν … δέ | daily routine | `ego`, `sy`, `luo` |
| | 2.2 | οἱ δοῦλοι | plural of article, 1st/2nd decl; present 1/2 pl; genitive of possession | family, slaves, culture box | `logos`, `timi` |
| | 2.3 | ὁ Κλεινίας λέγει μῦθον | imperative sg/pl; vocative; ὦ; prohibitions with μή | speech verbs | |
| | 2.4 | δεῖπνον | contract verbs -άω/-έω present; αὐτός | food, eating | `timao`, `poieo`, `autos` |
| **3 Ἡ πόλις** | 3.1 | ἡ ἑορτὴ ἐν τῇ πόλει | 3rd decl consonant stems (φύλαξ, γέρων) | festival, procession | `phylax`, `geron` |
| | 3.2 | ὁ πολίτης καὶ ὁ νεανίας | masc 1st decl; possessives; οὗτος/ἐκεῖνος | trades, citizens | `polites`, `neanias`, `houtos`, `ekeinos` |
| | 3.3 | ὁ Λάβρος ἀπόλλυται | middle voice present; deponents (γίγνομαι, βούλομαι) | wishing, fearing | `gignomai` |
| | 3.4 | εἰς τὴν ἀκρόπολιν | prepositions with gen/dat/acc; compound verbs | movement, the Acropolis | |
| **4 Ὁ Πειραιεύς** | 4.1 | ἡ ὁδὸς εἰς τὸν Πειραιᾶ | present active participle (attributive, circumstantial); πατήρ, μήτηρ, ἀνήρ | family, roads, walls | `pater`, `aner` |
| | 4.2 | τὸ ἐμπόριον | present middle participle; παύομαι + ptc; uses of the genitive; πᾶς | buying, selling | `pas` |
| | 4.3 | ὁ διδάσκαλος | πόλις, ἄστυ, βασιλεύς; article + participle as noun; impersonals δεῖ, ἔξεστι; τίς/τις | school, letters | `polis`, `basileus`, `tis-indef` |
| | 4.4 | αἱ νῆες | numerals 1–10; acc. of extent vs dat. of time; ναῦς; place adverbs (-θεν, -δε) | sea, ships, numbers | `naus`, `heis`, `dyo`, `treis`, `tettares` |
| **5 Οἱ θεοί** | 5.1 | ἡ θυσία | 2nd aorist (ἔλαβον, εἶπον, ἦλθον); aspect; aorist infinitive and participle | ritual | `lambano` |
| | 5.2 | ὁ Κλεινίας περὶ Σαλαμῖνος | 1st aorist (λύω, consonant stems, contracts, liquids); augment incl. compounds | war, memory | `luo`, `phaino` |
| | 5.3 | ὁ Ἀπόλλων καὶ ἡ Δάφνη (myth) | imperfect; imperfect of εἰμί; historic present; aorist vs imperfect in narrative | body, emotions | |
| | 5.4 | ὁ ἰατρός | relative pronoun and clauses; -εσ- stems (γένος, ἀληθής, τριήρης); reflexives, ἀλλήλων | health | `hos`, `genos`, `alethes`, `heautou`, `allelon` |
| **6 Τὸ ἀργύριον** | 6.1 | τὸ ἀργύριον | comparison of adjectives and adverbs; ἤ and genitive of comparison | money, trade | `beltion` |
| | 6.2 | ὁ ξένος ἐκ Μιλήτου | demonstratives οὗτος, ὅδε, ἐκεῖνος in full; interrogative vs indefinite adverbs; time expressions | travel, geography | `houtos`, `hode`, `ekeinos` |
| | 6.3 | ἡ Ἐλπὶς ὑφαίνει | -όω contracts; νοῦς; root aorists ἔβην, ἔγνων, ἔστην; δύναμαι, ἐπίσταμαι | weaving, ability | `deloo`, `nous`, `baino` |
| | 6.4 | Reading gate I | consolidated review; adapted Apollodorus (short myth, 120 words, unseen) | | |

Reference notes for all of this live in `docs/reference/` (Athenaze Book I
and II sequences, Workbook exercise types, LOGOS method, the Major 80 %
list, the learner's own deck and study plan).

Order check against Athenaze Book I (see `docs/reference/athenaze-book1-sequence.md`):
Units 1–2 ≈ Ch. 1–5, Unit 3 ≈ Ch. 5–7, Unit 4 ≈ Ch. 8–10, Unit 5 ≈
Ch. 11–13, Unit 6 ≈ Ch. 14–16. The future is deferred to Stage 2, as in
Athenaze. Each unit also carries a Word Study (English derivatives, from
`cognates.json`) and a Word Building (Greek word family) item.

### 2.5 Stage 2 — Γέφυρα (Units 7–12, 24 lessons)

Chronology (decided 2026-09-26 while starting Phase C): Unit 7's festival
is the **City Dionysia of spring 431** (Euripides' *Medea*), not the
Panathenaea, because Stage 1 ends in spring 431 and the Panathenaea fall in
midsummer, after the evacuation; the Panathenaea now take place inside the
crowded walls in 9.3. Unit 12 is an epilogue (c. 370) so that Xenophon and
Plato can be read without anachronism. Originals per lesson and the story
beats are in `docs/AUTHORING.md` (Stage 2).

| Unit | Lesson | Story beat | Grammar | Text tie-in |
|---|---|---|---|---|
| **7 Τὰ Διονύσια** | 7.1 | ἡ πομπή | future (incl. εἰμί, liquid futures); εἶμι; future participle of purpose | |
| | 7.2 | ὁ ἀγών | -μι verbs I: δίδωμι, τίθημι; uses of αὐτός reviewed; ταχύς-type adjectives | `didomi`, `tithemi`, `tachys` |
| | 7.3 | ἡ τραγῳδία (*Medea*) | genitive absolute; attributive vs predicate position; further uses of the article | adapted Apollodorus 1.9.28 (Medea) |
| | 7.4 | ἡ νύξ | ἵστημι, ἀφίσταμαι, καθίστημι; supplementary participles (λανθάνω, τυγχάνω, φαίνομαι, φθάνω) | `histemi` |
| **8 Ἡ ἐκκλησία** | 8.1 | ὁ Δημόκριτος λέγει | subjunctive: hortatory, deliberative, prohibitive, purpose (ἵνα/ὅπως/ὡς), ἐάν | |
| | 8.2 | περὶ τοῦ πολέμου | fear clauses; indefinite clauses with ἄν (ὅστις ἄν, ἐπειδάν, ἕως ἄν) | adapted Thucydides 1.1 (exists in library) |
| | 8.3 | ἡ ψῆφος | δείκνυμι; indirect statement with ὅτι/ὡς; indirect questions | `deiknymi` |
| | 8.4 | ὁ Περικλῆς | present and imperfect passive; prepositional prefixes and euphony | adapted Thuc. Pericles |
| **9 Ὁ πόλεμος** | 9.1 | οἱ Λακεδαιμόνιοι | indirect statement with infinitive and participle; φημί; relative attraction | `phemi`; adapted Xen. Hell. 2.2 (exists) |
| | 9.2 | οἱ Ἀχαρνῆς ἐν τῷ ἄστει (the cousins arrive) | aorist and future passive; aorist of deponents; ὅπως + future indicative | |
| | 9.3 | ἐντὸς τῶν τειχῶν | optative: forms, wishes, subordinate clauses in secondary sequence | |
| | 9.4 | Ἀρίστων ὁπλίτης | optative in indirect speech; uses of gen./dat./acc. in full; correlatives | **tracks unlock as side readings** |
| **10 Ἡ ἀγορὰ τῶν λόγων** | 10.1 | ὁ σοφός ἐν τῇ ἀγορᾷ | perfect and pluperfect middle-passive; πρίν ἄν; articular infinitive | adapted Plato Apol. 17a (exists) |
| | 10.2 | ὁ Λύσις ἐρωτᾷ | perfect and pluperfect active; ἕστηκα, οἶδα; uses of ὡς | `oida` |
| | 10.3 | τί ἐστιν ἡ ἀρετή; | potential optative; result clauses ὥστε; accusative absolute | adapted Xen. Mem. 1.1 (exists) |
| | 10.4 | ὁ Κλεινίας ἀποθνῄσκει | conditional sentences, all six types | |
| **11 Τὸ δικαστήριον** | 11.1 | ἡ δίκη | 3rd-person imperatives; verbal adjectives -τός, -τέος | adapted Lysias 1 (opening) |
| | 11.2 | οἱ μάρτυρες | negatives (οὐ/μή, μὴ οὐ, οὐ μή); verbs of hindering; summary of participle uses | |
| | 11.3 | ἡ ἀπολογία | crasis, elision, prodelision; particles (γε, δή, τοι, μέντοι, οὖν) | |
| | 11.4 | ἡ ψῆφος τῶν δικαστῶν | dual (recognition only); Attic vs Ionic/Koine forms to recognize; reading strategy | |
| **12 Ὁ ἀναγνώστης** | 12.1 | ὁ Λύσις ἀναγιγνώσκει | connected reading with running vocabulary only | Xen. Anab. 1.1 unadapted with glosses (exists) |
| | 12.2 | ὁ Ξενοφῶν | connected reading: 200-word original | Xen. Anab. 4.7 (exists) |
| | 12.3 | ὁ Σωκράτης | connected reading: Plato | Crito 43a (exists) |
| | 12.4 | Reading gate II | unseen original (Xenophon), unglossed except proper names | |

### 2.6 Stage 3 — Ὁδοί (four tracks, 8 lessons each)

Each track has the same ladder so progress is comparable:

| Lessons | Text level | Support |
|---|---|---|
| 1–3 | adapted (simplified syntax, core vocabulary) | full glosses, pictures, Greek questions |
| 4–6 | lightly adapted original (cuts, not rewrites) | glosses for words outside DCC + track list |
| 7 | original | running vocabulary only |
| 8 | track gate | unseen original passage, questions, parsing |

Track vocabulary: DCC words tagged with the matching topic (exists:
`topics` facet) plus a curated 80–120-word track list (new,
`course_data/tracks/<id>.vocab.json`) drawn from the passages.

| Track | Texts (all public domain, Perseus) | Culture images |
|---|---|---|
| **Μυθολογία** | Apollodorus *Library* (1.1, 1.7, 2.4, 3.14 exist) → more Apollodorus; Palaephatus; a Lucian dialogue of the gods | vase paintings (CC0: Met, Cleveland, Getty, Walters) |
| **Φιλοσοφία** | Plato *Apology*, *Crito* (exist), *Euthyphro* opening, *Republic* 1 (exists); Xenophon *Memorabilia* (exists); Epictetus *Enchiridion* excerpts (later Greek, flagged) | busts, Academy site, papyri |
| **Ἱστορία** | Xenophon *Anabasis*, *Hellenica* (exist); Thucydides 1.1 (exists), 2.34–46 funeral oration adapted; Herodotus excluded (Ionic) per user | maps (SVG), hoplite gear, trireme model (CC0) |
| **Πολιτεία** (politics & city life) | Old Oligarch (*Ath. Pol.* pseudo-Xen.) excerpts; Aristotle *Ath. Pol.* on the Assembly; Lysias 1, 12 excerpts; Demosthenes *Olynthiac* 1 opening; Aristophanes *Acharnians* 1–42 (metre flagged) | Pnyx, ostraka, kleroterion, agora plan (SVG) |

### 2.7 Stage 4 — Ἀναγνώστης

Not lessons: a guided mode of the existing Reader. Suggested first books
with DCC coverage percentage shown; "unknown words in this passage"
count from the learner's SRS state; one-tap add unknown words to the
deck; OCR of the learner's own Athenaze/Loeb pages (exists).

---

## 3. Content

### 3.1 Text

- **Original Greek** for Stage 0–2 stories, all exercises and all Greek
  questions. Written to the controlled-vocabulary rule: every word in a
  lesson story is (a) introduced in this or an earlier lesson, (b) a
  proper name, or (c) glossed in the margin. The build script enforces it.
- **Accent correctness** is checked mechanically: every word form must be
  producible by the morphology engine or be listed in a whitelist with a
  reason; enclitic accentuation (ἄνθρωπός ἐστιν, οἴκῳ ἐστίν) checked by a
  new `accent.enclitic()` helper.
- **Word budget**: 8–12 new words per lesson; DCC tier 1 (125 words) in
  Stage 1, tiers 2–3 in Stage 2, tier 4 spread over tracks. Function words
  frontloaded. 524 DCC words + ~250 story words (city, workshop, family, festival)
  + 4 × ~100 track words ≈ 1,150 words by the end.
- **Sample, Lesson 1.1 story** (draft, to be reviewed):

  > ὁ Ἀρίστων ἄνθρωπός ἐστιν. ὁ Ἀρίστων Ἀθηναῖός ἐστιν. ὁ Ἀρίστων
  > κεραμεύς ἐστιν· οὐ ναύτης ἐστίν. ὁ Ἀρίστων ἐν τῇ ἀγορᾷ ἐστιν. ἡ ἀγορὰ
  > μεγάλη ἐστίν, ἀλλὰ καλή. ἡ Χρυσὶς γυνή ἐστιν. ἡ Χρυσὶς ἐν τῷ οἴκῳ
  > ἐστίν. τίς ἐστιν ὁ Ἀρίστων; κεραμεύς ἐστιν. ποῦ ἐστιν ἡ Χρυσίς; ἐν τῷ
  > οἴκῳ ἐστίν.

  Margin: ἄνθρωπος [picture], κεραμεύς [picture: potter at the wheel, from
  a CC0 vase], ναύτης [picture: man on ship], ἀγορά [picture], οἶκος
  [picture], μεγάλη ↔ μικρά [two pictures], οὐ = "✗".
- **Grammar notes**: short English, one concept, one table, one diagram;
  tone of Athenaze's grammar sections. Cross-link to `/grammar/<id>`.
- **Culture boxes**: 150–250 words English each, one image, one primary
  source line in Greek with translation where possible.
- **Public-domain older readers** as inspiration and for extra reading
  (verify PD status per edition): Rouse, *A Greek Boy at Home* (1909,
  natural-method Attic; closest ancestor to LOGOS); Freeman & Lowe, *A
  Greek Reader for Schools* (1917). Use for ideas and optional extra
  readings, not as lesson text, to keep style consistent.

### 3.2 Images

**Decision: Creative Commons only, one visual identity.** Every image is
CC0, CC BY or CC BY-SA (or our own work released CC BY-SA). No generated
imagery, no all-rights-reserved stock. The brand ethos is "Attic pottery":
the terracotta, black and cream of red-figure and black-figure ware, so
museum photographs, our own drawings and the UI palette read as one thing.

Four kinds, one manifest, all with Greek + English alt text, credit,
license and source URL.

| Kind | Count (est.) | Source / treatment | Use |
|---|---|---|---|
| Picture dictionary | ~150 (Stage 1 concrete nouns, verbs, adjectives) | (1) details cropped from CC0 vase photographs (a potter at the wheel, a dog, a warrior, a woman weaving, a ship) with background knocked out to a flat cream field; (2) where no vase detail fits, our own two-tone SVG/line drawings in the same palette, released CC BY-SA | margin glosses, vocab cards, picture-match, flash cards |
| Story images | 2–3 per story lesson ≈ 130 | CC0/CC BY museum photographs and Commons photographs of the real places (Agora, Acropolis, Kerameikos, Piraeus, Pnyx) and of vase scenes matching the beat (school scene, symposium, procession, workshop); recurring characters are shown by a fixed *attribute*, not a drawn face: Ariston = a potter's wheel/kylix motif, Lysis = a writing tablet, Chrysis = a loom, Kleinias = a staff, Labros = the dog from the Met's dog askos | story sections, audio-first questions, "describe the picture" |
| Culture photographs | ~50 | CC0 open access: The Met, Cleveland Museum of Art, Getty Open Content, Walters, Rijksmuseum, Art Institute of Chicago, Smithsonian; British Museum is CC BY-NC-SA and excluded unless the product stays non-commercial; Wikimedia Commons CC0/CC BY/CC BY-SA with author credit | culture boxes, track lessons |
| Grammar diagrams | ~30 | our own inline SVG, theme-aware (uses the app's CSS tokens), CC BY-SA | case "map", preposition picture (ship: ἐν/εἰς/ἐκ/πρός/ἀπό), verb timeline, voice diagram, conditional ladder |

Sourcing workflow: `scripts/build_images.py` takes a CSV of
`(id, source_url, license, credit, crop box, caption_grc, caption_en)`,
downloads once, verifies the license text from the source API where one
exists (Met, Cleveland, AIC, Smithsonian all expose rights fields), crops
and resizes (WebP ≤ 60 KB, 3:2 or 1:1), applies the uniform cream field
and writes `images/manifest.json`. A CC BY-SA or CC BY image keeps its
attribution visible in the UI (tap the badge) and in an
`/course/credits` page; CC0 gets a credit anyway. Consistency rules:
crop to one subject, no museum labels or rulers in frame, uniform 12 %
padding, colour-graded to the palette, no English text in the image.

This sandbox cannot download or process images (egress policy), so the
plan ships placeholders (cream panel with the Greek caption and a CC badge)
and the manifest first; the image pass is a separate workstream that can
run locally or in CI with network access.

Manifest shape:

```json
{
  "id": "kerameus",
  "file": "course/pics/kerameus.webp",
  "kind": "dictionary",
  "alt_grc": "κεραμεὺς ἐν τῷ ἐργαστηρίῳ",
  "alt_en": "A potter at the wheel, detail of an Attic red-figure kylix",
  "credit": "The Metropolitan Museum of Art, Open Access",
  "license": "CC0 1.0",
  "source_url": "https://www.metmuseum.org/art/collection/search/…",
  "crop": [420, 310, 1400, 1400],
  "words": ["κεραμεύς", "ἐργαστήριον", "τροχός"]
}
```

### 3.3 Audio

- Every story sentence, gloss word, exercise stem and answer key is
  rendered by Kokoro through the existing clip cache; the pre-render job
  gets a "course" pass after the library and headwords (Stage 0–1 first).
- Dictation and listen-and-pick exercises use the same clips.
- Stage 0 uses per-letter/per-syllable clips (short phoneme strings; check
  Kokoro behaves on 1–2 phoneme inputs; fall back to whole-word examples).

---

## 4. Exercises, quizzes, tests

### 4.1 Exercise types (engine primitives)

| id | Learner does | Grading | Skills it can carry |
|---|---|---|---|
| `pick-picture` | choose the picture matching a word/sentence (or the sentence matching a picture) | exact | vocab, syntax |
| `listen-pick` | hear a clip, choose word/sentence/picture | exact | listening, vocab |
| `match` | pair columns (word ↔ picture, form ↔ description, Greek ↔ Greek synonym) | exact | vocab, morphology |
| `cloze-choice` | fill a gap from 3–5 options | exact | morphology, syntax |
| `cloze-type` | type the missing word/form (keyboard) | normalized string match, several accepted answers, accent-strict or -lenient by setting | morphology |
| `produce-form` | "dative plural of λόγος" → type | morph engine generates and checks | morphology |
| `parse` | tap chips: case · number · gender / person · number · tense · mood · voice | exact set match | morphology |
| `transform` | rewrite sentence: singular → plural, present → aorist, active → passive | normalized match against accepted set | morphology, syntax |
| `reorder` | drag/tap words into a sentence | exact or any listed order | syntax |
| `true-false-grc` | ἀληθὲς ἢ ψευδές; about the story | exact | comprehension |
| `answer-grc` | answer a Greek question in Greek (type or choose) | normalized match + accepted variants; model answer shown | comprehension, production |
| `translate-en` | translate Greek → English | self-graded against model with a 3-point rubric | comprehension |
| `compose-grc` | English → Greek (typed) | normalized match against accepted set; diff shown | production |
| `dictation` | hear, type Greek | normalized match; accent-lenient by default | listening, spelling |
| `describe-picture` | write 2–3 Greek sentences about a panel | self-graded with word bank and model | production |
| `read-aloud` | read along with audio, self-mark | none (no recording) | pronunciation |
| `retell` | free recall with word bank | self-graded against summary | comprehension |
| `locate` | tap every word in the story that is (e.g.) a dative / an imperative / a participle | exact set match | morphology, reading |
| `label` | code a form or word you just produced (S / DO / IO; case use A–I; attributive / predicate) | exact | syntax |
| `endings-cloze` | fill blanked endings in a continuous passage (LOGOS Μελέτημα Α) | normalized match per gap | morphology |
| `bank-cloze` | fill whole words from a word bank (LOGOS Μελέτημα Β) | exact | vocab, syntax |
| `word-family` | from a root, produce or pick compounds and cognates; English derivatives shown (Word Study / Word Building) | exact set / normalized | vocab |
| `continue-story` | write 2–3 Greek sentences continuing the tail reading (Stage 2) | self-graded against model, word bank | production |
| `paradigm-transfer` | give the forms of verb B that correspond to the forms you produced for verb A | morph engine | morphology |

Normalization (shared TS/Python, parity fixtures generated by Python):
NFC, final sigma, trim/collapse spaces, optional strip of accents and
breathings (lenient mode), Greek question mark `;` and ano teleia
handling, grave → acute equivalence.

### 4.2 Item authoring format

Hand-written items live in the lesson file; each carries `skills`, an
`explain` string shown on a miss, and optional `image`/`audio` refs.

```json
{
  "type": "cloze-type",
  "prompt": "ὁ Ἀρίστων ἐν τ__ ἐργαστηρί__ ἐστιν.",
  "gaps": [{"answers": ["ῷ"]}, {"answers": ["ῳ"]}],
  "skills": ["noun.decl2.dat.sg", "art.dat.sg.neut", "prep.en.dat"],
  "explain": "ἐν takes the dative; 2nd-declension dative singular ends in -ῳ (ᾳ/ῃ/ῳ carry iota subscript).",
  "audio": "auto"
}
```

### 4.3 Generated drills (the morphology engine's payoff)

`GET /api/course/drill?skills=noun.decl2.dat.sg,verb.pres.act.ind.3pl&n=8&vocab=lesson:1.2`
returns fresh `produce-form`, `parse`, `cloze-choice` and `transform`
items built from `decline_entry`/`conjugate_entry` over words the learner
has met (vocab scope = lessons completed). Distractors are neighbouring
cells of the same table (dat sg vs gen sg, 2 pl vs 3 pl). Used for spiral
review, the review quiz and unit-test parsing sections, so item pools do
not go stale.

### 4.4 Quizzes and tests

- **Lesson check**: 6–8 hand-picked items (`quiz` block in the lesson),
  immediate feedback, 75 % to complete.
- **Unit test** (`course_data/tests/unit-<n>.json`): sections
  1 vocabulary (8, listen/picture/match) · 2 forms (8, produce/parse,
  half generated) · 3 sentences (8, cloze/transform/reorder) ·
  4 reading (unseen 60–120-word passage in the unit's grammar + 5 Greek
  questions + 2 translations). Delayed feedback with explanations; 80 %.
  Unlocks ≥ 24 h after the last lesson check.
- **Retake**: automatic 7 days after a pass; 12 items = misses + weakest
  skills; result recorded but no gate.
- **Reading gates**: as §1.3; the passage is *not* in the library or any
  lesson.
- **Placement**: adaptive walk over unit tests' section-2/3 items; stops
  after 3 consecutive misses in a unit; places at that unit with earlier
  lessons marked "skipped (placement)" and their vocab enrolled.
- **Review quiz** (`/course/review`): 10 items from weak skills + due
  vocabulary; available any time; suggested when nothing is due.

---

## 5. Data model

### 5.1 Content files (backend, committed)

```text
backend/app/course_data/
  course.json                 stages → units → lesson ids, gates, track ids
  skills.json                 skill taxonomy (id, label, parent, paradigm ref)
  lessons/<lesson-id>.json    one lesson (see 5.2)
  tests/unit-<n>.json         unit tests; gates/gate-<n>.json
  tracks/<track>.json         track manifest, vocab list, lesson ids
  images/manifest.json        §3.2
  authoring/*.md              source: Markdown+YAML front matter, compiled by scripts/build_course.py
frontend/public/course/pics/  images (WebP/SVG)
```

### 5.2 Lesson JSON (compiled)

```json
{
  "id": "1.1", "unit": 1, "stage": 1, "title_grc": "ὁ Ἀρίστων κεραμεύς ἐστιν", "title_en": "Ariston is a potter",
  "cover": "panel-1-1-a",
  "story": [{"text": "ὁ Ἀρίστων ἄνθρωπός ἐστιν.", "image": null, "glosses": {"ἄνθρωπός": {"pic": "anthropos"}}}, ...],
  "vocab": [{"id": "anthropos", "pic": "anthropos"}, {"lemma": "Ἀρίστων", "extra": true, "gloss_grc": "ὄνομα ἀνδρός"}],
  "notice": ["ὁ Ἀρίστων γεωργός ἐστιν.", "ἡ Χρυσὶς γυνή ἐστιν."],
  "grammar": {"md": "...", "paradigms": ["article", "eimi"], "diagram": "case-map-nom"},
  "exercises": [...], "questions_grc": [...], "culture": {"md": "...", "image": "acharnai-plain"},
  "quiz": [...], "skills": ["noun.nom.sg", "verb.eimi.pres.3sg", "part.ou"], "review_skills_hint": []
}
```

### 5.3 Skill taxonomy (excerpt)

```text
alpha.letters  alpha.breathings  alpha.accents
noun.decl1.<case>.<num>  noun.decl2.<case>.<num>  noun.decl3.<stem>.<case>.<num>
adj.agree  adj.compare
art.<case>.<num>.<gender>
pron.<kind>
verb.<tense>.<voice>.<mood>.<person><num>   e.g. verb.aor2.act.ind.3sg
verb.contract.<a|e|o>  verb.mi.<lemma>
prep.<lemma>.<case>
syntax.gen-abs  syntax.ind-statement.<hoti|inf|part>  syntax.cond.<type>  syntax.purpose  syntax.result
read.comprehension  listen  spell.accents  produce.sentence
```

Skills nest by prefix, so mastery can roll up (`verb.aor2.*`).

### 5.4 Progress (frontend document, synced with the existing sync code)

Extend `Progress` to `version: 2` with `migrateProgress()`:

```ts
course: {
  track?: "mythology" | "philosophy" | "history" | "politics";
  placement?: { unit: number; at: number };
  lessons: Record<string, { status: "locked"|"open"|"in-progress"|"done"|"skipped"; best: number; attempts: number; firstDone?: number; lastDone?: number; step?: number }>;
  tests: Record<string, { attempts: { at: number; score: number; misses: string[] }[]; passedAt?: number; retakeDue?: number }>;
  skills: Record<string, { correct: number; total: number; streak: number; last: number; ewma: number; days: string[] }>;
  errors: { item: string; lesson: string; answer: string; at: number }[];   // capped at 500
  rereads: Record<string, number[]>;                                          // lesson id → timestamps
  goal: { minutesPerDay: number };
  activity: { day: string; minutes: number; items: number }[];              // 90 days
}
```

Size stays well under the 2 MB server cap; `errors` is capped. Merge rule
for sync: lessons/tests by newest timestamp per key, skills by larger
`total` (then newer `last`), errors union-deduped by `(item, at)`.

---

## 6. API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/course` | stages, units, lesson summaries (title, skills, word count, has-audio), gates, tracks |
| GET | `/api/course/lesson/{id}` | compiled lesson JSON with resolved vocab entries and image records |
| GET | `/api/course/test/{id}` | unit test / gate (generated sections filled at request time, seeded per attempt) |
| GET | `/api/course/drill` | generated drill items (§4.3) |
| GET | `/api/course/track/{id}` | track manifest + lessons + vocab list |
| POST | `/api/course/check` | optional server-side normalization/grading for typed answers (used when the client wants morph-aware feedback, e.g. "you gave the genitive") |
| GET | `/api/course/images` | image manifest |
| PUT/GET | `/api/progress/{code}` | exists; document grows a `course` key |

Grading stays client-side for instant, offline feedback; `/check` is an
enhancement that names the form the learner actually typed (via the morph
engine's reverse lookup over the lesson's vocabulary).

---

## 7. Frontend

Routes (Next.js app dir, `AppNav` gets a **Course** tab first):

| Route | Screen |
|---|---|
| `/course` | course home: stage map (units as cards, lessons as dots), today's suggestions (continue · due vocab · reread · review quiz), streak/goal, track chooser after Unit 9 |
| `/course/lesson/[id]` | lesson player: stepper over the 10 sections; sticky ▶ bar reused from the reader; progress saved per step |
| `/course/test/[id]` | test runner: timer optional, no feedback until submit, results page with explanations and "add misses to review" |
| `/course/review` | review quiz from weak skills + due cards |
| `/course/track/[id]` | track home |
| `/course/placement` | placement test |
| `/course/skills` | mastery grid by skill family, tap → paradigm/lesson |

Theme: style C in light mode (§9.8) is the app-wide theme, applied to the
existing Read / Vocab / Grammar screens as well, via CSS tokens in
`globals.css` (light only at first; C's dark palette later).

Components (new): `StoryPanel` (image + sentences with glosses and word
highlight), `Gloss` popover, `ExerciseRunner` + one component per type,
`GreekInput` (NFC, final-sigma fix, accent-lenient toggle, on-screen
polytonic helper for missing keys), `SkillGrid`, `LessonStepper`,
`PictureGrid`, `Diagram` (SVG by id). Reused: `Speak`, `Highlight`,
`FormsTable`, SRS study screen (deck preset "lesson 3.2").

Mobile: all exercises tap-first; typed items get the keyboard once per
screen; panels 3:2 full width; offline: lesson JSON + clips cached in the
PWA service worker after first open.

---

## 8. Build pipeline and quality checks

`backend/scripts/build_course.py` compiles `authoring/*.md` → JSON and
fails on:

1. Unglossed word not yet introduced (controlled vocabulary).
2. Word form not derivable by the morph engine and not whitelisted.
3. Enclitic accent violations; missing final sigma; NFD leakage.
4. Exercise answers that do not normalize to themselves; `produce-form`
   answers that disagree with the engine.
5. Missing image ids, missing license/credit, alt text absent.
6. Skill ids not in `skills.json`; lesson introduces a skill with no
   exercise on it; unit test lacks a section.
7. Per-lesson stats outside budget (new words > 12, story words > cap).

Tests (pytest): schema of every lesson; controlled-vocab check runs as a
test; drill generator produces valid items for every skill; API routes;
TS: normalization parity fixtures, SRS/mastery pure functions (vitest),
exercise components (a couple of interaction tests), e2e headless pass
through Lesson 1.1 with the fake TTS (pattern exists in
`scratchpad/e2e_vocab.py`).

---

## 9. Decisions

Taken (2026-09-25):

1. **Setting** — the city of Athens, 432–431 BC; a potter's family in
   Kydathenaion with a Kerameikos workshop (§2.2).
2. **Images** — Creative Commons only, one "Attic pottery" visual identity
   (§3.2).
3. **English in Stage 1** — Greek-first with a "show English" toggle per
   section.
4. **Politics** is its own track.
5. **Accent strictness** — lenient in typed answers until Unit 4, then
   strict, per-user override.
6. **Tracks unlock** after Unit 9 as side readings, fully after Unit 12.
7. **Pitch accent** — stress cue for now; pitch notation later.

8. **Visual style: C "Night Reader", in a light palette** (2026-09-26; it
   replaced B "Workbook", chosen on 2026-09-25 and built in Phases A–B).
   Paper ground `#f6f4ee`, white cards, stone panels `#eeebe3`, ink
   `#1c2024`, muted `#5a6168`, hairlines `#dcd8ce`; one sage accent: C's
   `#a3b18a` for fills (lesson dots, underlines, highlights) and a darker
   `#4e6136` for text, links and filled buttons so both pass WCAG AA on
   white. Literata for Greek and headings (Greek Extended, so polytonic),
   IBM Plex Sans for the interface at 400–600. Flat surfaces: 1 px
   borders, 10–14 px radii, no offset shadows; the spoken or looked-up word
   sits on a pale sage wash `#dfe7c9`. Glossed words carry a sage
   underline; ▶ is an outlined sage circle that fills on hover. Tokens live
   in `frontend/app/globals.css`; class names are unchanged from the
   Workbook theme. Light only for now; a dark variant (C's original) can be
   added as a second token set.

---

## 10. Implementation phases

| Phase | Deliverable | Depends on |
|---|---|---|
| **A. Skeleton** — DONE | `course_data` schemas, `build_course.py` validator, skills taxonomy, `/api/course*` + `/check` + `/drill`, progress v2 + migration + merge, `/course` home, 10-step lesson player with all exercise modalities (25 item types), test runner, review quiz, Stage 0 (4 lessons) and Unit 1 (4 lessons + test) authored with placeholder images, course pre-render pass, Workbook theme app-wide, e2e harness | — |
| **B. Stage 1 content** — DONE (images pending) | Units 2–6 authored (20 lessons, ~110 course-only words with engine forms, 260 placeholder image records), unit tests 2–5, Reading gate I, generated drills (decl. 3 subgroups, deponent-first middle), placement test, `/course/credits`, typed-form feedback from `/check`, `build_images.py` + `sources.csv` (the image pass itself needs network: run locally, then commit `frontend/public/course/pics/` and the manifests) | A; image pass: local run |
| **C. Stage 2 content** — DONE (photographs pending) | Units 7–12 (24 lessons; Unit 7 is the Dionysia, Unit 12 an epilogue c. 370), unit tests 7–11, Reading gate II (unseen Xenophon), 47 own SVG diagrams and maps, original-text pipeline (`build_course_texts.py`, 9 Perseus passages + library passages, `original` + per-sentence `orig` alignment, "the original" panel), full participle and comparison declension, Stage 2 drill skills, unit-test passage glossaries; photographs sourced as `sources.csv` rows for the local image pass | B |
| **D. Tracks** — DONE (photographs pending) | 4 tracks × 7 lessons + a track gate each (Apollodorus/Lucian; Plato/Xenophon; Thucydides/Xenophon; *Ath. Pol.*/Lysias/Demosthenes), track lists of 85–92 words, `/course/track/[id]`, track gating (1–3 after 9.4, 4–7 after 12.4), Stage 4 guided reading (`/api/analyze`: lexicon/core coverage per text and per library passage, new words → `/vocab?words=`), 5 new SVG maps/diagrams | C |
| **E. Polish** — mostly DONE | offline caching (service worker) ✓, skills grid ✓, mistakes deck ✓, accessibility pass (axe clean) ✓, navigation (bottom tab bar, breadcrumbs, footer) ✓, dual + verbal adjectives in the engine ✓; still open: content review by a second reader, real-voice check of all story clips | any |

Suggested first session: Phase A end to end. The success test is a
learner completing Lesson 1.1 on a phone with audio, pictures
(placeholders), Greek questions, a passing lesson check, and their
progress surviving a reload and a sync push/pull.

---

## 11. Risks and mitigations

- **Content volume** is the real cost (~90 lessons × ~20 items). Mitigate
  with generated drills for morphology, a tight authoring format, and
  shipping stage by stage. Stage 0 + Unit 1 first.
- **Greek quality** (accents, idiom). Mechanical checks above plus a
  reviewer pass per unit; every lesson carries a "report an error" link
  like the forms tables already do.
- **Image consistency** across ~280 CC pictures from many museums.
  Uniform crop, padding and colour grading in `build_images.py`; a
  character is a fixed attribute, not a face; review checklist per unit.
  Placeholders keep engineering unblocked.
- **Image coverage**: some concrete words will have no good vase detail.
  Fallback is our own SVG in the same palette, released CC BY-SA, never a
  generated image.
- **Licensing**: all text original or PD; DCC list CC BY-SA (attribution
  exists); images CC0/CC BY/CC BY-SA with per-image credit and a credits
  page; CC BY-NC sources excluded; nothing from Athenaze, LOGOS or
  *Reading Greek* is reproduced.
- **Audio on CPU host**: course adds several thousand short clips; the
  pre-render job already yields to users and caches to disk; order Stage
  0–1 first and render tracks lazily.
