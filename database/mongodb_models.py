"""
MongoDB 資料模型
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from bson import ObjectId
import motor.motor_asyncio
import os

# MongoDB 連線設定
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
database = client.lifemap_db

# Collections
memories_collection = database.memories
audio_collection = database.audio_recordings

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class MemoryModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    text: str = ""
    place: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    photo_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

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

class AudioRecordingModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    audio_data: str  # Base64 encoded audio
    transcription: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    place_name: Optional[str] = None
    memory_id: Optional[str] = None
    source: str = "unknown"
    duration: Optional[float] = None
    audio_type: str = "audio/webm"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    synced: bool = False

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class AudioRecordingCreate(BaseModel):
    audio_data: str
    transcription: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    place_name: Optional[str] = None
    memory_id: Optional[str] = None
    source: str = "unknown"
    duration: Optional[float] = None
    audio_type: str = "audio/webm"

# 資料庫操作函數
async def create_memory(memory_data: MemoryCreate) -> MemoryModel:
    """創建新的記憶"""
    memory_dict = memory_data.dict()
    memory_dict["created_at"] = datetime.utcnow()
    
    result = await memories_collection.insert_one(memory_dict)
    memory_dict["_id"] = result.inserted_id
    
    return MemoryModel(**memory_dict)

async def get_memories() -> List[MemoryModel]:
    """獲取所有記憶"""
    memories = []
    async for memory in memories_collection.find().sort("created_at", -1):
        memories.append(MemoryModel(**memory))
    return memories

async def get_memory(memory_id: str) -> Optional[MemoryModel]:
    """根據 ID 獲取記憶"""
    memory = await memories_collection.find_one({"_id": ObjectId(memory_id)})
    if memory:
        return MemoryModel(**memory)
    return None

async def update_memory(memory_id: str, memory_data: MemoryUpdate) -> bool:
    """更新記憶"""
    update_data = {k: v for k, v in memory_data.dict().items() if v is not None}
    if not update_data:
        return False
        
    result = await memories_collection.update_one(
        {"_id": ObjectId(memory_id)}, 
        {"$set": update_data}
    )
    return result.modified_count > 0

async def delete_memory(memory_id: str) -> bool:
    """刪除記憶"""
    result = await memories_collection.delete_one({"_id": ObjectId(memory_id)})
    return result.deleted_count > 0

async def create_audio_recording(audio_data: AudioRecordingCreate) -> AudioRecordingModel:
    """創建新的錄音記錄"""
    audio_dict = audio_data.dict()
    audio_dict["created_at"] = datetime.utcnow()
    
    result = await audio_collection.insert_one(audio_dict)
    audio_dict["_id"] = result.inserted_id
    
    return AudioRecordingModel(**audio_dict)

async def get_audio_recordings() -> List[AudioRecordingModel]:
    """獲取所有錄音記錄"""
    recordings = []
    async for recording in audio_collection.find().sort("created_at", -1):
        recordings.append(AudioRecordingModel(**recording))
    return recordings

async def delete_audio_recording(recording_id: str) -> bool:
    """刪除錄音記錄"""
    result = await audio_collection.delete_one({"_id": ObjectId(recording_id)})
    return result.deleted_count > 0