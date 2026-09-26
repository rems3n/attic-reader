# Reference: the learner's own vocabulary study plan

Source: `greek_vocab_study_plan.xlsx` in the user's Drive folder (read in
full, 1,000 rows + an "About this plan" sheet). Summary only; the sheet
itself is not copied into the repo.

## What it is

- The learner's physical 1,000-card flashcard deck, resequenced into
  **40 batches of 25 words**, ordered by frequency tier, then difficulty,
  then card number. `Card #` is the number printed on the card
  (alphabetical: 1 = ἀγαθός … 1000 = ὠφελέω) and is the stable ID.
- Columns: `Study Plan Batch, Order, Card #, Greek (as printed on card),
  Headword, Meaning, Part of speech, Difficulty, Grammar note,
  Frequency tier, Check card?`
- Tiers: `1 - core` 118 words (batches 1–5), `2 - high` 205 (5–13),
  `3 - common` 84 (13–17), `4 - rarer` 593 (17–40). The tier source list
  is not named in the sheet.
- Difficulty: 1 easy (indeclinables, -ος/-η/-ον, 1st/2nd decl.), 2
  moderate (regular ω-verbs, two-termination adjectives), 3 harder (3rd
  decl., contracts, deponents), 4 hardest (μι-verbs, irregular principal
  parts).
- Part of speech and grammar notes were auto-derived from the citation
  form and are often wrong (εἷς tagged preposition, γῆ "3rd declension",
  βραχύς noun). 198 rows are flagged `verify` because the Greek was OCR'd
  from scans and contains garbage in places.
- No themes, no dates, no spaced-repetition fields. The only method
  guidance: learn batch 1, then 2, keep reviewing earlier batches.

## How the course uses it

- Import the deck as an optional **"My 1000 cards" deck** keyed on
  `Card #`, preserving the 40×25 batch order, with tier and difficulty as
  filters. Treat Greek, POS and grammar note as unverified; match each
  headword to the DCC lexicon where possible and show the DCC entry
  instead.
- The course's own vocabulary order (DCC frequency, 8–12 words per
  lesson) is compatible: tier 1 here ≈ DCC tier 1. Lessons show "batch n"
  badges on words that are also in the learner's deck, so the two
  schedules reinforce each other rather than compete.
- The four-level difficulty taxonomy is worth reusing as a facet in the
  vocab deck builder (it is a morphology-difficulty axis the DCC list
  lacks).
