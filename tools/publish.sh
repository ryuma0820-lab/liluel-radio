#!/bin/bash
# Publish static files from main and retain previously published audio on gh-pages.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
ROOT=$PWD
read -r DIR KEEP < <(python3 -c 'import json; a = json.load(open("station.json")).get("audio", {}); print(a.get("dir", "audio"), a.get("keep_days", 30))')
CUT=$(python3 -c "import datetime; print((datetime.date.today() - datetime.timedelta(days=$KEEP)).isoformat())")
REMOTE=$(git remote get-url origin)
NAME=$(git config user.name || echo 'github-actions[bot]')
EMAIL=$(git config user.email || echo '41898282+github-actions[bot]@users.noreply.github.com')
AUTH=$(git -C "$ROOT" config --local --get 'http.https://github.com/.extraheader' || true)
TMP=$(mktemp -d)
OLD=$(mktemp -d)
trap 'rm -rf "$TMP" "$OLD"' EXIT
git archive HEAD | tar -x -C "$TMP"
mkdir -p "$TMP/$DIR"
# Remote gh-pages contains the MP3 files excluded from the main branch by .gitignore.
# Copy them first, then overwrite with a newly generated local MP3 if present.
if git fetch -q origin gh-pages:refs/remotes/origin/gh-pages 2>/dev/null; then
  if git archive refs/remotes/origin/gh-pages "$DIR" 2>/dev/null | tar -x -C "$OLD" 2>/dev/null; then
    for f in "$OLD/$DIR"/*; do
      [ -f "$f" ] || continue
      d=$(basename "$f"); d=${d:0:10}
      if [[ ! "$d" < "$CUT" ]]; then cp "$f" "$TMP/$DIR/"; fi
    done
  fi
fi
for f in "$DIR"/*; do
  [ -f "$f" ] || continue
  d=$(basename "$f"); d=${d:0:10}
  if [[ ! "$d" < "$CUT" ]]; then cp "$f" "$TMP/$DIR/"; fi
done
# Purge expired audio if it was committed to main unexpectedly.
for f in "$TMP/$DIR"/*; do
  [ -f "$f" ] || continue
  d=$(basename "$f"); d=${d:0:10}
  if [[ "$d" < "$CUT" ]]; then rm -f "$f"; fi
done
PY=${SHARE_PYTHON:-python3}
if [[ -f tools/share.py ]] && "$PY" -c 'import PIL' 2>/dev/null; then
  "$PY" tools/share.py "$TMP" --all --front
else
  echo 'share cards: skipped (no Pillow)'
fi
touch "$TMP/.nojekyll"
cd "$TMP"
git init -q -b gh-pages
git add -A -f
git -c user.name="$NAME" -c user.email="$EMAIL" commit -q -m "publish $(date +%F)"
if [[ -n "$AUTH" && "$REMOTE" == https://github.com/* ]]; then
  git -c "http.https://github.com/.extraheader=$AUTH" push -q -f "$REMOTE" gh-pages
else
  git push -q -f "$REMOTE" gh-pages
fi
echo "published gh-pages: $(git ls-files | wc -l | tr -d ' ') files, $(find "$DIR" -maxdepth 1 -type f -name '*.mp3' | wc -l | tr -d ' ') audio"
