# Reference: Wilfred E. Major, "Core Greek Vocabulary for the First Two Years of Greek at LSU" (the 80 % list)

Source: two identical PDFs in the user's Drive folder
(`323989518-Major-Wilfred-E-Greek-Vocabulary-80-List-pdf.pdf` and
`ancient-greek-attic-greek-vocab.pdf`), read in full.

## What it is

- ~1,100 lemmas that make up about 80 % of running words in the Perseus
  corpus (3.8 M words, list compiled 2004), with proper names removed,
  look-alike rare words dropped, and a few culturally important words
  added. 404 verbs (247 base + 157 compounds), 325 nouns (114 1st decl.,
  103 2nd, 108 3rd), 188 adjectives.
- Alphabetical; each entry is lemma + short gloss + declension endings or
  preposition cases; compounds are listed under their prefix group
  (ἀπο-, δια-, ἐκ-, ἐπι-, κατα-, παρα-, προσ-, συν-, ὑπο-).
- Uses Koine/Ionic spellings in places (θάλασσα, πράσσω, γλῶσσα,
  ἁρμόζω noted as Attic ἁρμόττω); our lexicon uses the Attic -ττ- forms.

## How the course uses it

- **Second vocabulary ring.** The DCC 524 (already in the app) is ring 1.
  Major's ~1,100 minus DCC ≈ 600 words is ring 2, assigned to Stage 2 and
  the tracks. Build step: `scripts/build_vocab.py --ring2` parses this
  list, normalizes to Attic spelling, drops entries already in DCC, and
  emits `vocab_data/ring2.json` with `source: "major-80"`.
- **Compound families.** Major's grouping of compounds by prefix is the
  model for a "word-building" exercise type in Units 9–12: given ἄγω and
  the prefix chart, produce/parse ἀπάγω, εἰσάγω, ἐξάγω, προσάγω, συνάγω.
- **Track lists.** Domain words for the tracks (e.g. ψήφισμα, δικαστήριον,
  στρατόπεδον, τριήρης, ἱερεύς, θυσία) come first from this list before
  anything rarer.
- Licence: the PDF carries no explicit licence; treat the word selection
  as data and write our own glosses (the DCC glosses are CC BY-SA).
