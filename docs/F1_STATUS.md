# F1 release verification

PR: https://github.com/rems3n/attic-reader/pull/2
Verified application commit: `ba48400c34a9f5b9add9f066413ad086a5739f3f`
Run: https://github.com/rems3n/attic-reader/actions/runs/36269975095

Implemented: desktop sidebar, mobile navigation, Home and guest dashboard,
onboarding and starting check, Help, guest Settings, Practice, quick vocabulary
sessions, weekly word goals, shared session summaries, route redirects, and
offline route migration.

## Verification

- Backend: 654 passed, 5 skipped.
- Frontend: 130 passed; TypeScript and production build passed.
- Course validation: 0 problems.
- All nine browser suites passed: shell, course, placement, stage1, stage2,
  tracks, skills, navigation, offline.
- Navigation: 0 problems, including mobile/desktop accessibility audits.
- Home resumes an in-progress lesson after loading course data.
- Workflow uses bash pipefail so piped logging cannot hide test failures.
- All 24 screenshots visually reviewed at phone 390×844 and desktop
  1280×900; lossless WebP copies saved in `screenshots/f1/`. Full-page
  captures include the fixed mobile bar at the initial viewport position.

## Recommendations applied

Returning guests receive a progress dashboard. Smaller desktops retain sidebar
labels. The short starting check makes a conservative recommendation and leaves
unit skipping to full placement. Known words require a 21-day review interval
and are deduplicated across card directions.

Accounts remain F2, the Library redesign F3, unified practice F4, and deeper
Progress redesign F5. No course content or voice changes are included.

Repository housekeeping: GitHub's default branch still points to an older
branch. Main is the production source; changing the GitHub default requires a
repository administration capability not exposed by the current connector.
