#!/usr/bin/env bash
# 列出專案中可能的 app 目錄與 git-tracked 的 app 檔案
set -euo pipefail

ROOT="$(pwd)"
CANDIDATES=("$ROOT/app" "$ROOT/adminfrontend/app" "$ROOT/adminfrontend/build" "$ROOT/adminfrontend/dist" "$ROOT/adminfrontend")

echo "Checking candidate app folders..."
for d in "${CANDIDATES[@]}"; do
  if [ -d "$d" ]; then
    echo "---- Folder: $d ----"
    find "$d" -maxdepth 2 -type f -printf "%P\t%k KB\n" | sort -r -k2 | sed -n '1,200p'
    echo
  else
    echo "No: $d"
  fi
done

echo "---- Git-tracked files under app/ or adminfrontend/ (HEAD, top 200 by path) ----"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git ls-tree -r -l --full-tree HEAD | awk '{print $4, $5, $6, $7}' | sed -n '1,200p' | grep -E '(^app/|adminfrontend/|/app/|/build/|/dist/)' || echo "(no tracked app-related files)"
else
  echo "Not a git repo; skipping git-tracked listing."
fi
