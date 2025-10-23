#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地測試 Vercel API 函數
"""

import os
import sys
import asyncio
import json

# 添加 api 目錄到 path
current_dir = os.path.dirname(os.path.abspath(__file__))
api_dir = os.path.join(current_dir, 'api')
sys.path.insert(0, api_dir)

async def test_database_connection():
    """測試資料庫連線"""
    print("🔧 測試資料庫連線...")
    
    try:
        from api.database import db_manager
        from api.config import DATABASE_TYPE
        
        print(f"📊 資料庫類型: {DATABASE_TYPE}")
        
        # 測試列出記憶（應該不會有錯誤，即使是空的）
        memories = await db_manager.list_memories(limit=1)
        print(f"✅ 資料庫連線成功！找到 {len(memories)} 筆記憶")
        
        return True
        
    except Exception as e:
        print(f"❌ 資料庫連線失敗: {e}")
        return False

async def test_create_memory():
    """測試創建記憶"""
    print("📝 測試創建記憶...")
    
    try:
        from api.database import db_manager
        
        test_memory = {
            "text": "測試記憶 - Vercel API",
            "place": "測試地點",
            "lat": 25.0330,
            "lng": 121.5654
        }
        
        result = await db_manager.create_memory(**test_memory)
        print(f"✅ 記憶創建成功！ID: {result.get('id')}")
        
        return result
        
    except Exception as e:
        print(f"❌ 記憶創建失敗: {e}")
        return None

async def main():
    """主測試函數"""
    print("🚀 開始測試 Vercel API 設定")
    print("=" * 50)
    
    # 檢查環境
    print("🔍 檢查環境設定...")
    print(f"Python 版本: {sys.version}")
    print(f"工作目錄: {os.getcwd()}")
    
    # 測試資料庫連線
    db_success = await test_database_connection()
    
    if db_success:
        # 測試創建記憶
        memory = await test_create_memory()
        
        if memory:
            print("\n🎉 所有測試通過！Vercel API 設定正常")
            print("\n📋 下一步:")
            print("1. 設定 MongoDB Atlas 連線字串")
            print("2. 執行 deploy.bat 部署到 Vercel")
            print("3. 更新前端 API_ENDPOINTS.current 設定")
        else:
            print("\n❌ 記憶創建測試失敗")
    else:
        print("\n❌ 資料庫連線測試失敗")
        print("\n🔧 請檢查:")
        print("- MongoDB Atlas 連線字串是否正確")
        print("- 網路連線是否正常")
        print("- 環境變數是否設定正確")

if __name__ == "__main__":
    asyncio.run(main())