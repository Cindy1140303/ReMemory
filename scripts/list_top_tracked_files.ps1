# 於 repo 根目錄執行： .\scripts\list_top_tracked_files.ps1
$lines = git ls-tree -r -l --full-tree HEAD 2>$null
if (-not $lines) { Write-Host "No tracked files or git not available."; exit 1 }

$items = foreach ($line in $lines) {
    # line format: "<mode> <type> <hash> <size>\t<path>"
    $parts = $line -split "`t", 2
    if ($parts.Count -lt 2) { continue }
    $left = $parts[0].Trim()
    $path = $parts[1].Trim()
    $tokens = -split $left
    $sizeStr = $tokens[-1]
    [PSCustomObject]@{
        Path = $path
        Size = [int64]::Parse($sizeStr)
        SizeMB = [math]::Round([int64]::Parse($sizeStr) / 1MB, 2)
    }
}

$items | Sort-Object -Property Size -Descending | Select-Object -First 30 | 
    ForEach-Object { "{0,8} MB`t{1}" -f $_.SizeMB, $_.Path }
