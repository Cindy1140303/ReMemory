# 🚀 Re Memory - Vercel 部署指南

## 📁 這個資料夾可以直接部署到 Vercel

### 🎯 方法 1: 拖拉部署（最簡單）

1. **前往 Vercel 網站**
   - 開啟 https://vercel.com
   - 用 email 註冊: `rememory.fju.2025@gmail.com`

2. **直接拖拉部署**
   - 登入後，點擊 "Add New..."
   - 選擇 "Project"
   - 將整個 `vercel-deploy` 資料夾拖到瀏覽器中

3. **設定環境變數**
   在 Vercel 專案設定中添加：
   ```
   MONGODB_URI = mongodb+srv://rememoryfju2025_db_user:AgAOvGRB5wlzHCje@cluster0.yvl3ug4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
   DB_TYPE = mongodb
   GEMINI_API_KEY = AIzaSyDD4JJV91yOm7NFm6AM3r3ZA-RYJiBp_7M
   ```

### 🎯 方法 2: Git 部署

1. **上傳到 GitHub**
   - 在 GitHub 建立新 repository
   - 上傳這個資料夾的內容

2. **連接 Vercel**
   - 在 Vercel 選擇 "Import Git Repository"
   - 選擇你的 GitHub repository

### 🎯 方法 3: CLI 部署（進階方式）

如果你有安裝 Node.js，這個方法可以快速更新專案而不用重新上傳檔案。

1. **安裝 Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **登入你的帳號**
   ```bash
   vercel login
   ```
   系統會開啟瀏覽器讓你登入 Vercel 帳號

3. **部署專案**
   ```bash
   cd vercel-deploy
   vercel
   ```
   
   CLI 會自動偵測框架並詢問：
   - 專案名稱
   - 部署路徑
   - 是否為正式環境 (production)
   
   輸入完後就會自動上傳並給你網址！

4. **後續更新**
   ```bash
   vercel --prod
   ```
   直接部署到正式環境，無需重新設定

## ⚙️ 部署後設定

1. **環境變數設定**
   - 進入 Vercel Dashboard
   - 選擇你的專案
   - Settings → Environment Variables
   - 添加上述環境變數

2. **測試 API**
   - Health Check: `https://your-project.vercel.app/api/health`
   - Memories API: `https://your-project.vercel.app/api/memories`

## 📱 手機版設定

部署成功後，將前端的 API 端點更新為你的 Vercel URL：
```javascript
const API_ENDPOINTS = {
  vercel: "https://your-project.vercel.app",
  current: "vercel"
};
```

## 🎉 完成！

你的 Re Memory 應用程式就可以在雲端運行了！

### 📞 支援

如果遇到問題：
1. 檢查 Vercel 的部署日誌
2. 確認環境變數設定正確
3. 測試 MongoDB 連線