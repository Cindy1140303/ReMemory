#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <path-to-remove> [more-paths...]"
  echo "Example: $0 uploads node_modules .env"
  exit 1
fi

# 確認在 git repo
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: not inside a git repository. Run this from repo root."
  exit 1
fi

ORIGIN_URL=$(git config --get remote.origin.url || true)
if [ -z "$ORIGIN_URL" ]; then
  echo "Warning: no remote.origin.url found. Script will still remove from HEAD but won't push."
fi

echo "The following paths will be removed from HEAD tracking and added to .gitignore:"
for p in "$@"; do
  echo "  - $p"
done

read -p "Proceed? This will run 'git rm --cached -r' for each path and commit. Type 'yes' to continue: " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
  echo "Aborted."
  exit 0
fi

# Perform removal and update .gitignore
for p in "$@"; do
  if [ -e "$p" ] || git ls-files --error-unmatch "$p" >/dev/null 2>&1; then
    echo "Removing from index: $p"
    git rm --cached -r "$p" || true
  else
    echo "Note: path not present in working tree or not tracked: $p"
  fi

  # Append to .gitignore if not present
  if ! grep -qxF "$p" .gitignore 2>/dev/null; then
    echo "$p" >> .gitignore
    echo "Added $p to .gitignore"
  else
    echo "$p already in .gitignore"
  fi
done

git add .gitignore || true
git commit -m "chore: remove specified large/sensitive paths from HEAD and add to .gitignore" || {
  echo "No changes to commit (maybe only removals)."
}

if [ -n "$ORIGIN_URL" ]; then
  echo "Pushing to origin..."
  git push
else
  echo "No origin configured; skipping push."
fi

echo "Done. Note: history unchanged. If large files exist in repo history, consider git-filter-repo or BFG."
