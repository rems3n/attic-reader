#!/usr/bin/env bash
# Resume verified downloads by default. IMAGE_MODE=all also searches missing rows.
# IMAGE_PUSH=1 explicitly commits and pushes image outputs on the CURRENT branch.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)" || exit 1
BRANCH=$(git branch --show-current)
[ -n "$BRANCH" ] || { echo "Use a named branch before running the image pass."; exit 1; }
if [ "${IMAGE_PUSH:-0}" = 1 ] && ! git diff --cached --quiet; then
  echo "Commit or unstage existing staged changes before using IMAGE_PUSH=1."; exit 1
fi
cd backend || exit 1
if [ -x .venv/bin/python ]; then
  PY=.venv/bin/python
else
  if [ ! -x .image-venv/bin/python ]; then
    BASE=$(command -v python3 || command -v python) || exit 1
    "$BASE" -m venv .image-venv || exit 1
  fi
  PY=.image-venv/bin/python
fi
"$PY" -c "import PIL" 2>/dev/null || "$PY" -m pip install -q pillow || exit 1
LOG=app/course_data/images/last-run.log
MODE=${IMAGE_MODE:-recover}
echo "Image mode: $MODE; branch: $BRANCH" | tee "$LOG"
# Avoid empty-array expansion differences in macOS's bundled Bash 3.2.
if [ $# -gt 0 ]; then
  "$PY" -u scripts/build_images.py "$MODE" --only "$@" 2>&1 | tee -a "$LOG"
else
  "$PY" -u scripts/build_images.py "$MODE" 2>&1 | tee -a "$LOG"
fi
RESULT=${PIPESTATUS[0]}
"$PY" scripts/build_images.py report 2>&1 | tee -a "$LOG"
cd .. || exit 1
if [ "${IMAGE_PUSH:-0}" = 1 ]; then
  git add frontend/public/course/pics backend/app/course_data/images
  if ! git diff --cached --quiet; then
    git commit -m "Recover course images and record remaining gaps" && git push origin "$BRANCH" || exit 1
  fi
else
  echo "Outputs remain on $BRANCH for review; no branch switch, commit or push was performed."
fi
[ "$RESULT" -eq 0 ] || echo "Partial recovery: see inventory.json and failures.json for remaining images."
exit "$RESULT"
