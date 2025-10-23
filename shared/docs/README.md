# Life Map - Re Memory

基於記憶和地理位置的生活軌跡記錄應用。

## 🌟 功能特色

- 📍 地理位置記錄
- 🎤 語音記錄與轉文字
- 🗺️ 互動式地圖顯示
- 📱 跨平台支援 (Web + Android APK)
- 🔄 離線/線上同步

## 🚀 部署方式

### Vercel + MongoDB Atlas (推薦)

1. **MongoDB Atlas 設定**
   - 註冊 [MongoDB Atlas](https://cloud.mongodb.com/)
   - 創建免費 Cluster
   - 獲取連線字串

2. **Vercel 部署**
   ```bash
   # 安裝 Vercel CLI
   npm i -g vercel
   
   # 部署
   vercel --prod
   ```

3. **環境變數設定**
   在 Vercel Dashboard 設定：
   - `MONGODB_URI`: MongoDB 連線字串
   - `GEMINI_API_KEY`: Google Gemini API Key (可選)

### 本地開發 (MSSQL)

```bash
# 安裝依賴
pip install -r requirements.txt

# 啟動伺服器
python run_server.py
```

## 📱 Android APK

使用 Capacitor 打包為 Android 應用：

```bash
npm install
npx cap sync android
npx cap build android
```

## 🔧 技術架構

- **前端**: HTML5 + Tailwind CSS + Leaflet
- **後端**: FastAPI + MongoDB/MSSQL
- **移動端**: Capacitor
- **部署**: Vercel + MongoDB Atlas

## 📄 API 端點

- `GET /api/health` - 健康檢查
- `GET /api/memories` - 獲取記憶列表
- `POST /api/memories` - 創建新記憶
- `PUT /api/memories/{id}` - 更新記憶
- `DELETE /api/memories/{id}` - 刪除記憶

## 🌍 環境變數

```env
# 資料庫選擇
DATABASE_TYPE=mongodb  # or mssql

# MongoDB 設定
MONGODB_URI=mongodb+srv://...
MONGODB_DB_NAME=lifemap

# MSSQL 設定 (保留)
MSSQL_URL=mssql+pyodbc://...

# API Keys
GEMINI_API_KEY=your_gemini_key
```

## 📦 檔案結構

```
life-map-app/
├── www/              # 前端檔案 (Vercel 靜態檔案)
├── api/              # Vercel API Functions
├── android/          # Android 專案
├── server.py         # 本地 FastAPI 伺服器 (保留)
├── vercel.json       # Vercel 配置
└── requirements-vercel.txt  # Vercel 依賴
```

## 🎯 使用方式

1. 開啟地圖介面
2. 點擊錄音按鈕記錄語音
3. 系統自動獲取地理位置
4. 語音轉文字並儲存
5. 在地圖上顯示記憶標記