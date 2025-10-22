#!/bin/bash

echo "🚀 開始部署 Life Map 到 Vercel + MongoDB Atlas"

# 檢查 Vercel CLI
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI 未安裝，正在安裝..."
    npm install -g vercel
fi

# 檢查是否已登入 Vercel
echo "🔐 檢查 Vercel 登入狀態..."
vercel whoami || {
    echo "📝 請登入 Vercel:"
    vercel login
}

# 確認環境變數設定
echo "⚙️ 請確認你已在 Vercel Dashboard 設定以下環境變數:"
echo "  - DATABASE_TYPE=mongodb"
echo "  - MONGODB_URI=mongodb+srv://..."
echo "  - MONGODB_DB_NAME=lifemap"
echo "  - GEMINI_API_KEY=... (可選)"
echo ""
read -p "已設定環境變數了嗎？(y/N): " confirm
if [[ $confirm != [yY] ]]; then
    echo "❌ 請先設定環境變數再執行部署"
    echo "📖 參考: .env.vercel 檔案"
    exit 1
fi

# 檢查 requirements-vercel.txt
if [ ! -f "requirements-vercel.txt" ]; then
    echo "❌ 找不到 requirements-vercel.txt"
    exit 1
fi

# 部署到 Vercel
echo "🚀 開始部署..."
vercel --prod

if [ $? -eq 0 ]; then
    echo "✅ 部署成功！"
    echo "🌍 你的 Life Map 應用已上線"
    echo "📝 記得更新前端的 API_ENDPOINTS.current 設定"
    echo "💡 部署 URL 會顯示在上方，請複製並更新到前端設定中"
else
    echo "❌ 部署失敗，請檢查錯誤訊息"
    exit 1
fi