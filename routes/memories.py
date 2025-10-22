from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import SessionLocal
from database.models import Memory

# 建立 router
router = APIRouter(prefix="/api/memories", tags=["Memories"])

# --- 共用 DB Session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# === 1️⃣ 取得所有回憶 ===
@router.get("/")
def get_memories(db: Session = Depends(get_db)):
    memories = db.query(Memory).order_by(Memory.created_at.desc()).all()
    return [m.__dict__ for m in memories]

# === 2️⃣ 刪除指定回憶 ===
@router.delete("/{memory_id}")
def delete_memory(memory_id: int, db: Session = Depends(get_db)):
    memory = db.query(Memory).filter(Memory.id == memory_id).first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    db.delete(memory)
    db.commit()
    return {"ok": True, "message": "Memory deleted successfully"}
