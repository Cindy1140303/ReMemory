param (
    [Parameter(Mandatory=$true, ValueFromRemainingArguments=$true)]
    [string[]]$Paths
)

# 確認 git repo
if (-not (git rev-parse --is-inside-work-tree 2>$null)) {
    Write-Host "Error: not inside a git repository. Run from repo root." -ForegroundColor Red
    exit 1
}

$origin = git config --get remote.origin.url 2>$null
if (-not $origin) {
    Write-Host "Warning: no remote.origin.url found. Script will still remove from HEAD but won't push."
}

Write-Host "The following paths will be removed from HEAD tracking and added to .gitignore:"
$Paths | ForEach-Object { Write-Host "  - $_" }

$confirm = Read-Host "Proceed? This will run 'git rm --cached -r' for each path and commit. Type 'yes' to continue"
if ($confirm -ne "yes") {
    Write-Host "Aborted."
    exit 0
}

foreach ($p in $Paths) {
    if (Test-Path $p -PathType Any -ErrorAction SilentlyContinue -ErrorVariable ev) {
        Write-Host "Removing from index: $p"
        git rm --cached -r $p 2>$null
    } else {
        # still attempt to untrack if git knows it
        try {
            git ls-files --error-unmatch $p 2>$null | Out-Null
            Write-Host "Removing tracked path (not in working tree): $p"
            git rm --cached -r $p 2>$null
        } catch {
            Write-Host "Note: path not present in working tree or not tracked: $p"
        }
    }

    # Append to .gitignore if not present
    $giContent = Get-Content -Raw -ErrorAction SilentlyContinue -Path .gitignore
    if ($giContent -notmatch [regex]::Escape($p)) {
        Add-Content -Path .gitignore -Value $p
        Write-Host "Added $p to .gitignore"
    } else {
        Write-Host "$p already in .gitignore"
    }
}

git add .gitignore 2>$null
try {
    git commit -m "chore: remove specified large/sensitive paths from HEAD and add to .gitignore" 2>$null
} catch {
    Write-Host "No changes to commit (maybe only removals)."
}

if ($origin) {
    Write-Host "Pushing to origin..."
    git push
} else {
    Write-Host "No origin configured; skipping push."
}

Write-Host "Done. Note: history unchanged. If large files exist in repo history, consider git-filter-repo or BFG."
