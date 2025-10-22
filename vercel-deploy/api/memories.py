# -*- coding: utf-8 -*-
from fastapi import Request
from fastapi.responses import JSONResponse
import json
import sys
import os

# 添加 api 目錄到 path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.database import db_manager

async def handler(request: Request):
    """處理記憶相關的 API 請求 - 支援 MongoDB 和 MSSQL"""
    try:
        method = request.method
        
        # 選擇資料庫引擎
        if os.getenv("DB_TYPE") == "mongodb":
            from database.mongodb_models import get_memories, create_memory, MemoryCreate
            use_mongodb = True
        else:
            use_mongodb = False
        
        if method == "GET":
            # 列出所有記憶
            if use_mongodb:
                memories = await get_memories()
                # 轉換 ObjectId 為字串
                memories_data = []
                for memory in memories:
                    memory_dict = memory.dict()
                    memory_dict["id"] = str(memory_dict["id"])
                    memory_dict.pop("_id", None)
                    memories_data.append(memory_dict)
                return JSONResponse(content=memories_data)
            else:
                memories = await db_manager.list_memories()
                return JSONResponse(content=memories)
        
        elif method == "POST":
            # 創建新記憶
            body = await request.json()
            
            if use_mongodb:
                memory_data = MemoryCreate(
                    text=body.get("text", ""),
                    place=body.get("place"),
                    lat=body.get("lat"),
                    lng=body.get("lng")
                )
                result = await create_memory(memory_data)
                result_dict = result.dict()
                result_dict["id"] = str(result_dict["id"])
                result_dict.pop("_id", None)
                return JSONResponse(content=result_dict)
            else:
                result = await db_manager.create_memory(
                    text=body.get("text", ""),
                    place=body.get("place"),
                    lat=body.get("lat"),
                    lng=body.get("lng")
                )
                return JSONResponse(content=result)
        
        else:
            return JSONResponse(
                status_code=405, 
                content={"error": "Method not allowed"}
            )
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "database_type": os.getenv("DB_TYPE", "mssql")}
        )