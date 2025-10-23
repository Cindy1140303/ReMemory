param()
# 列出可能的 app 目錄內容與 git-tracked 的 app 檔案（Windows PowerShell）
$root = Get-Location
$candidates = @(
    Join-Path $root "app",
    Join-Path $root "adminfrontend\app",
    Join-Path $root "adminfrontend\build",
    Join-Path $root "adminfrontend\dist",
    Join-Path $root "adminfrontend"
)

Write-Host "Checking candidate app folders..."
foreach ($d in $candidates) {
    if (Test-Path $d -PathType Container) {
        Write-Host "---- Folder: $d ----"
        Get-ChildItem -Path $d -Recurse -File -Depth 2 |
            Select-Object @{Name='SizeMB';Expression={[math]::Round($_.Length/1MB,2)}}, FullName |
            Sort-Object -Property SizeMB -Descending |
            Select-Object -First 200 |
            ForEach-Object { "{0,6} MB`t{1}" -f $_.SizeMB, $_.FullName }
        Write-Host ""
    } else {
        Write-Host "No: $d"
    }
}

Write-Host "---- Git-tracked files under app/ or adminfrontend/ (HEAD) ----"
if (git rev-parse --is-inside-work-tree 2>$null) {
    git ls-tree -r -l --full-tree HEAD |
    Select-String -Pattern '(^|/)(app|build|dist|adminfrontend)(/|$)' |
    Select-Object -First 200 |
    ForEach-Object { $_.Line }
} else {
    Write-Host "Not a git repo; skipping git-tracked listing."
}
