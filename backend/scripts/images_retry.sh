#!/usr/bin/env bash
# Retry the image pass on your machine and push the results.
#
#   bash backend/scripts/images_retry.sh            # all images
#   bash backend/scripts/images_retry.sh kerameus   # only these ids
#
# Pulls the latest sources, resolves only what is still missing (shorter
# queries and other museums as fallbacks), downloads, crops, fills the
# manifests, writes backend/app/course_data/images/failures.json, doctor.json
# (can this machine reach each source?) and last-run.log, then commits the
# pictures + manifests + those reports and pushes, so the failures can be
# fixed from the branch.
set -uo pipefail

BRANCH=claude/ancient-greek-course-plan-n7f3lj
cd "$(git rev-parse --show-toplevel)"

git checkout "$BRANCH" && git pull --ff-only origin "$BRANCH" || { echo "git pull failed: commit or stash local changes first"; exit 1; }

cd backend
[ -d .venv ] && source .venv/bin/activate
python -c "import PIL" 2>/dev/null || pip install -q pillow

LOG=app/course_data/images/last-run.log
echo "== doctor" | tee "$LOG"
python scripts/build_images.py doctor 2>&1 | tee -a "$LOG"

ONLY=()
[ $# -gt 0 ] && ONLY=(--only "$@")
python -u scripts/build_images.py all "${ONLY[@]}" 2>&1 | tee -a "$LOG"
python scripts/build_images.py report 2>&1 | tail -n 5 | tee -a "$LOG"
cd ..

git add frontend/public/course/pics backend/app/course_data/images
if git diff --cached --quiet; then
  echo "Nothing new to commit."
else
  git commit -qm "Images: local image pass (pictures, manifests, failures.json)"
  git push -q origin "$BRANCH" && echo "Pushed (pictures, failures.json, doctor.json, last-run.log)."
fi
