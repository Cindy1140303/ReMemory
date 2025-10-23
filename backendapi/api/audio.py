# -*- coding: utf-8 -*-
from fastapi import Request
from fastapi.responses import JSONResponse
import json
import sys
import os
import base64
import datetime

# 添加 api 目錄到 path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def handler(request: Request):
    """處理錄音相關的 API 請求 - 支援 MongoDB"""
    try:
        method = request.method
        
        # 只支援 MongoDB 儲存錄音
        if os.getenv("DB_TYPE") != "mongodb":
            return JSONResponse(
                status_code=503,
                content={"error": "Audio recording requires MongoDB"}
            )
            
        from database.mongodb_models import (
            get_audio_recordings, 
            create_audio_recording, 
            delete_audio_recording,
            AudioRecordingCreate
        )
        
        if method == "GET":
            # 列出所有錄音
            recordings = await get_audio_recordings()
            recordings_data = []
            for recording in recordings:
                recording_dict = recording.dict()
                recording_dict["id"] = str(recording_dict["id"])
                recording_dict.pop("_id", None)
                # 不返回完整的音頻數據，只返回基本資訊
                recording_dict.pop("audio_data", None)
                recordings_data.append(recording_dict)
            return JSONResponse(content=recordings_data)
        
        elif method == "POST":
            # 創建新錄音記錄
            body = await request.json()
            
            # 驗證必要的欄位
            if not body.get("audio_data"):
                return JSONResponse(
                    status_code=400,
                    content={"error": "audio_data is required"}
                )
            
            recording_data = AudioRecordingCreate(
                audio_data=body.get("audio_data"),
                transcription=body.get("transcription"),
                location=body.get("location"),
                latitude=body.get("latitude"),
                longitude=body.get("longitude"),
                place_name=body.get("place_name"),
                memory_id=body.get("memory_id"),
                source=body.get("source", "mobile_app"),
                duration=body.get("duration"),
                audio_type=body.get("audio_type", "audio/webm")
            )
            
            result = await create_audio_recording(recording_data)
            result_dict = result.dict()
            result_dict["id"] = str(result_dict["id"])
            result_dict.pop("_id", None)
            # 不返回完整的音頻數據
            result_dict.pop("audio_data", None)
            
            return JSONResponse(content=result_dict)
        
        elif method == "DELETE":
            # 刪除錄音記錄
            # 從 URL 路徑獲取 recording_id
            path_parts = request.url.path.split('/')
            if len(path_parts) > 3:
                recording_id = path_parts[-1]
                success = await delete_audio_recording(recording_id)
                if success:
                    return JSONResponse(content={"success": True})
                else:
                    return JSONResponse(
                        status_code=404,
                        content={"error": "Recording not found"}
                    )
            else:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Recording ID required"}
                )
        
        else:
            return JSONResponse(
                status_code=405, 
                content={"error": "Method not allowed"}
            )
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "timestamp": datetime.datetime.utcnow().isoformat()}
        )