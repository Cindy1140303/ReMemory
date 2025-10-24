from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
import os
from dotenv import load_dotenv
import logging
from typing import Optional, List
import datetime
import json
import time
from typing import Any
from fastapi import Request

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

try:
    import certifi
except Exception:
    certifi = None

@app.on_event("startup")
async def startup_connect_mongo():
    """
    延遲在服務啟動時嘗試連線 MongoDB，增加重試與 TLS fallback 選項。
    環境變數：
      - MONGODB_TLS_INSECURE=true    # (開發) 若預設 TLS 失敗，允許忽略憑證驗證重試
      - MONGODB_CONNECT_RETRIES=3    # 重試次數（預設 3）
      - MONGODB_CONNECT_RETRY_DELAY=2 # 每次重試的基礎秒數（指數退避）
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

    # 連線重試參數
    retries = int(os.getenv("MONGODB_CONNECT_RETRIES", "3"))
    base_delay = float(os.getenv("MONGODB_CONNECT_RETRY_DELAY", "2"))
    allow_insecure = os.getenv("MONGODB_TLS_INSECURE", "false").lower() in ("1", "true", "yes")

    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Attempting MongoDB connection (attempt {attempt}/{retries})...")
            # 使用短 timeout 測試連線
            mongodb_client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
            db_name = os.getenv("MONGODB_DB_NAME", "lifemap")
            db = mongodb_client[db_name]
            # 測試連線
            mongodb_client.admin.command("ping")
            logger.info(f"✅ MongoDB 連線成功: {db_name}")
            return
        except Exception as e:
            last_exc = e
            # 檢查是否為 SSL/TLS 相關錯誤
            err_msg = str(e).lower()
            logger.warning(f"MongoDB connect attempt {attempt} failed: {e}")
            if ("ssl" in err_msg or "tls" in err_msg or "certificate" in err_msg) and allow_insecure:
                # 嘗試使用不安全的 TLS 選項重試一次（開發用）
                try:
                    logger.warning("Detected TLS/SSL issue and MONGODB_TLS_INSECURE=true -> retrying with tlsAllowInvalidCertificates")
                    connect_kwargs = {
                        "serverSelectionTimeoutMS": 5000,
                        "tls": True,
                        "tlsAllowInvalidCertificates": True
                    }
                    # 如果有 certifi，可提供 CA 作為第一選擇（不與 invalidCertificates 同時使用）
                    if certifi:
                        connect_kwargs.pop("tlsAllowInvalidCertificates", None)
                        connect_kwargs["tlsCAFile"] = certifi.where()
                        logger.info("Using certifi CA bundle for TLS.")
                    mongodb_client = MongoClient(mongodb_uri, **connect_kwargs)
                    db = mongodb_client[db_name]
                    mongodb_client.admin.command("ping")
                    logger.info(f"✅ MongoDB 連線成功 (insecure mode): {db_name}")
                    return
                except Exception as e2:
                    last_exc = e2
                    logger.exception(f"Retry with insecure TLS also failed: {e2}")
            # 若尚未到重試次數，退避後再試
            if attempt < retries:
                delay = base_delay * (2 ** (attempt - 1))
                logger.info(f"Waiting {delay} seconds before next attempt...")
                time.sleep(delay)

    # 如果到這裡仍失敗，回退到記憶體模式
    logger.error(f"❌ MongoDB 連線失敗，回退至記憶體模式。最後例外：{last_exc}")
    mongodb_client = None
    db = None
    HAVE_MONGO = False

# 記憶體儲存 (MongoDB 不可用時的備案)
memory_records = []

# 掛載前端靜態檔案（使用絕對路徑）
admin_frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "adminfrontend"))
if os.path.exists(admin_frontend_path):
    app.mount("/static", StaticFiles(directory=admin_frontend_path), name="static")

# === ✅ 修正：Vercel 為唯讀系統，改用 /tmp 作為暫存目錄 ===
if os.getenv("VERCEL_ENV"):
    # 在 Vercel Serverless 環境中，/var/task 是唯讀的，只能用 /tmp
    uploads_dir = "/tmp/uploads"
else:
    # 本地端開發仍使用原始 uploads 資料夾
    uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))

os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# ===== 新增：data 資料夾與 memories.json 路徑（支援 Vercel /tmp 與本機） =====
# 支援情境：
# 1) 若 adminserver/memories.json 已存在 (你現在的情況)，則直接使用該檔案（避免搬移）
# 2) 否則在 data 或 /tmp/data 建立並初始化 memories.json

admin_local_json = os.path.join(os.path.dirname(__file__), "memories.json")

if os.path.exists(admin_local_json):
    MEMORIES_JSON_PATH = admin_local_json
    data_dir = os.path.dirname(MEMORIES_JSON_PATH)
    logger.info(f"Found existing memories.json in adminserver folder, using: {MEMORIES_JSON_PATH}")
else:
    # 先依環境決定 data 資料夾位置
    if os.getenv("VERCEL_ENV"):
        data_dir = "/tmp/data"
    else:
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

    os.makedirs(data_dir, exist_ok=True)
    MEMORIES_JSON_PATH = os.path.join(data_dir, "memories.json")
    logger.info(f"No adminserver/memories.json found, using data path: {MEMORIES_JSON_PATH}")

# 如果不存在，建立一個初始的 JSON 檔案（避免讀取時例外）
if not os.path.exists(MEMORIES_JSON_PATH):
    try:
        with open(MEMORIES_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump({"memories": []}, f, ensure_ascii=False, indent=2)
        logger.info(f"Initialized memories.json at {MEMORIES_JSON_PATH}")
    except Exception as e:
        logger.warning(f"Unable to create memories.json at {MEMORIES_JSON_PATH}: {e}")

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
    """上傳語音檔案（使用絕對 uploads_dir、檢查大小並避免檔名衝突）"""
    try:
        # 變更：使用已宣告的 uploads_dir（絕對路徑）
        MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 最大 20 MB，可依需求調整
        
        # 取得安全檔名並加上 uuid 前綴避免衝突
        import uuid
        from pathlib import Path

        original_name = Path(file.filename).name  # 移除路徑成份
        safe_name = original_name.replace("/", "_").replace("\\", "_")
        unique_name = f"{uuid.uuid4().hex}_{safe_name}"
        file_path = os.path.join(uploads_dir, unique_name)

        # 讀取內容並檢查大小上限
        content = await file.read()
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="檔案過大，超過上限")

        # 寫入檔案
        with open(file_path, "wb") as buffer:
            buffer.write(content)

        # 創建記錄（使用 uploads_dir 對應的 URL 路徑）
        record = {
            "filename": original_name,
            "file_path": file_path,
            "file_url": f"/uploads/{unique_name}",
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

        return {"ok": True, "record_id": record["_id"], "message": "檔案上傳成功", "file_url": record["file_url"]}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"檔案上傳失敗: {str(e)}")

# ===== 新增匯入端點：讓前端可以匯入記憶資料 =====

@app.post("/api/import/memories")
async def import_memories(records: List[dict] = Body(...)):
    """
    匯入記憶（JSON body）
    範例 body: [ { "text": "...", "lat": 23.5, "lng": 120.9, "place": "台北", "created_at":"2023-10-01T12:00:00" }, ... ]
    """
    if not HAVE_MONGO or db is None:
        raise HTTPException(status_code=400, detail="MongoDB 未啟用。請於環境變數設定 MONGODB_URI 並啟用資料庫。")

    if not isinstance(records, list) or len(records) == 0:
        raise HTTPException(status_code=400, detail="請提供記憶陣列作為 JSON body。")

    to_insert = []
    for r in records:
        rec = {}
        rec["text"] = r.get("text", "") or r.get("description", "")
        rec["lat"] = r.get("lat") if "lat" in r else r.get("latitude")
        rec["lng"] = r.get("lng") if "lng" in r else r.get("longitude")
        rec["place"] = r.get("place") or r.get("place_name") or r.get("location")
        rec["photo_url"] = r.get("photo_url", "")
        # 解析 created_at（若為 ISO 字串）
        created = r.get("created_at") or r.get("createdAt") or None
        if isinstance(created, str):
            try:
                rec["created_at"] = datetime.datetime.fromisoformat(created)
            except Exception:
                try:
                    # fallback: parse without timezone if present
                    rec["created_at"] = datetime.datetime.fromisoformat(created.replace("Z", "+00:00"))
                except Exception:
                    rec["created_at"] = datetime.datetime.utcnow()
        elif isinstance(created, (int, float)):
            rec["created_at"] = datetime.datetime.utcfromtimestamp(float(created))
        else:
            rec["created_at"] = datetime.datetime.utcnow()

        # 可攜帶其他欄位
        rec["meta"] = r.get("meta", {})
        to_insert.append(rec)

    try:
        coll = db.memories
        result = coll.insert_many(to_insert)
        inserted_ids = [str(i) for i in result.inserted_ids]
        return {"ok": True, "inserted_count": len(inserted_ids), "ids": inserted_ids}
    except Exception as e:
        logger.exception("import_memories failed")
        raise HTTPException(status_code=500, detail=f"匯入失敗: {str(e)}")


@app.post("/api/import/upload-json")
async def import_memories_file(file: UploadFile = File(...)):
    """
    上傳 JSON 檔案並匯入記憶（multipart/form-data）
    檔案內容應為 JSON 陣列或物件 { "records": [...] }
    """
    if not HAVE_MONGO or db is None:
        raise HTTPException(status_code=400, detail="MongoDB 未啟用。請於環境變數設定 MONGODB_URI 並啟用資料庫。")

    try:
        content = await file.read()
        try:
            payload = json.loads(content)
        except Exception as jerr:
            raise HTTPException(status_code=400, detail=f"無法解析 JSON: {jerr}")

        # 支援直接陣列或包在 records 欄位內
        records = []
        if isinstance(payload, list):
            records = payload
        elif isinstance(payload, dict) and "records" in payload and isinstance(payload["records"], list):
            records = payload["records"]
        else:
            raise HTTPException(status_code=400, detail="JSON 格式錯誤，請傳入陣列或包含 records 欄位的物件。")

        # 重用上方邏輯：簡化呼叫
        req = await import_memories(records)  # 直接呼叫內部函式（會檢查並寫入）
        return req
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("import_memories_file failed")
        raise HTTPException(status_code=500, detail=f"上傳並匯入失敗: {str(e)}")

# ===== 新增：讓 service-worker.js 可從根路徑被取用（避免註冊失敗） =====

@app.get("/service-worker.js")
async def service_worker_root():
    """供瀏覽器註冊 service worker 用（把 adminfrontend/service-worker.js 映射到 /service-worker.js）"""
    sw_path = os.path.join(admin_frontend_path, "service-worker.js")
    if os.path.exists(sw_path):
        return FileResponse(sw_path, media_type="application/javascript")
    return Response(status_code=404)

# 可選：若你有對應的 map 檔案也一併提供
@app.get("/service-worker.js.map")
async def service_worker_map():
    map_path = os.path.join(admin_frontend_path, "service-worker.js.map")
    if os.path.exists(map_path):
        return FileResponse(map_path, media_type="application/json")
    return Response(status_code=404)

# ===== 新增端點：接收文字+位置+照片+錄音，上傳並同步至 MongoDB 與 memories.json =====
@app.post("/api/save_memory")
async def save_memory(
    text: Optional[str] = Form(None),
    place: Optional[str] = Form(None),
    lat: Optional[str] = Form(None),
    lng: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None)
):
    """
    接收表單（multipart/form-data）:
      - text, place, lat, lng (Form)
      - photo (file), audio (file)
    行為：
      1. 將上傳檔案儲存到 uploads_dir，並產生 /uploads/ 相對 URL
      2. 將記錄寫入 MongoDB（若可用）或記憶體陣列
      3. 同步 app 可使用的 memories.json（位於 MEMORIES_JSON_PATH）
    """
    try:
        import uuid
        from pathlib import Path

        # 解析 lat/lng 為 float（若可）
        def parse_float(v):
            try:
                return float(v) if v not in (None, "", "null") else None
            except:
                return None

        lat_val = parse_float(lat)
        lng_val = parse_float(lng)

        memory = {
            "text": text or "",
            "place": place or "",
            "lat": lat_val,
            "lng": lng_val,
            "created_at": datetime.datetime.utcnow().isoformat()
        }

        # 儲存上傳檔案（若有）
        saved_files = {}
        for file_field, upload in (("photo", photo), ("audio", audio)):
            if upload:
                original_name = Path(upload.filename).name
                safe_name = original_name.replace("/", "_").replace("\\", "_")
                unique_name = f"{uuid.uuid4().hex}_{safe_name}"
                file_path = os.path.join(uploads_dir, unique_name)

                content = await upload.read()
                with open(file_path, "wb") as fw:
                    fw.write(content)

                file_url = f"/uploads/{unique_name}"
                saved_files[file_field] = {
                    "original_name": original_name,
                    "file_path": file_path,
                    "file_url": file_url,
                    "size": len(content),
                    "content_type": upload.content_type
                }
                # 將對應欄位加入 memory
                if file_field == "photo":
                    memory["photo_url"] = file_url
                else:
                    memory["audio_url"] = file_url

                logger.info(f"Saved uploaded {file_field}: {file_path}")

        # 寫入 MongoDB 或記憶體
        if HAVE_MONGO and db is not None:
            coll = db.get_collection("memories")
            # 若資料包含 datetime 物件，轉為 ISO string 前已經處理 created_at
            insert_doc = memory.copy()
            result = coll.insert_one(insert_doc)
            memory["_id"] = str(result.inserted_id)
            logger.info(f"Inserted memory into MongoDB, id={memory['_id']}")
        else:
            # 使用記憶體儲存（確保 _id 欄位）
            memory["_id"] = f"mem_{len(memory_records)+1}"
            memory_records.append(memory)
            logger.info(f"Appended memory to memory_records, id={memory['_id']}")

        # 同步更新 memories.json（simple append，保護性讀寫）
        try:
            existing = {"memories": []}
            if os.path.exists(MEMORIES_JSON_PATH):
                with open(MEMORIES_JSON_PATH, "r", encoding="utf-8") as rf:
                    try:
                        parsed = json.load(rf)
                        # 支援兩種格式：{"memories": [...]} 或直接陣列
                        if isinstance(parsed, dict) and "memories" in parsed and isinstance(parsed["memories"], list):
                            existing = parsed
                        elif isinstance(parsed, list):
                            existing = {"memories": parsed}
                        else:
                            existing = {"memories": []}
                    except Exception:
                        existing = {"memories": []}

            # 準備可序列化的紀錄物件（把 _id / datetime 轉為字串）
            serializable = {k: (str(v) if isinstance(v, (datetime.datetime, ObjectId)) else v) for k, v in memory.items()}

            existing["memories"].append(serializable)

            with open(MEMORIES_JSON_PATH, "w", encoding="utf-8") as wf:
                json.dump(existing, wf, ensure_ascii=False, indent=2)

            logger.info(f"Appended memory to memories.json ({MEMORIES_JSON_PATH})")
        except Exception as jf:
            logger.exception(f"Failed to update memories.json: {jf}")

        return {"ok": True, "memory": memory}

    except Exception as e:
        logger.exception("save_memory failed")
        raise HTTPException(status_code=500, detail=f"儲存失敗: {str(e)}")

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