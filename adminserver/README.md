# 語憶心聲 - 管理後台

這是語憶心聲應用的管理後台，用於檢視和管理語音分析資料。

## 🏗️ 架構說明

```
APP(JS) 
  ↓ 錄音 → 封裝成 JSON
  ↓
MongoDB（雲端資料庫）
  ↓
Server（Python on Vercel）
  ↓ 語音轉文字 + 爬蟲分析地區、興趣名詞
  ↓
MongoDB 更新分析結果
  ↓
APP(JS) 取回結果顯示
  ↓
Debug UI 顯示分析狀況
```

## 📁 檔案結構

```
adminserver/
├── server.py           # FastAPI 後端伺服器
├── run_admin.py        # 啟動腳本
├── requirements.txt    # Python 依賴
└── README.md          # 說明文件

adminfrontend/
└── index.html         # Vue.js 管理介面
```

## 🚀 快速啟動

### 1. 安裝依賴

```bash
cd adminserver
pip install -r requirements.txt
```

### 2. 設定環境變數

在專案根目錄的 `.env` 檔案中設定：

```env
# MongoDB 設定
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DB_NAME=lifemap
```

### 3. 啟動管理後台

```bash
python run_admin.py
```

### 4. 開啟管理介面

在瀏覽器開啟：http://127.0.0.1:8020

## 🔧 API 端點

- `GET /` - 管理前端頁面
- `GET /api/health` - 健康檢查
- `GET /api/records` - 取得所有語音記錄
- `POST /api/analyze?id=<record_id>` - 觸發重新分析
- `POST /api/upload` - 上傳語音檔案
- `GET /docs` - API 文檔

## 📊 功能特色

### 前端管理介面
- 即時查看語音檔案分析狀態
- 支援分頁瀏覽大量資料
- 重新分析功能
- 響應式設計，支援手機/平板

### 後端 API
- MongoDB 整合（支援本地記憶體備案）
- 語音檔案上傳與管理
- 分析狀態追蹤
- RESTful API 設計

### 分析流程
1. **語音上傳** - 接收 APP 上傳的語音檔案
2. **語音轉文字** - 使用 ASR 模型轉換
3. **地區分析** - 分析文字中的地點資訊
4. **興趣分析** - 提取興趣關鍵詞
5. **狀態更新** - 更新分析結果到資料庫

## 🐛 除錯模式

### 測試資料
系統會自動建立測試資料（僅在記憶體模式下）：
- 已完成分析的記錄
- 處理中的記錄  
- 未分析的記錄

### 日誌檢視
- 伺服器啟動時會顯示連線狀態
- API 錯誤會記錄在終端

### 健康檢查
訪問 `/api/health` 查看：
- 伺服器狀態
- MongoDB 連線狀態
- 時間戳記

## ⚙️ 設定選項

### MongoDB 設定
- `MONGODB_URI` - MongoDB 連線字串
- `MONGODB_DB_NAME` - 資料庫名稱（預設：lifemap）

### 伺服器設定
- 預設端口：8020
- 預設主機：127.0.0.1
- 支援熱重載（開發模式）

## 🔒 安全注意事項

1. **CORS 設定** - 生產環境需限制允許的來源
2. **API 認證** - 未來應增加身份驗證
3. **檔案上傳** - 需要檔案類型與大小限制
4. **環境變數** - 敏感資訊不要提交到版本控制

## 📝 開發備註

- 使用 FastAPI 框架，支援自動 API 文檔
- 前端使用 Vue.js 3 + Tailwind CSS
- 支援 MongoDB 和記憶體儲存雙模式
- 響應式設計，適配各種螢幕尺寸