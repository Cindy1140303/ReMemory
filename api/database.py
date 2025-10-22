# -*- coding: utf-8 -*-
import os
import datetime
from typing import Optional, List, Dict, Any
from .config import *

# === 雙重資料庫支援 ===

# MongoDB 連線
try:
    from pymongo import MongoClient
    from bson import ObjectId
    HAVE_MONGODB = True
except ImportError:
    MongoClient = None
    ObjectId = None
    HAVE_MONGODB = False

# MSSQL 連線（保留原有）
try:
    from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Text
    from sqlalchemy.orm import sessionmaker
    try:
        from sqlalchemy.orm import declarative_base
    except ImportError:
        from sqlalchemy.ext.declarative import declarative_base
    HAVE_SQLALCHEMY = True
except ImportError:
    HAVE_SQLALCHEMY = False

class DatabaseManager:
    def __init__(self):
        self.db_type = DATABASE_TYPE
        self._mongo_client = None
        self._mongo_db = None
        self._sql_session = None
        
        if self.db_type == "mongodb" and HAVE_MONGODB:
            self._init_mongodb()
        elif self.db_type == "mssql" and HAVE_SQLALCHEMY:
            self._init_mssql()
        else:
            print(f"❌ 不支援的資料庫類型或缺少依賴: {self.db_type}")
    
    def _init_mongodb(self):
        """初始化 MongoDB 連線"""
        try:
            self._mongo_client = MongoClient(MONGODB_URI)
            self._mongo_db = self._mongo_client[MONGODB_DB_NAME]
            # 測試連線
            self._mongo_client.admin.command('ping')
            print("✅ MongoDB 連線成功")
        except Exception as e:
            print(f"❌ MongoDB 連線失敗: {e}")
            self._mongo_client = None
    
    def _init_mssql(self):
        """初始化 MSSQL 連線（保留原有邏輯）"""
        try:
            engine = create_engine(MSSQL_URL, connect_args={"check_same_thread": False} if MSSQL_URL.startswith("sqlite") else {})
            SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
            
            # 定義原有的 Memory 模型
            Base = declarative_base()
            
            class Memory(Base):
                __tablename__ = "memories"
                id = Column(Integer, primary_key=True, index=True)
                text = Column(Text, default="")
                place = Column(String(255), default=None)
                lat = Column(Float, default=None)
                lng = Column(Float, default=None)
                photo_url = Column(String(512), default=None)
                created_at = Column(DateTime, default=datetime.datetime.utcnow)
            
            Base.metadata.create_all(bind=engine)
            self._sql_session = SessionLocal()
            self.Memory = Memory
            print("✅ MSSQL 連線成功")
        except Exception as e:
            print(f"❌ MSSQL 連線失敗: {e}")
            self._sql_session = None
    
    async def create_memory(self, text: str, place: Optional[str] = None, 
                           lat: Optional[float] = None, lng: Optional[float] = None,
                           photo_url: Optional[str] = None) -> Dict[str, Any]:
        """創建記憶"""
        if self.db_type == "mongodb" and self._mongo_db:
            doc = {
                "text": text,
                "place": place,
                "lat": lat,
                "lng": lng,
                "photo_url": photo_url,
                "created_at": datetime.datetime.utcnow()
            }
            result = self._mongo_db.memories.insert_one(doc)
            doc["_id"] = str(result.inserted_id)
            doc["id"] = str(result.inserted_id)
            return doc
        
        elif self.db_type == "mssql" and self._sql_session:
            memory = self.Memory(text=text, place=place, lat=lat, lng=lng, photo_url=photo_url)
            self._sql_session.add(memory)
            self._sql_session.commit()
            self._sql_session.refresh(memory)
            return {
                "id": memory.id,
                "text": memory.text,
                "place": memory.place,
                "lat": memory.lat,
                "lng": memory.lng,
                "photo_url": memory.photo_url,
                "created_at": memory.created_at
            }
        
        raise Exception("資料庫未初始化")
    
    async def list_memories(self, limit: Optional[int] = 100) -> List[Dict[str, Any]]:
        """列出記憶"""
        if self.db_type == "mongodb" and self._mongo_db:
            cursor = self._mongo_db.memories.find().sort("created_at", -1)
            if limit:
                cursor = cursor.limit(limit)
            
            memories = []
            for doc in cursor:
                doc["id"] = str(doc["_id"])
                memories.append(doc)
            return memories
        
        elif self.db_type == "mssql" and self._sql_session:
            query = self._sql_session.query(self.Memory).order_by(self.Memory.created_at.desc())
            if limit:
                query = query.limit(limit)
            
            memories = []
            for memory in query.all():
                memories.append({
                    "id": memory.id,
                    "text": memory.text,
                    "place": memory.place,
                    "lat": memory.lat,
                    "lng": memory.lng,
                    "photo_url": memory.photo_url,
                    "created_at": memory.created_at
                })
            return memories
        
        raise Exception("資料庫未初始化")
    
    async def update_memory(self, memory_id: str, **updates) -> bool:
        """更新記憶"""
        if self.db_type == "mongodb" and self._mongo_db:
            try:
                object_id = ObjectId(memory_id)
                result = self._mongo_db.memories.update_one(
                    {"_id": object_id}, 
                    {"$set": updates}
                )
                return result.modified_count > 0
            except:
                return False
        
        elif self.db_type == "mssql" and self._sql_session:
            try:
                memory = self._sql_session.get(self.Memory, int(memory_id))
                if memory:
                    for key, value in updates.items():
                        if hasattr(memory, key):
                            setattr(memory, key, value)
                    self._sql_session.commit()
                    return True
                return False
            except:
                return False
        
        raise Exception("資料庫未初始化")
    
    async def delete_memory(self, memory_id: str) -> bool:
        """刪除記憶"""
        if self.db_type == "mongodb" and self._mongo_db:
            try:
                object_id = ObjectId(memory_id)
                result = self._mongo_db.memories.delete_one({"_id": object_id})
                return result.deleted_count > 0
            except:
                return False
        
        elif self.db_type == "mssql" and self._sql_session:
            try:
                memory = self._sql_session.get(self.Memory, int(memory_id))
                if memory:
                    self._sql_session.delete(memory)
                    self._sql_session.commit()
                    return True
                return False
            except:
                return False
        
        raise Exception("資料庫未初始化")
    
    def close(self):
        """關閉連線"""
        if self._mongo_client:
            self._mongo_client.close()
        if self._sql_session:
            self._sql_session.close()

# 全域資料庫管理器
db_manager = DatabaseManager()