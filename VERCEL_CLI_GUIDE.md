# 🚀 Vercel CLI 部署完整指南

## 🎯 方法二：使用 Vercel CLI（進階方式）

如果你有安裝 Node.js，這個方法可以快速更新專案而不用重新上傳 zip。

### 📋 步驟一：安裝與設定

1. **檢查 Node.js**
   ```powershell
   node --version
   npm --version
   ```
   如果沒有安裝，請先到 [nodejs.org](https://nodejs.org) 下載安裝

2. **安裝 Vercel CLI**
   ```powershell
   npm install -g vercel
   ```

3. **登入你的帳號**
   ```powershell
   vercel login
   ```
   系統會開啟瀏覽器讓你登入 Vercel 帳號（使用 `rememory.fju.2025@gmail.com`）

### 📋 步驟二：部署專案

1. **進入部署資料夾**
   ```powershell
   cd vercel-deploy
   ```

2. **執行部署**
   ```powershell
   vercel
   ```

3. **CLI 互動問答**
   CLI 會自動偵測框架並詢問：
   
   ```
   ? Set up and deploy "vercel-deploy"? [Y/n] Y
   ? Which scope do you want to deploy to? Your personal account
   ? Link to existing project? [y/N] N
   ? What's your project's name? re-memory-fju-2025
   ? In which directory is your code located? ./
   ```

4. **部署完成**
   部署成功後會顯示：
   ```
   ✅ Production: https://re-memory-fju-2025.vercel.app [copied to clipboard]
   ```

### 📋 步驟三：設定環境變數

1. **方法一：透過 CLI**
   ```powershell
   vercel env add MONGODB_URI
   vercel env add DB_TYPE
   vercel env add GEMINI_API_KEY
   ```

2. **方法二：透過網頁**
   - 前往 [vercel.com/dashboard](https://vercel.com/dashboard)
   - 選擇你的專案
   - Settings → Environment Variables
   - 添加以下變數：
   
   ```
   MONGODB_URI = mongodb+srv://rememoryfju2025_db_user:AgAOvGRB5wlzHCje@cluster0.yvl3ug4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
   DB_TYPE = mongodb
   GEMINI_API_KEY = AIzaSyDD4JJV91yOm7NFm6AM3r3ZA-RYJiBp_7M
   ```

### 📋 步驟四：重新部署（應用環境變數）

```powershell
vercel --prod
```

### 🔄 後續更新

當你修改程式碼後，只需要：

1. **開發版部署**
   ```powershell
   vercel
   ```

2. **正式版部署**
   ```powershell
   vercel --prod
   ```

### 🛠️ 常用 CLI 指令

| 指令 | 說明 |
|------|------|
| `vercel` | 部署到預覽環境 |
| `vercel --prod` | 部署到正式環境 |
| `vercel ls` | 查看所有專案 |
| `vercel env ls` | 查看環境變數 |
| `vercel logs` | 查看部署日誌 |
| `vercel dev` | 本地開發模式 |

### ✅ CLI 優點

- 🚀 **快速更新**：不用重新上傳檔案
- 🔄 **版本控制**：每次部署都有版本記錄
- 📊 **即時日誌**：可以看到部署過程
- 🌐 **預覽功能**：可以先部署到測試環境
- ⚡ **自動偵測**：自動識別專案類型

### 🎉 完成！

使用 CLI 部署後，你的 Re Memory 應用程式就在雲端運行了！

網址格式：`https://re-memory-fju-2025.vercel.app`