# -*- coding: utf-8 -*-
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import json
import datetime
import sys
import os

# 添加 api 目錄到 path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.database import db_manager
from api.config import *

async def handler(request: Request):
    """健康檢查端點 - 支援 MongoDB 和 MSSQL"""
    try:
        # 檢查資料庫連線
        if DATABASE_TYPE == "mongodb":
            # MongoDB 連線測試
            from database.mongodb_models import get_memories
            memories = await get_memories()
            db_status = "MongoDB Atlas connected"
        else:
            # MSSQL 連線測試（保留原有邏輯）
            await db_manager.list_memories(limit=1)
            db_status = "MSSQL connected"
        
        return JSONResponse(content={
            "status": "healthy",
            "database": {
                "type": DATABASE_TYPE,
                "status": db_status,
                "connected": True
            },
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "message": "Life Map API 運行正常",
            "environment": "vercel" if os.getenv("VERCEL") else "local",
            "mongodb_uri": "configured" if os.getenv("MONGODB_URI") else "not configured"
        })
    
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy", 
                "error": str(e),
                "database": {
                    "type": DATABASE_TYPE,
                    "connected": False,
                    "error": str(e)
                },
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "environment": "vercel" if os.getenv("VERCEL") else "local"
            }
        )