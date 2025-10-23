from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from datetime import datetime
from .db import Base

class Memory(Base):
    __tablename__ = "memories"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text)
    summary = Column(String(255))
    place_name = Column(String(100))
    lat = Column(Float)
    lng = Column(Float)
    date = Column(String(50))
    photo_url = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
