#!/bin/bash

# Re Memory - Vercel 部署腳本
echo "🚀 準備部署 Re Memory 到 Vercel..."

# 1. 檢查 Vercel CLI 是否已安裝
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI 未安裝，正在安裝..."
    npm install -g vercel
fi

# 2. 確保所有必要檔案存在
echo "📋 檢查部署檔案..."
required_files=(
    "vercel.json"
    "requirements-vercel.txt"
    "api/health.py"
    "api/memories.py"
    "api/audio.py"
    "www/index.html"
    "database/mongodb_models.py"
)

for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "❌ 缺少必要檔案: $file"
        exit 1
    fi
done

echo "✅ 所有檔案檢查完成"

# 3. 設定環境變數（這些會在 Vercel dashboard 中設定）
echo "⚙️ 環境變數配置："
echo "  - MONGODB_URI: mongodb+srv://rememoryfju2025_db_user:***"
echo "  - DB_TYPE: mongodb"
echo "  - GEMINI_API_KEY: ***"

# 4. 執行部署
echo "🚀 開始部署到 Vercel..."

# 設定專案名稱
PROJECT_NAME="re-memory-fju-2025"

# 登入 Vercel（如果尚未登入）
echo "🔐 Vercel 登入..."
vercel login --email rememory.fju.2025@gmail.com

# 部署
echo "📦 執行部署..."
vercel --prod --name $PROJECT_NAME --yes

echo "✅ 部署完成！"
echo "🌐 您的應用程式將可在以下網址存取："
echo "   https://$PROJECT_NAME.vercel.app"

echo ""
echo "📝 部署後檢查清單："
echo "  1. 測試 API 端點: https://$PROJECT_NAME.vercel.app/api/health"
echo "  2. 測試記憶功能: https://$PROJECT_NAME.vercel.app/api/memories"
echo "  3. 測試錄音功能: https://$PROJECT_NAME.vercel.app/api/audio"
echo "  4. 檢查 MongoDB 連線狀態"
echo ""
echo "🎉 Re Memory 已成功部署到雲端！"