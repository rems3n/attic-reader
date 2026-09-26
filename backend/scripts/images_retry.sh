#!/usr/bin/env bash
# Retry the image pass on your machine and push the results.
#
#   bash backend/scripts/images_retry.sh            # all images
#   bash backend/scripts/images_retry.sh kerameus   # only these ids
#
# Pulls the latest sources, resolves only what is still missing (shorter
# queries and other museums as fallbacks), downloads, crops, fills the
# manifests, writes backend/app/course_data/images/failures.json, then commits
# the pictures + manifests + failures.json and pushes, so the failures can be
# fixed from the branch.
set -uo pipefail

BRANCH=claude/ancient-greek-course-plan-n7f3lj
cd "$(git rev-parse --show-toplevel)"

git checkout "$BRANCH" && git pull --ff-only origin "$BRANCH" || { echo "git pull failed: commit or stash local changes first"; exit 1; }

cd backend
[ -d .venv ] && source .venv/bin/activate
python -c "import PIL" 2>/dev/null || pip install -q pillow

ONLY=()
[ $# -gt 0 ] && ONLY=(--only "$@")
python scripts/build_images.py all "${ONLY[@]}" 2>&1 | tee ../image-run.log
python scripts/build_images.py report | tail -n 5
cd ..

git add frontend/public/course/pics backend/app/course_data/images
if git diff --cached --quiet; then
  echo "Nothing new to commit."
else
  git commit -qm "Images: local image pass (pictures, manifests, failures.json)"
  git push -q origin "$BRANCH" && echo "Pushed. Failures are listed in backend/app/course_data/images/failures.json."
fi
