#!/usr/bin/env python3.11
from dotenv import load_dotenv
import os
import sys

# 載入環境變數
load_dotenv()

# 加入專案根目錄到 Python 路徑
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import uvicorn

if __name__ == '__main__':
    # 將工作目錄設為 adminserver 目錄
    adminserver_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(adminserver_path)
    
    print("🚀 啟動語憶心聲管理後台 (Python 3.11)...")
    print(f"📂 工作目錄: {adminserver_path}")
    print(f"🌐 前端位址: http://127.0.0.1:8020")
    print(f"📊 API 文檔: http://127.0.0.1:8020/docs")
    
    uvicorn.run('server:app', host='127.0.0.1', port=8020, reload=True)