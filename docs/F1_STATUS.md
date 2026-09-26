# F1 implementation status

Pull request: https://github.com/rems3n/attic-reader/pull/2

Implemented: desktop sidebar, mobile navigation, Home and guest dashboard,
onboarding and starting check, Help, guest Settings, Practice, quick vocabulary
sessions, weekly word goals, shared session summaries, route redirects, and
offline route migration.

Verified: 654 backend tests passed (5 skipped), 130 frontend tests passed,
TypeScript and production build passed, course validator reported 0 problems.

Browser results from run 36269228052, verified from logs:
- Passed: course, placement, stage1, stage2, tracks, skills, navigation, offline.
- Navigation: 0 problems, including phone/desktop axe checks.
- Failed: shell walk waiting for Home's Resume lesson link after opening Lesson 0.1.
  Home itself shows the returning-learner heading. The follow-up test allows the
  same 30-second loading window as other API-backed flows and captures the
  rendered Home text and screenshot if the link still fails.
- The workflow's piped logging previously hid failing test exit codes.
  Explicit bash with pipefail now makes each failure fail its step and job.

Keep this PR in draft until the shell walk passes and all new-page screenshots
have been inspected. Do not begin F2 or deploy this phase before that gate.

The development workspace disconnected during verification. Source and tests are
saved in the PR. The next run can complete on GitHub without the local workspace;
download its shell-screenshots artifact after reconnecting for visual review.

Recommendations applied: give returning guests a dashboard; keep sidebar labels
on smaller desktops; use the short check only for a conservative starting
recommendation, retaining full placement for skipping units. GitHub's default
branch is still an older branch; change it to main when managing repository
settings.
