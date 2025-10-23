param (
    [Parameter(Mandatory=$true, ValueFromRemainingArguments=$true)]
    [string[]]$Paths
)

if ($Paths.Count -lt 1) {
    Write-Host "Usage: .\git_filter_repo_remove.ps1 <path-to-remove> [more-paths...]"
    exit 1
}

$origin = git config --get remote.origin.url 2>$null
if (-not $origin) {
    Write-Host "Error: no remote.origin.url found. Run from a repo with origin set."
    exit 1
}

$timestamp = [int][double]::Parse((Get-Date -UFormat %s))
$tmpDir = Join-Path (Get-Location) ("repo-filter-{0}.git" -f $timestamp)

Write-Host "Will mirror-clone $origin to $tmpDir"
$confirm = Read-Host "Proceed? This will rewrite remote history and force-push. Type 'yes' to continue"
if ($confirm -ne "yes") {
    Write-Host "Aborted."
    exit 0
}

git clone --mirror $origin $tmpDir
Set-Location $tmpDir

# 檢查 git-filter-repo
if (-not (Get-Command git-filter-repo -ErrorAction SilentlyContinue)) {
    Write-Host "git-filter-repo not found. Install via 'pip install git-filter-repo' and re-run."
    exit 1
}

# 建立參數
$filterArgs = @()
foreach ($p in $Paths) {
    $filterArgs += "--path"
    $filterArgs += $p
}

Write-Host "Running git-filter-repo to remove paths: $($Paths -join ', ')"
git filter-repo --force --invert-paths $filterArgs

Write-Host "Expiring reflog and running aggressive gc..."
git reflog expire --expire=now --all
git gc --prune=now --aggressive

Write-Host "Force-pushing cleaned repo back to origin (all branches and tags)..."
git push --force --all
git push --force --tags

Write-Host "Done. IMPORTANT: history rewritten. All collaborators MUST re-clone the repo."
Write-Host "Local mirror backup at $tmpDir"
