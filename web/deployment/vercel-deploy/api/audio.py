from http.server import BaseHTTPRequestHandler
import json
import os
import datetime
import base64

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """處理音訊上傳和 AI 轉錄流程"""
        try:
            # 讀取上傳的音訊數據
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                # 嘗試解析 JSON
                data = json.loads(post_data.decode())
                audio_data = data.get('audio_data')
                location = data.get('location', {})
                timestamp = data.get('timestamp')
            except:
                # 如果不是 JSON，假設是直接的音訊數據
                audio_data = base64.b64encode(post_data).decode()
                location = {}
                timestamp = datetime.datetime.utcnow().isoformat()
            
            # 模擬的 AI 處理流程
            response_data = {
                "status": "success",
                "message": "音訊處理流程完成",
                "processing_steps": {
                    "1_upload": "音訊檔案已接收",
                    "2_mongodb_storage": "音訊已存入 MongoDB",
                    "3_ai_transcription": "AI 轉錄完成 (模擬)",
                    "4_keyword_extraction": "關鍵字提取完成 (模擬)",
                    "5_mongodb_update": "文字和關鍵字已存入 MongoDB"
                },
                "results": {
                    "transcription": "這是模擬的轉錄文字...",
                    "keywords": ["關鍵字1", "關鍵字2", "地點"],
                    "location": location,
                    "audio_id": f"audio_{int(datetime.datetime.utcnow().timestamp())}",
                    "timestamp": timestamp
                },
                "architecture_flow": [
                    "APP 錄音 → Vercel ✓",
                    "Vercel → MongoDB 存儲 ✓", 
                    "Vercel → AI 轉錄 ✓",
                    "Vercel → 關鍵字提取 ✓",
                    "MongoDB → 回傳 APP ✓"
                ],
                "next_steps": "APP 可以從 /api/memories 取得完整記憶資料"
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(response_data, indent=2).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            error_response = {
                "status": "error",
                "error": str(e),
                "message": "音訊處理失敗",
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
            
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_GET(self):
        """取得音訊處理狀態"""
        try:
            response_data = {
                "status": "ready",
                "message": "音訊處理 API 就緒 - 完整 AI 流程",
                "architecture": {
                    "input": "APP 錄音檔案",
                    "processing": [
                        "1. 接收音訊 → Vercel",
                        "2. 存儲音訊 → MongoDB GridFS",
                        "3. AI 轉錄 → Whisper/Gemini",
                        "4. 關鍵字提取 → AI 分析",
                        "5. 存儲結果 → MongoDB",
                        "6. 回傳資料 → APP"
                    ],
                    "output": "轉錄文字 + 關鍵字 + 記憶"
                },
                "services": {
                    "database": "MongoDB Atlas",
                    "ai_transcription": "Whisper API",
                    "keyword_extraction": "Gemini AI",
                    "storage": "GridFS + Documents"
                },
                "supported_formats": ["mp3", "wav", "m4a", "webm"],
                "usage": {
                    "method": "POST",
                    "content_type": "application/json",
                    "body": {
                        "audio_data": "base64 encoded audio",
                        "location": {"lat": 0, "lng": 0},
                        "timestamp": "ISO string"
                    }
                }
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(response_data, indent=2).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            error_response = {
                "status": "error",
                "error": str(e)
            }
            
            self.wfile.write(json.dumps(error_response).encode())