# Course image audit — 2026-09-28

Production initially returned 633 image records: 52 built-in SVG diagrams and
581 photo placeholders. No files existed under frontend/public/course/pics,
including on the old image-work branch. This was an incomplete image pipeline,
not a redirect or CSS regression.

The saved data contained 541 source-search rows and 173 licence-verified records
representing 101 distinct image URLs. All 173 candidates were recovered locally.
40 photo records have no source row, so the old script could never search them.

## Correctness issue

Licence verification did not verify the subject. The search relaxed away the
subject words and accepted generic object-type matches. Examples: kyon (dog)
resolved to a boar-shaped askos; polites (citizen) to a bronze horse; pappos
(grandfather) to a statuette of an emaciated woman. Many specific story scenes
resolved to unrelated generic pottery. Those candidates must not teach the wrong
word or stand in for the requested narrative scene.

Thirteen clear matches were visually reviewed and approved in reviewed.json.
Approval is bound to source and object ID; a different search result invalidates
approval. Other downloaded candidates remain placeholders until subject review.
The complete current inventory and per-image reasons are in
backend/app/course_data/images/inventory.json and failures.json.

## Pipeline changes

- `recover`: deduplicate saved image URLs, download with bounded concurrency,
  process candidates, and publish only source-matched reviewed pictures.
- `inventory`: distinguish ready photos, diagrams, downloaded candidates needing
  review, verified sources not downloaded, unverified sources, and missing rows.
- `all`: finish and checkpoint each image before attempting the next search.
  Previously every search had to finish before any downloads started.
- Retry script stays on the current branch, handles empty arguments on older
  Bash, preserves the command exit status, and prints the complete report.
  It no longer automatically switches to the old Claude branch or silently pushes.
- `IMAGE_PUSH=1` explicitly enables commit/push; `IMAGE_MODE=all` runs searches.
  The default resumes verified downloads. Partial recovery exits nonzero.
- Repair workflow saves actual binaries and matching manifests together.

## Remaining work

Review the recovered candidates against their intended subjects, replace wrong
matches with specific verified sources, and add the 40 missing source rows.
Dictionary nouns can often use object photographs. Action verbs, comparisons and
fictional story panels need precise illustrations; broad museum keyword matches
are unsuitable. Recommend authored diagrams or purpose-made illustrations for
those scenes rather than lowering the matching standard just to increase counts.

## Targeted introductory recovery

Four additional artifacts were located, licence-checked, downloaded and visually
reviewed: the Dipylon inscription, Themistokles ostraka, the Greek schoolboy's
wax writing tablet (BL Add MS 34186), and the Douris school cup. Wax tablet and
school cup rows now pin specific Commons files instead of broad searches.
A fresh doctor run succeeded for museum APIs, Commons search/metadata, and image
downloads; the old numeric-metadata error did not reproduce.

Final recovery inventory: **17 approved photos, 160 downloaded candidates awaiting
review/replacement, 364 rows needing a verified source, 40 records without a
source row**, plus 52 built-in diagrams. The image collection is still incomplete.

## Original illustration pass — 2026-09-28

The owner approved high-quality original illustrations, superseding the older
no-generated-imagery direction. The opening manifest now has **zero placeholders**
across its 74 image records, including all eight Unit 1 story panels.

- 51 reviewed original illustrations fill 57 formerly empty image slots.
- Five additional museum/site photographs fill exact cultural subjects: Dipylon
  gate, Munich 1717 potter scene, Met 247244 fountain-house hydria, Met 253348
  Amasis weaving lekythos, and Met 251043 funerary lekythos.
- The funerary vessel caption now describes its actual figures and date.
- Original illustration prompts, generator, review notes and SHA-256 hashes are
  recorded in `backend/app/course_data/images/illustrations.json`.
- Raster originals live in `frontend/public/course/illustrations`, separate from
  museum candidates. The installer writes encoded WebP files atomically.
- Museum retries preserve originals. Course validation requires matching original
  provenance; credits identify interpretive AI illustrations explicitly.
- 30 image-pipeline tests pass, including decoding, hashes and overwrite protection.
- The previously rejected kiln scene was replaced with brick-and-clay closures.

The full collection remains incomplete: **79 ready raster image records, 52
built-in diagrams, 502 placeholders**. The complete current inventory is in
`backend/app/course_data/images/inventory.json`. Future passes must retain the
same subject-review standard; downloaded candidates are not automatically approved.

The daytime image is distinct from the sun image, including when both appear in
the same picture-choice quiz. A regression check rejects duplicate published
pictures within a question. The final daytime illustration uses simpler gouache
shapes and reduced detail, as requested for faster future generation.
