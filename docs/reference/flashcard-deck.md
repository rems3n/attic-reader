# Reference: the learner's 1,000-card flashcard deck

Source: `greek_flashcards_1000.pdf` and its four parts in the user's Drive
folder; part 1 (cards 1–250) was read in full. Summary only.

## What it is

- A scanned commercial-style deck, printed 30 cards per sheet, ordered
  strictly **alphabetically** (1 ἀγαθός … 250 ἕκαστος; the whole deck is
  about 1,000 cards). Card numbers are alphabetical positions, not
  frequency ranks. The same numbering is the `Card #` in the learner's
  study-plan spreadsheet (`learner-study-plan.md`).
- Each card: headword with lexical info (nouns with genitive and
  article, adjectives with three endings, verbs with **full principal
  parts**, indeclinables labelled), up to seven numbered **related words**
  (cognates, compounds, idioms: ἐπ' ἀσπίδα, ἀλλὰ γάρ), **English
  derivatives** (Metabolism, Symbol, Hyperbole), and a back with the gloss
  plus a gloss per related word. An asterisk marks poetic or Homeric
  items.
- Absent: frequency, example sentences, mnemonics, images, topic tags.
- Not the DCC list (includes non-core words such as γλαύξ, δάφνη,
  βάρβιτος), not Major's list, not Athenaze chapter vocabulary. Attic
  spellings (ἀλλάττω, γλῶττα).
- The text layer is OCR and noisy, especially in the small-print related
  words; treat Greek from this file as unverified.

## How the course uses it

- The **related-words cluster** is the model for a "word family" panel on
  the word page and for the word-building exercise type (root → compounds
  and cognates, with the English derivatives the app already has in
  `cognates.json`).
- Import as the optional "My 1000 cards" deck (see `learner-study-plan.md`),
  matching headwords to DCC and Major entries; unmatched cards are shown
  with the OCR'd gloss flagged "unverified".
- Principal parts on cards agree with the app's morphology engine output
  in the spot checks made (αἱρέω, βάλλω, ἀκούω); use the deck as an extra
  gold source for `test_morph_verb.py` after cleaning.
