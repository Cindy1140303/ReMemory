@echo off
echo 🚀 準備部署 Re Memory 到 Vercel...

REM 1. 檢查 Node.js 和 npm
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Node.js 未安裝，請先安裝 Node.js
    exit /b 1
)

REM 2. 安裝或檢查 Vercel CLI
where vercel >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo 📦 安裝 Vercel CLI...
    npm install -g vercel
)

REM 3. 檢查必要檔案
echo 📋 檢查部署檔案...
if not exist "vercel.json" (
    echo ❌ 缺少 vercel.json
    exit /b 1
)
if not exist "requirements-vercel.txt" (
    echo ❌ 缺少 requirements-vercel.txt
    exit /b 1
)
if not exist "www\index.html" (
    echo ❌ 缺少 www\index.html
    exit /b 1
)

echo ✅ 檔案檢查完成

REM 4. 顯示環境變數資訊
echo ⚙️ 環境變數配置：
echo   - MONGODB_URI: mongodb+srv://rememoryfju2025_db_user:***
echo   - DB_TYPE: mongodb
echo   - GEMINI_API_KEY: ***

REM 5. 執行部署
echo 🚀 開始部署到 Vercel...

REM 自動登入和部署
vercel --prod --name re-memory-fju-2025 --yes

if %ERRORLEVEL% EQU 0 (
    echo ✅ 部署完成！
    echo 🌐 您的應用程式網址: https://re-memory-fju-2025.vercel.app
    echo.
    echo 📝 部署後檢查清單：
    echo   1. 測試 API: https://re-memory-fju-2025.vercel.app/api/health
    echo   2. 測試記憶: https://re-memory-fju-2025.vercel.app/api/memories  
    echo   3. 測試錄音: https://re-memory-fju-2025.vercel.app/api/audio
    echo.
    echo 🎉 Re Memory 已成功部署到雲端！
) else (
    echo ❌ 部署失敗，請檢查錯誤訊息
    exit /b 1
)

pause