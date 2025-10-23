# -*- coding: utf-8 -*-
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import os
import sys
import datetime

# 添加 api 目錄到 path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import db_manager
from config import *

app = FastAPI(title="Life Map API - Vercel")

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生產環境中應該限制為特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MemoryCreate(BaseModel):
    text: str
    place: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None

class MemoryUpdate(BaseModel):
    text: Optional[str] = None
    place: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None

@app.get("/")
async def root():
    return {
        "message": "Life Map API - Vercel 版本",
        "database": DATABASE_TYPE,
        "status": "running",
        "endpoints": [
            "/api/memories - GET/POST",
            "/api/memories/{id} - PUT/DELETE", 
            "/api/health - GET"
        ]
    }

@app.get("/api/health")
async def health_check():
    """健康檢查端點"""
    try:
        # 簡單的資料庫連線測試
        if DATABASE_TYPE == "mongodb":
            await db_manager.list_memories(limit=1)
        return {
            "status": "healthy",
            "database": DATABASE_TYPE,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy", 
                "error": str(e),
                "database": DATABASE_TYPE
            }
        )

@app.post("/api/memories")
async def create_memory(memory: MemoryCreate):
    """創建新記憶"""
    try:
        result = await db_manager.create_memory(
            text=memory.text,
            place=memory.place,
            lat=memory.lat,
            lng=memory.lng
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/memories")
async def list_memories(limit: Optional[int] = 100):
    """列出所有記憶"""
    try:
        memories = await db_manager.list_memories(limit=limit)
        return memories
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/memories/{memory_id}")
async def update_memory(memory_id: str, memory: MemoryUpdate):
    """更新記憶"""
    try:
        updates = {k: v for k, v in memory.dict().items() if v is not None}
        success = await db_manager.update_memory(memory_id, **updates)
        if success:
            return {"success": True}
        else:
            raise HTTPException(status_code=404, detail="記憶不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/memories/{memory_id}")
async def delete_memory(memory_id: str):
    """刪除記憶"""
    try:
        success = await db_manager.delete_memory(memory_id)
        if success:
            return {"success": True}
        else:
            raise HTTPException(status_code=404, detail="記憶不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Vercel 處理器（實際上不會被調用，但保留兼容性）
def handler(request):
    return app