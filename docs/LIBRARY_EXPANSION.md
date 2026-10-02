# Reading library expansion

322 Greek passages, 26 works, seven authors, approximately 85,800 whitespace-delimited words. Original featured excerpts are retained; 310 new readings are consecutive opening selections, not complete works. Source: PerseusDL/canonical-greekLit, revision bcc5df0602f3b3fe6fefe1e1d575602a25ab1db6, CC BY-SA 4.0. Individual records link to the pinned edition and the starting section in Scaife Reader.

The catalog provides work and passage views, accent-insensitive metadata search, author/subject/difficulty/dialect/length filters, five sort options, URL-preserved filters, and pagination. Recommendations prioritize editorial difficulty, vocabulary-list coverage, then length, with diverse works. They do not infer personal knowledge from dictionary matches. The reader opens text immediately, with explicit audio generation and previous/next navigation for imported sequences. Existing translation, definitions, vocabulary support, and audio controls remain available.

The importer groups whole TEI sections near 180 words (some sections are longer), up to twelve readings per work. Run `python backend/scripts/expand_library.py /path/to/canonical-greekLit` to rebuild from a local source checkout. Original featured excerpts can overlap these opening sequences. Editorial notation remains in displayed source text; unsupported silent marks are normalized only at the speech adapter. Imported prose includes Attic, Ionic, and later Koine; audio remains Classical Attic.

The additional catalog is excluded from startup audio pre-rendering and bulk cache inspection. Vocabulary examples retain original references and bound new references per word and passage. Run `python backend/scripts/build_vocab.py` after changing catalog contents.

Validation includes catalog/source integrity and voice-symbol tests; search/sort/grouping unit tests; production build; desktop/phone browser navigation, filters, pagination, source attribution, text-first opening, and requested audio. The dedicated browser suite is `backend/scripts/e2e/e2e_library.py` and runs in the existing verification workflow.
