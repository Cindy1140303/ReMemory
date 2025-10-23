# Re Memory - 生活記憶地圖應用

基於記憶和地理位置的生活軌跡記錄應用，支援語音記錄、地圖標記與 AI 聊天功能。

## 📁 專案結構

```
ReMemory/
│
├── README.md              # 專案說明
├── .gitignore            # Git 忽略檔案
├── .env                  # 全域環境變數
├── package.json          # Node.js 專案設定
├── node_modules/         # Node.js 模組
│
├── app/                  # 手機 App 版前後端
│   ├── android/          # Android 專案
│   ├── www/              # Capacitor 前端檔案
│   ├── builds/           # APK 構建產物
│   └── capacitor.config.json # Capacitor 設定
│
├── web/                  # 網頁測試版前後端
│   ├── src/              # 網頁前端原始碼
│   │   ├── index.html    # 主頁面
│   │   ├── manifest.json # PWA 設定
│   │   ├── server.py     # 開發用伺服器
│   │   └── service-worker.js # Service Worker
│   └── deployment/       # 部署相關檔案
│       ├── vercel.json   # Vercel 設定
│       └── vercel-deploy/ # Vercel 部署檔案
│
├── backendapi/           # 後端伺服器 (FastAPI)
│   ├── api/              # API 端點
│   ├── database/         # 資料庫模型
│   ├── routes/           # 路由定義
│   ├── requirements.txt  # Python 依賴
│   └── memories.db       # SQLite 資料庫
│
├── adminfrontend/        # 後台前端 (Vue.js + Tailwind CSS)
│   └── index.html        # 語音資料檢視介面
│
├── adminserver/          # 後台伺服器 (FastAPI + MongoDB)
│   ├── server.py         # 管理 API 伺服器
│   ├── run_admin.py      # 啟動腳本
│   ├── requirements.txt  # Python 依賴
│   └── README.md         # 後台說明文件
│
└── shared/               # 共用資源
    ├── assets/           # 應用資源
    ├── static/           # 靜態檔案
    ├── uploads/          # 上傳檔案
    ├── icon/             # 圖示檔案
    ├── tools/            # 開發工具 (FFmpeg 等)
    ├── scripts/          # 腳本工具
    ├── logs/             # 日誌檔案
    └── docs/             # 文檔
```

## 🚀 快速啟動

### 本地開發

1. **安裝依賴**
   ```bash
   pip install -r backendapi/requirements.txt
   npm install
   ```

2. **設定環境變數**
   ```bash
   cp .env.example .env
   # 編輯 .env 檔案，設定 GEMINI_API_KEY 等變數
   ```

3. **啟動開發伺服器**
   ```bash
   python shared/scripts/run_server.py
   ```

### Vercel 部署

1. **安裝 Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **部署到 Vercel**
   ```bash
   cd web/deployment
   vercel --prod
   ```

### 管理後台啟動

1. **安裝後台依賴**
   ```bash
   cd adminserver
   pip install -r requirements.txt
   ```

2. **設定 MongoDB 連線**
   ```bash
   # 在 .env 檔案中設定
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
   MONGODB_DB_NAME=lifemap
   ```

3. **啟動管理後台**
   ```bash
   python run_admin.py
   # 開啟 http://127.0.0.1:8020
   ```

## 🌟 主要功能

- 📍 **地理位置記錄** - 自動擷取並標記記憶位置
- 🎤 **語音轉文字** - 支援語音記錄並轉換為文字
- 🗺️ **互動式地圖** - 在地圖上顯示記憶標記
- 💬 **AI 聊天** - 與 Gemini AI 進行對話
- 📱 **跨平台支援** - Web 版本與 Android APK
- 🔄 **多重部署** - 本地、Vercel、Android 多平台部署
- 🎛️ **管理後台** - Vue.js 語音資料檢視與分析管理

## 🛠️ 技術架構

- **前端**: HTML5 + Tailwind CSS + Leaflet Maps
- **後端**: FastAPI + SQLite/MongoDB
- **移動端**: Capacitor
- **AI**: Google Gemini API
- **部署**: Vercel + MongoDB Atlas

## 📖 文檔

詳細的安裝、設定和使用說明請參閱 [`shared/docs/`](./shared/docs/) 目錄中的文檔：

- [詳細 README](./shared/docs/README.md)
- [Node.js 安裝指南](./shared/docs/NODEJS_INSTALL_GUIDE.md)
- [Vercel CLI 指南](./shared/docs/VERCEL_CLI_GUIDE.md)
- [APK 構建摘要](./shared/docs/APK_BUILD_SUMMARY.md)

## 📄 授權

ISC License

---

如有任何問題或建議，歡迎提出 Issue 或 Pull Request！