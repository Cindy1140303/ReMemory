#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <path-to-remove> [more-paths...]"
  echo "Example: $0 uploads node_modules .env"
  exit 1
fi

# 取得遠端 origin URL
ORIGIN_URL=$(git config --get remote.origin.url || true)
if [ -z "$ORIGIN_URL" ]; then
  echo "Error: no remote.origin.url found. Run this from a repo with origin set or provide origin manually."
  exit 1
fi

# 產生唯一暫存資料夾
TIMESTAMP=$(date +%s)
TMP_DIR="$(pwd)/repo-filter-${TIMESTAMP}.git"

echo "Will mirror-clone ${ORIGIN_URL} to ${TMP_DIR}"
read -p "Proceed? This will rewrite remote history and force-push. (yes/no) " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
  echo "Aborted."
  exit 0
fi

echo "Cloning mirror..."
git clone --mirror "${ORIGIN_URL}" "${TMP_DIR}"

cd "${TMP_DIR}"

# 檢查 git-filter-repo
if ! command -v git-filter-repo >/dev/null 2>&1; then
  echo "git-filter-repo not found. Please install it first (pip install git-filter-repo) and re-run."
  exit 1
fi

# 建立 --path 參數
FILTER_ARGS=()
for p in "$@"; do
  FILTER_ARGS+=(--path "$p")
done

echo "Running git-filter-repo to remove paths: $*"
# invert-paths 表示刪除列出之路徑
git filter-repo --force --invert-paths "${FILTER_ARGS[@]}"

echo "Expiring reflog and running aggressive gc..."
git reflog expire --expire=now --all || true
git gc --prune=now --aggressive || true

echo "Force-pushing cleaned repo back to origin (all branches and tags)..."
git push --force --all
git push --force --tags

echo "Done. IMPORTANT: This rewrites repository history. All collaborators MUST re-clone the repo."
echo "Local mirror is at ${TMP_DIR} (you can keep as backup or delete it)."
