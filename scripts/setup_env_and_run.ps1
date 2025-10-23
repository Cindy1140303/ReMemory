param(
    [string]$DbUser = "admin",
    [string]$ClusterHost = "cluster0.cykiyri.mongodb.net",
    [string]$DbName = "lifemap",
    [int]$Port = 8020
)

# 交互式輸入密碼（不在螢幕上回顯）
Write-Host "This script will create .env and run the FastAPI server (uvicorn)."
$pwd = Read-Host -AsSecureString "Enter MongoDB password for user '$DbUser'"
$unsecure = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($pwd))

# 組成 MONGODB_URI（請自行確認需要的 query 參數）
$mongo_uri = "mongodb+srv://$($DbUser):$($unsecure)@$($ClusterHost)/?retryWrites=true&w=majority"

# 寫入 .env（覆寫）
$envContent = @"
MONGODB_URI="$mongo_uri"
MONGODB_DB_NAME=$DbName
# If you have TLS issues for local development only, you can enable the next line:
# MONGODB_TLS_INSECURE=true
"@

$envPath = Join-Path -Path (Get-Location) -ChildPath ".env"
$envContent | Out-File -Encoding UTF8 -FilePath $envPath -Force
Write-Host ".env created at $envPath (contains your DB URI)."

# 啟用虛擬環境（假設 .venv 已存在）
$venvActivate = Join-Path -Path (Get-Location) -ChildPath ".venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    Write-Host "Activating virtual environment .venv..."
    & $venvActivate
} else {
    Write-Host ".venv not found. Creating .venv and installing minimal dependencies..."
    python -m venv .venv
    & $venvActivate
    pip install --upgrade pip
    pip install fastapi uvicorn python-dotenv pymongo certifi
}

Write-Host "Starting uvicorn server: host=0.0.0.0 port=$Port"
# 啟動 uvicorn（在此終端可見日誌；以 Ctrl+C 停止）
uvicorn server:app --host 0.0.0.0 --port $Port --reload
