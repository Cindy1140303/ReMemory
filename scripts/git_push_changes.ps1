param(
    [Parameter(Mandatory=$true)]
    [string]$Message
)

# 顯示狀態
git status --porcelain

# 加入所有變更
git add -A

# 嘗試 commit
try {
    git commit -m $Message | Out-Null
} catch {
    Write-Host "No changes to commit." -ForegroundColor Yellow
    exit 0
}

# 取得目前分支並推送
$branch = git rev-parse --abbrev-ref HEAD
Write-Host "Pushing to origin/$branch ..."
git push origin $branch
Write-Host "Push complete."
