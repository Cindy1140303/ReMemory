# -*- coding: utf-8 -*-
import os
from typing import Optional

# 環境變數設定
DATABASE_TYPE = os.getenv("DATABASE_TYPE", "mongodb")  # "mongodb" or "mssql"

# === MongoDB 設定 ===
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://username:password@cluster.mongodb.net/lifemap?retryWrites=true&w=majority")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "lifemap")

# === MSSQL 設定（保留原有設定）===
MSSQL_URL = os.getenv("MSSQL_URL", "mssql+pyodbc://@DESKTOP-LGUQAO8/LifeMapDB?driver=ODBC%20Driver%2017%20for%20SQL%20Server&trusted_connection=yes")

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 上傳設定
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB

# Vercel 函數超時限制（秒）
VERCEL_TIMEOUT = 60

# 啟用的功能
ENABLE_CHAT = os.getenv("ENABLE_CHAT", "true").lower() == "true"
ENABLE_TRANSCRIPTION = os.getenv("ENABLE_TRANSCRIPTION", "true").lower() == "true"
ENABLE_GEOCODING = os.getenv("ENABLE_GEOCODING", "true").lower() == "true"

print(f"🔧 配置載入完成 - 資料庫類型: {DATABASE_TYPE}")