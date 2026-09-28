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
