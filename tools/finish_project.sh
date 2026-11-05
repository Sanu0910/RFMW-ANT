#!/usr/bin/env bash
# Commit and push a finished (or updated) project to GitHub, after the checks in LOCAL_SETUP.md.
#
#   bash tools/finish_project.sh projects/15_cband-6x6-dualpol-stacked-patch_match-debug "short summary of the change"
#
# - refuses to run if STATUS.md / CHANGELOG.md of that project were not touched since the last commit
# - warns about files over 50 MB (GitHub rejects > 100 MB) and about simulation dumps not ignored
# - commits only that project folder plus the root README.md / STATUS.md, then pushes the current branch
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
P="${1:?usage: finish_project.sh projects/NN_name \"message\"}"; P="${P%/}"
MSG="${2:?give a short commit message}"
[ -d "$P" ] || { echo "no such folder: $P"; exit 1; }
NAME="$(basename "$P")"; NUM="${NAME%%_*}"

for f in STATUS.md CHANGELOG.md; do
  [ -f "$P/$f" ] || echo "WARNING: $P/$f is missing (see docs/CONVENTIONS.md)"
done
[ -f "$P/00_README.md" ] || [ -f "$P/README.md" ] || echo "WARNING: $P has no 00_README.md"

if [ -z "$(git status --porcelain -- "$P/STATUS.md" "$P/CHANGELOG.md")" ] && [ -n "$(git log -1 --format=%H -- "$P" 2>/dev/null)" ]; then
  echo "STATUS.md and CHANGELOG.md of $P are unchanged. Update them first (docs/CONVENTIONS.md)."; exit 1
fi
grep -q "$NAME" README.md || echo "WARNING: $NAME is not in the project table of the root README.md"
grep -q "^| $NUM " STATUS.md || echo "WARNING: project $NUM is not in the table of the root STATUS.md"

BIG=$(find "$P" -type f -size +50M -not -path '*/.git/*' | while read -r f; do git check-ignore -q "$f" || echo "$f"; done)
if [ -n "$BIG" ]; then echo "Files over 50 MB would be committed (zip them or add them to .gitignore):"; echo "$BIG"; exit 1; fi

git add -- "$P" README.md STATUS.md
git status --short -- "$P" README.md STATUS.md
git commit -m "proj${NUM}: ${MSG}"
BR="$(git rev-parse --abbrev-ref HEAD)"
for i in 1 2 3 4; do git push -u origin "$BR" && break || { echo "push failed, retry in $((2**i)) s"; sleep $((2**i)); }; done
echo "Pushed $P on branch $BR: $(git rev-parse --short HEAD)"
