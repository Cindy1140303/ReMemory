# -*- coding: utf-8 -*-
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import json
import datetime
import sys
import os

# 添加 api 目錄到 path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from api.database import db_manager
    from api.config import *
except:
    # Vercel 環境的備用設定
    DATABASE_TYPE = os.getenv("DB_TYPE", "mongodb")
    MONGODB_URI = os.getenv("MONGODB_URI")

async def handler(request: Request):
    """健康檢查端點 - 支援 MongoDB 和 MSSQL"""
    try:
        # 檢查資料庫連線
        if DATABASE_TYPE == "mongodb" or os.getenv("DB_TYPE") == "mongodb":
            # MongoDB 連線測試
            try:
                from database.mongodb_models import get_memories
                memories = await get_memories()
                db_status = "MongoDB Atlas connected"
            except Exception as mongo_error:
                db_status = f"MongoDB connection failed: {str(mongo_error)}"
        else:
            # MSSQL 連線測試（保留原有邏輯）
            try:
                await db_manager.list_memories(limit=1)
                db_status = "MSSQL connected"
            except Exception as sql_error:
                db_status = f"MSSQL connection failed: {str(sql_error)}"
        
        return JSONResponse(content={
            "status": "healthy",
            "database": {
                "type": os.getenv("DB_TYPE", DATABASE_TYPE if 'DATABASE_TYPE' in globals() else "mongodb"),
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
                    "type": os.getenv("DB_TYPE", "unknown"),
                    "connected": False,
                    "error": str(e)
                },
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "environment": "vercel" if os.getenv("VERCEL") else "local"
            }
        )