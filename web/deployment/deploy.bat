@echo off
echo 🚀 開始部署 Life Map 到 Vercel + MongoDB Atlas

REM 檢查 Vercel CLI
where vercel >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Vercel CLI 未安裝，正在安裝...
    npm install -g vercel
)

REM 檢查是否已登入 Vercel
echo 🔐 檢查 Vercel 登入狀態...
vercel whoami
if %errorlevel% neq 0 (
    echo 📝 請登入 Vercel:
    vercel login
)

REM 確認環境變數設定
echo ⚙️ 請確認你已在 Vercel Dashboard 設定以下環境變數:
echo   - DATABASE_TYPE=mongodb
echo   - MONGODB_URI=mongodb+srv://...
echo   - MONGODB_DB_NAME=lifemap
echo   - GEMINI_API_KEY=... (可選)
echo.
set /p confirm="已設定環境變數了嗎？(y/N): "
if /i not "%confirm%"=="y" (
    echo ❌ 請先設定環境變數再執行部署
    echo 📖 參考: .env.vercel 檔案
    pause
    exit /b 1
)

REM 檢查 requirements-vercel.txt
if not exist "requirements-vercel.txt" (
    echo ❌ 找不到 requirements-vercel.txt
    pause
    exit /b 1
)

REM 部署到 Vercel
echo 🚀 開始部署...
vercel --prod

if %errorlevel% equ 0 (
    echo ✅ 部署成功！
    echo 🌍 你的 Life Map 應用已上線
    echo 📝 記得更新前端的 API_ENDPOINTS.current 設定
    echo 💡 部署 URL 會顯示在上方，請複製並更新到前端設定中
) else (
    echo ❌ 部署失敗，請檢查錯誤訊息
)

pause