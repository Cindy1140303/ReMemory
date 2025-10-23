from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from dotenv import load_dotenv
import logging
from typing import Optional, List
import datetime
import json

# -------------- 新增：logging 與明確載入專案根目錄 .env --------------
# 設定 logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# 優先從專案根目錄載入 .env（adminserver 在子資料夾，原本可能讀不到根目錄的 .env）
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
dotenv_path = os.path.join(project_root, ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    logger.info(f"Loaded .env from project root: {dotenv_path}")
else:
    logger.info(".env not found at project root, loaded default locations if any")

# MongoDB
try:
    from pymongo import MongoClient
    from bson import ObjectId
    HAVE_MONGO = True
except ImportError:
    HAVE_MONGO = False
    print("WARNING: pymongo not installed. Using fallback memory storage.")

# FastAPI 應用
app = FastAPI(title="語憶心聲 Admin API", description="後端資料檢視與分析 API")

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開發環境，生產環境需限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB 連接
mongodb_client = None
db = None

@app.on_event("startup")
async def startup_connect_mongo():
    """
    延遲在服務啟動時嘗試連線 MongoDB，若失敗會回退到記憶體模式 (HAVE_MONGO = False)。
    這樣可以避免在模組匯入時因網路/SSL 問題導致整個應用啟動失敗。
    """
    global mongodb_client, db, HAVE_MONGO

    if not HAVE_MONGO:
        logger.info("pymongo not installed - skipping MongoDB connection.")
        return

    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        logger.info("MONGODB_URI not set - running in memory mode.")
        HAVE_MONGO = False
        return

    try:
        # 縮短連線測試的 timeout，避免啟動時卡太久
        mongodb_client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        db_name = os.getenv("MONGODB_DB_NAME", "lifemap")
        db = mongodb_client[db_name]

        # 測試連線
        mongodb_client.admin.command("ping")
        logger.info(f"✅ MongoDB 連線成功: {db_name}")
    except Exception as e:
        logger.exception(f"❌ MongoDB 連線失敗: {e}")
        mongodb_client = None
        db = None
        HAVE_MONGO = False

# 記憶體儲存 (MongoDB 不可用時的備案)
memory_records = []

# 掛載前端靜態檔案（使用絕對路徑）
admin_frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "adminfrontend"))
if os.path.exists(admin_frontend_path):
    app.mount("/static", StaticFiles(directory=admin_frontend_path), name="static")

# 掛載 uploads 靜態檔案，並確保資料夾存在
uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# ===== API 端點 =====

@app.get("/")
async def serve_admin_frontend():
    """提供管理前端頁面"""
    frontend_file = os.path.join(admin_frontend_path, "index.html")
    if os.path.exists(frontend_file):
        return FileResponse(frontend_file)
    return {"message": "Admin Frontend not found", "path": admin_frontend_path}

@app.get("/api/health")
async def health_check():
    """健康檢查（回傳額外診斷資訊以利除錯）"""
    # 讀取環境變數狀態（不回傳完整 URI，只回傳是否存在）
    mongodb_uri_present = bool(os.getenv("MONGODB_URI"))
    return {
        "status": "ok",
        "mongodb_connected": HAVE_MONGO and mongodb_client is not None,
        "mongodb_uri_present": mongodb_uri_present,
        "uploads_dir": uploads_dir,
        "admin_frontend_path": admin_frontend_path,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

@app.get("/api/records")
async def get_records():
    """取得所有語音記錄"""
    try:
        if HAVE_MONGO and db is not None:
            # 從 MongoDB 取得記錄
            records = []
            collection = db.voice_records  # 語音記錄集合
            cursor = collection.find().sort("created_at", -1)  # 最新的在前
            
            for doc in cursor:
                record = {
                    "_id": str(doc["_id"]),
                    "filename": doc.get("filename", "未命名"),
                    "status": doc.get("analysis_status", ""),
                    "region": doc.get("region_analysis", ""),
                    "interest": doc.get("interest_analysis", ""),
                    "created_at": doc.get("created_at", ""),
                    "text": doc.get("transcribed_text", ""),
                    "file_url": doc.get("file_url", "")
                }
                records.append(record)
            
            return records
        else:
            # 使用記憶體儲存
            return memory_records
            
    except Exception as e:
        print(f"Error fetching records: {e}")
        raise HTTPException(status_code=500, detail=f"取得記錄失敗: {str(e)}")

@app.post("/api/analyze")
async def trigger_analysis(id: str):
    """觸發重新分析"""
    try:
        if HAVE_MONGO and db is not None:
            # MongoDB 版本
            collection = db.voice_records
            result = collection.update_one(
                {"_id": ObjectId(id)},
                {
                    "$set": {
                        "analysis_status": "processing",
                        "analysis_started_at": datetime.datetime.utcnow()
                    }
                }
            )
            
            if result.matched_count == 0:
                raise HTTPException(status_code=404, detail="記錄不存在")
            
            # 這裡應該觸發實際的分析流程
            # 目前先模擬分析完成
            await simulate_analysis(id)
            
            return {"ok": True, "message": f"已啟動 ID {id} 的分析任務"}
        else:
            # 記憶體版本（欄位與 MongoDB 版保持一致）
            for record in memory_records:
                if record["_id"] == id:
                    record["analysis_status"] = "processing"
                    # 模擬分析
                    await simulate_analysis_memory(id)
                    return {"ok": True, "message": f"已啟動 ID {id} 的分析任務"}
            
            raise HTTPException(status_code=404, detail="記錄不存在")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error triggering analysis: {e}")
        raise HTTPException(status_code=500, detail=f"分析啟動失敗: {str(e)}")

@app.post("/api/upload")
async def upload_voice_file(file: UploadFile = File(...), metadata: Optional[str] = Form(None)):
    """上傳語音檔案"""
    try:
        # 儲存檔案
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 創建記錄
        record = {
            "filename": file.filename,
            "file_path": file_path,
            "file_url": f"/uploads/{file.filename}",
            "analysis_status": "pending",
            "region_analysis": "",
            "interest_analysis": "",
            "transcribed_text": "",
            "created_at": datetime.datetime.utcnow(),
            "metadata": json.loads(metadata) if metadata else {}
        }
        
        if HAVE_MONGO and db is not None:
            # 儲存到 MongoDB
            collection = db.voice_records
            result = collection.insert_one(record)
            record["_id"] = str(result.inserted_id)
        else:
            # 儲存到記憶體
            record["_id"] = f"mem_{len(memory_records)}"
            memory_records.append(record)
        
        return {"ok": True, "record_id": record["_id"], "message": "檔案上傳成功"}
        
    except Exception as e:
        print(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"檔案上傳失敗: {str(e)}")

# ===== 輔助函數 =====

async def simulate_analysis(record_id: str):
    """模擬分析流程 (MongoDB 版本)"""
    import asyncio
    
    # 模擬分析時間
    await asyncio.sleep(2)
    
    if HAVE_MONGO and db is not None:
        collection = db.voice_records
        
        # 模擬語音轉文字
        mock_text = "今天去了台北101，看到很美的夜景，心情很好。"
        
        # 模擬地區分析
        mock_region = "台北市"
        
        # 模擬興趣分析
        mock_interest = "旅遊, 攝影, 城市景觀"
        
        # 更新分析結果
        collection.update_one(
            {"_id": ObjectId(record_id)},
            {
                "$set": {
                    "analysis_status": "done",
                    "transcribed_text": mock_text,
                    "region_analysis": mock_region,
                    "interest_analysis": mock_interest,
                    "analysis_completed_at": datetime.datetime.utcnow()
                }
            }
        )

async def simulate_analysis_memory(record_id: str):
    """模擬分析流程 (記憶體版本)"""
    import asyncio
    
    # 模擬分析時間
    await asyncio.sleep(2)
    
    for record in memory_records:
        if record["_id"] == record_id:
            record["analysis_status"] = "done"
            record["transcribed_text"] = "今天去了台北101，看到很美的夜景，心情很好。"
            record["region_analysis"] = "台北市"
            record["interest_analysis"] = "旅遊, 攝影, 城市景觀"
            record["analysis_completed_at"] = datetime.datetime.utcnow()
            break

# 建立一些測試資料
def create_test_data():
    """建立測試資料"""
    if not HAVE_MONGO:
        # 只在記憶體模式下建立測試資料（欄位名稱與 MongoDB 版一致）
        test_records = [
            {
                "_id": "test_001",
                "filename": "recording_001.wav",
                "analysis_status": "done",
                "region_analysis": "台北市",
                "interest_analysis": "美食, 旅遊",
                "created_at": datetime.datetime.utcnow() - datetime.timedelta(days=1),
                "transcribed_text": "今天去了信義區吃美食",
                "file_url": "/uploads/recording_001.wav"
            },
            {
                "_id": "test_002", 
                "filename": "recording_002.wav",
                "analysis_status": "processing",
                "region_analysis": "",
                "interest_analysis": "",
                "created_at": datetime.datetime.utcnow() - datetime.timedelta(hours=2),
                "transcribed_text": "",
                "file_url": "/uploads/recording_002.wav"
            },
            {
                "_id": "test_003",
                "filename": "recording_003.wav", 
                "analysis_status": "",
                "region_analysis": "",
                "interest_analysis": "",
                "created_at": datetime.datetime.utcnow() - datetime.timedelta(minutes=30),
                "transcribed_text": "",
                "file_url": "/uploads/recording_003.wav"
            }
        ]
        memory_records.extend(test_records)

# 啟動時建立測試資料
create_test_data()

if __name__ == "__main__":
    import uvicorn
    # 改為 0.0.0.0 以便外部連線（若不需要可改回 127.0.0.1）
    logger.info("啟動 API (uvicorn) - host=0.0.0.0 port=8020")
    uvicorn.run(app, host="0.0.0.0", port=8020, reload=True)