#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 \"commit message\""
  exit 1
fi

MSG="$*"

# 顯示狀態
echo "Git status:"
git status --porcelain

# 加入所有變更
git add -A

# commit（若無變更則顯示訊息並退出）
if git commit -m "$MSG"; then
  CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
  echo "Pushing to origin/$CURRENT_BRANCH..."
  git push origin "$CURRENT_BRANCH"
  echo "Push complete."
else
  echo "No changes to commit."
fi
