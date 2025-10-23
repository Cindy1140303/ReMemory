# 🚀 Node.js 安裝與 Vercel CLI 快速指南

## 📦 步驟一：安裝 Node.js

你的系統有 npm (10.9.3) 但缺少 Node.js，需要完整安裝：

### 方法一：官方安裝包（推薦）
1. 前往 https://nodejs.org
2. 下載 LTS 版本（推薦）
3. 執行安裝檔，全部選擇預設值
4. 重新開啟 PowerShell

### 方法二：透過 Chocolatey
```powershell
# 如果有 Chocolatey
choco install nodejs
```

### 方法三：透過 Winget
```powershell
# Windows 10/11 內建
winget install OpenJS.NodeJS
```

## 🔧 步驟二：驗證安裝

安裝完成後，重新開啟 PowerShell 並執行：

```powershell
node --version
npm --version
```

應該看到類似：
```
v20.9.0
10.9.3
```

## 🚀 步驟三：安裝 Vercel CLI

```powershell
npm install -g vercel
```

## 📋 步驟四：部署流程

```powershell
# 1. 登入
vercel login

# 2. 進入專案資料夾
cd vercel-deploy

# 3. 部署
vercel

# 4. 設定環境變數（透過網頁較簡單）
# 前往 vercel.com → 專案 → Settings → Environment Variables

# 5. 重新部署以應用環境變數
vercel --prod
```

## 🎯 如果不想安裝 Node.js

**直接使用拖拉部署**：
1. 前往 https://vercel.com
2. 註冊/登入
3. 點擊 "Add New..." → "Project"
4. 拖拉整個 `vercel-deploy` 資料夾
5. 設定環境變數
6. 完成！

## 📞 需要協助？

如果 Node.js 安裝有問題，我們可以：
1. 使用拖拉部署（最簡單）
2. 使用 GitHub 部署
3. 協助解決 Node.js 安裝問題

CLI 的優點是後續更新方便，但如果只是要快速部署，拖拉方式更簡單！