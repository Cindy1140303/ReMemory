from fastapi import APIRouter, UploadFile, File
from PIL import Image
import os

router = APIRouter()

UPLOAD_DIR = "static/photos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/api/photo/upload")
async def upload_photo(file: UploadFile = File(...)):
    img = Image.open(file.file)
    img.thumbnail((300, 300))
    path = os.path.join(UPLOAD_DIR, file.filename)
    img.save(path)
    return {"photo_url": path}
