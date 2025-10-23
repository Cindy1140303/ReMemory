from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from dotenv import load_dotenv
from typing import Optional, List
import datetime
import json
import logging

# MongoDB
try:
    from pymongo import MongoClient
    from bson import ObjectId
    HAVE_MONGO = True
except ImportError:
    HAVE_MONGO = False
    print("WARNING: pymongo not installed. Using fallback memory storage.")

# 環境設定
load_dotenv()

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

if HAVE_MONGO:
    try:
        MONGODB_URI = os.getenv("MONGODB_URI")
        if MONGODB_URI:
            mongodb_client = MongoClient(MONGODB_URI)
            DB_NAME = os.getenv("MONGODB_DB_NAME", "lifemap")
            db = mongodb_client[DB_NAME]
            # 測試連接
            mongodb_client.admin.command('ping')
            print(f"✅ MongoDB 連線成功: {DB_NAME}")
        else:
            print("❌ MONGODB_URI 未設定，使用內存儲存")
            HAVE_MONGO = False
    except Exception as e:
        print(f"❌ MongoDB 連線失敗: {e}")
        HAVE_MONGO = False

# 記憶體儲存 (MongoDB 不可用時的備案)
memory_records = []

# 掛載前端靜態檔案
admin_frontend_path = os.path.join(os.path.dirname(__file__), "../adminfrontend")
if os.path.exists(admin_frontend_path):
    app.mount("/static", StaticFiles(directory=admin_frontend_path), name="static")

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
    """健康檢查"""
    return {
        "status": "ok",
        "mongodb_connected": HAVE_MONGO and mongodb_client is not None,
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
            # 記憶體版本
            for record in memory_records:
                if record["_id"] == id:
                    record["status"] = "processing"
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
            record["status"] = "done"
            record["text"] = "今天去了台北101，看到很美的夜景，心情很好。"
            record["region"] = "台北市"
            record["interest"] = "旅遊, 攝影, 城市景觀"
            break

# 建立一些測試資料
def create_test_data():
    """建立測試資料"""
    if not HAVE_MONGO:
        # 只在記憶體模式下建立測試資料
        test_records = [
            {
                "_id": "test_001",
                "filename": "recording_001.wav",
                "status": "done",
                "region": "台北市",
                "interest": "美食, 旅遊",
                "created_at": datetime.datetime.utcnow() - datetime.timedelta(days=1),
                "text": "今天去了信義區吃美食",
                "file_url": "/uploads/recording_001.wav"
            },
            {
                "_id": "test_002", 
                "filename": "recording_002.wav",
                "status": "processing",
                "region": "",
                "interest": "",
                "created_at": datetime.datetime.utcnow() - datetime.timedelta(hours=2),
                "text": "",
                "file_url": "/uploads/recording_002.wav"
            },
            {
                "_id": "test_003",
                "filename": "recording_003.wav", 
                "status": "",
                "region": "",
                "interest": "",
                "created_at": datetime.datetime.utcnow() - datetime.timedelta(minutes=30),
                "text": "",
                "file_url": "/uploads/recording_003.wav"
            }
        ]
        memory_records.extend(test_records)

# 啟動時建立測試資料
create_test_data()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8020, reload=True)