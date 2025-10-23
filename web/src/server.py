import os
import io
import base64
import datetime
import requests
from dotenv import load_dotenv
from typing import Optional, List

try:
    import google.generativeai as genai
    HAVE_GEMINI = True
except Exception:
    genai = None
    HAVE_GEMINI = False
    import logging
    logging.warning("google.generativeai not installed; /api/chat endpoint will be disabled until package is installed and GEMINI_API_KEY configured.")
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import subprocess
import tempfile
import shlex
import json
import logging
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Text
from sqlalchemy.orm import sessionmaker
try:
    from sqlalchemy.orm import declarative_base
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from PIL import Image
try:
    # faster-whisper is optional; if missing the endpoint will raise 503
    from faster_whisper import WhisperModel
    HAVE_FASTER_WHISPER = True
except Exception:
    WhisperModel = None
    HAVE_FASTER_WHISPER = False

# ------------------ 環境設定 ------------------
load_dotenv()
if HAVE_GEMINI:
    # configure only when SDK is available
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
else:
    # No-op when library missing; chat endpoint will return 503
    pass

DB_URL = os.getenv("MSSQL_URL", "sqlite:///memory.db")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ------------------ FastAPI 初始化 ------------------
app = FastAPI(title="Life Map API (Gemini版)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ------------------ DB 設定 ------------------
Base = declarative_base()
engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

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

# ------------------ Models ------------------
class MemoryCreate(BaseModel):
    text: str

class MemoryUpdate(BaseModel):
    text: Optional[str] = None
    place: Optional[str] = None

# ------------------ Transcription (faster-whisper) ------------------
# Model cache (load once per process)
_fw_model = None
_fw_model_name = os.getenv('FW_MODEL', 'small')  # default model size; change as needed
_fw_compute_type = os.getenv('FW_COMPUTE_TYPE', None)

def get_faster_whisper_model(model_name: str = None):
    global _fw_model, _fw_model_name, _fw_compute_type
    if not HAVE_FASTER_WHISPER:
        return None
    if model_name is None:
        model_name = _fw_model_name

    # decide device and compute_type
    device = os.getenv('FW_DEVICE', 'cpu')
    compute_type = os.getenv('FW_COMPUTE_TYPE', _fw_compute_type)
    # If not explicitly set and running on CPU, prefer int8 for speed and smaller memory
    if compute_type is None and device == 'cpu':
        compute_type = 'int8'

    # allow tuning threads for CPU-bound inference
    fw_threads = os.getenv('FW_THREADS')
    if fw_threads:
        try:
            import os as _os
            _os.environ['OMP_NUM_THREADS'] = str(int(fw_threads))
        except Exception:
            pass

    if _fw_model is None or model_name != _fw_model_name or compute_type != _fw_compute_type:
        try:
            # WhisperModel accepts compute_type for faster-whisper (int8/float16/float32)
            _fw_model = WhisperModel(model_name, device=device, compute_type=compute_type)
            _fw_model_name = model_name
            _fw_compute_type = compute_type
        except Exception as e:
            logging.exception('Failed to load faster-whisper model')
            _fw_model = None
            raise
    return _fw_model


def _convert_to_wav(input_path: str, output_path: str):
    """Use ffmpeg (CLI) to convert any input audio to 16kHz mono WAV (PCM S16LE)."""
    import shutil

    # allow overriding ffmpeg executable via environment variable (useful if user didn't add to PATH)
    ffmpeg_env = os.getenv('FFMPEG_PATH')
    ffmpeg_path = None
    if ffmpeg_env:
        # prefer explicit path if provided and exists
        if os.path.exists(ffmpeg_env):
            ffmpeg_path = ffmpeg_env
        else:
            # try quoting or direct lookup if user provided directory
            candidate = os.path.join(ffmpeg_env, 'ffmpeg.exe') if os.path.isdir(ffmpeg_env) else ffmpeg_env
            if os.path.exists(candidate):
                ffmpeg_path = candidate
    if not ffmpeg_path:
        ffmpeg_path = shutil.which('ffmpeg')
    if not ffmpeg_path:
        raise RuntimeError("ffmpeg not found. Install ffmpeg or set environment variable FFMPEG_PATH to the ffmpeg executable path.")

    # build command as list to avoid shell parsing issues
    cmd = [ffmpeg_path, '-y', '-i', input_path, '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le', output_path]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        # prefer stderr as utf-8 but fallback to latin-1 to avoid loss
        try:
            err = proc.stderr.decode('utf-8', errors='ignore')
        except Exception:
            err = proc.stderr.decode('latin-1', errors='ignore')
        raise RuntimeError(f"ffmpeg failed (exit {proc.returncode}): {err}")


@app.post('/api/transcribe')
async def transcribe(file: UploadFile = File(...), model: Optional[str] = Form(None), beam_size: Optional[int] = Form(None), threads: Optional[int] = Form(None), debug: Optional[bool] = Form(False), target_script: Optional[str] = Form(None), fast: Optional[bool] = Form(False)):
    """Upload an audio file and return transcribed text using faster-whisper.

    Optional form field `model` can override the FW_MODEL (e.g., 'small', 'medium', 'large-v2').
    """
    if not HAVE_FASTER_WHISPER:
        raise HTTPException(status_code=503, detail='faster-whisper 未安裝，請在環境中安裝 faster-whisper。')

    # save uploaded file to a temp file
    try:
        suffix = os.path.splitext(file.filename or '')[1] or '.webm'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_in:
            data = await file.read()
            tmp_in.write(data)
            tmp_in.flush()
            tmp_in_path = tmp_in.name

        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_out:
            tmp_out_path = tmp_out.name

        # convert to 16k mono wav
        try:
            _convert_to_wav(tmp_in_path, tmp_out_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f'音訊轉檔失敗: {e}')

        # load model (cached)
        try:
            fw_model = get_faster_whisper_model(model if model else None)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f'模型載入失敗: {e}')

        # transcribe: faster-whisper supports streaming segments; here we run a simple sync transcribe
        try:
            # tuning: use provided beam_size or env/default; smaller beam_size -> faster
            # default beam size: prefer smaller beam for lower latency (env FW_BEAM can override)
            if beam_size is None:
                beam_size = int(os.getenv('FW_BEAM', '1'))

            # if client requests a fast mode, enforce low-beam low-latency settings
            if fast:
                try:
                    beam_size = 1
                except Exception:
                    beam_size = int(beam_size)

            # threads tuning: set OMP_NUM_THREADS if provided
            if threads is None:
                threads = os.getenv('FW_THREADS')
            if threads:
                try:
                    import os as _os
                    _os.environ['OMP_NUM_THREADS'] = str(int(threads))
                except Exception:
                    pass
            else:
                # if not explicitly set and client asked fast mode, try to use more CPU threads
                if fast and not threads:
                    try:
                        import os as _os
                        _os.environ['OMP_NUM_THREADS'] = str(max(1, (os.cpu_count() or 2) - 1))
                        threads = _os.environ['OMP_NUM_THREADS']
                    except Exception:
                        pass

            segments, info = fw_model.transcribe(tmp_out_path, beam_size=int(beam_size))
            # segments may be an iterator/generator of dicts OR Segment objects (faster-whisper)
            text_parts = []
            debug_segments = []
            segments_list = None
            if segments is not None:
                # consume generator to list so we can inspect and debug if needed
                try:
                    segments_list = list(segments)
                except Exception:
                    # fallback: iterate safely
                    segments_list = []
                    for s in segments:
                        segments_list.append(s)

                for i, s in enumerate(segments_list):
                    # prefer dict-like access, fall back to attribute access
                    if isinstance(s, dict):
                        t = s.get('text', '')
                        start = s.get('start', None)
                        end = s.get('end', None)
                    else:
                        t = getattr(s, 'text', None)
                        start = getattr(s, 'start', None)
                        end = getattr(s, 'end', None)
                        if t is None:
                            try:
                                t = s['text']
                            except Exception:
                                try:
                                    t = str(s)
                                except Exception:
                                    t = ''
                    if t:
                        text_parts.append(t)

                    # collect lightweight debug info
                    debug_segments.append({
                        'index': i,
                        'type': type(s).__name__,
                        'text_len': len(t) if t else 0,
                        'text_preview': (t[:120] + ('...' if t and len(t) > 120 else '')) if t else '',
                        'start': start,
                        'end': end,
                    })
            text = ''.join(text_parts)
            # Keep original text before any conversion
            orig_text = text
            # Optional: convert simplified -> traditional if requested and opencc available
            converted = None
            if target_script:
                try:
                    if 'opencc' not in globals():
                        try:
                            import opencc as _opencc
                            globals()['opencc'] = _opencc
                        except Exception:
                            globals()['opencc'] = None
                    if globals().get('opencc'):
                        # support common flags: 'tw'|'traditional' -> use s2t (simplified to traditional)
                        tc_requested = str(target_script).lower() in ('tw', 'traditional', 't')
                        if tc_requested:
                            conv = globals()['opencc'].OpenCC('s2t')
                            converted = conv.convert(text)
                    else:
                        converted = None
                except Exception:
                    converted = None
            if converted:
                text = converted
            duration = None
            if isinstance(info, dict):
                duration = info.get('audio_duration', None)
            elif hasattr(info, 'audio_duration'):
                try:
                    duration = info.audio_duration
                except Exception:
                    duration = None
            # if no text produced, log a warning with debug segments/info
            if not text:
                logging.warning('Transcription produced empty text; segments_count=%d; info=%s', len(debug_segments) if 'debug_segments' in locals() and debug_segments is not None else 0, repr(info))

            resp = {'text': text, 'duration': duration}
            # expose used settings so clients can see latency/accuracy tradeoffs
            try:
                resp['beam_size_used'] = int(beam_size)
            except Exception:
                resp['beam_size_used'] = str(beam_size)
            try:
                resp['threads_used'] = int(os.environ.get('OMP_NUM_THREADS') or threads or 0)
            except Exception:
                resp['threads_used'] = threads
            # include original text if conversion happened or requested
            if 'orig_text' in locals():
                resp['orig_text'] = orig_text
            if target_script:
                resp['target_script'] = target_script
            # include segments count for debug convenience
            if 'debug_segments' in locals():
                resp['segments_count'] = len(debug_segments)
            # if debug requested, save converted wav to UPLOAD_DIR so frontend can download & inspect
            if debug and 'tmp_out_path' in locals():
                try:
                    import shutil as _shutil
                    debug_fname = f"debug_transcribe_{int(datetime.datetime.utcnow().timestamp())}.wav"
                    debug_save_path = os.path.join(UPLOAD_DIR, debug_fname)
                    _shutil.copyfile(tmp_out_path, debug_save_path)
                    resp['debug_wav'] = f"/uploads/{debug_fname}"
                except Exception as _err:
                    logging.exception('failed to save debug wav: %s', _err)
            if debug and 'debug_segments' in locals():
                resp['debug_segments'] = debug_segments
                # include info in debug response as well
                try:
                    resp['info'] = info if isinstance(info, dict) else (info.__dict__ if hasattr(info, '__dict__') else str(info))
                except Exception:
                    resp['info'] = str(info)

            return resp
        except Exception as e:
            logging.exception('Transcription failed')
            raise HTTPException(status_code=500, detail=f'轉錄失敗: {e}')
    finally:
        # cleanup temp files
        try:
            if 'tmp_in_path' in locals() and os.path.exists(tmp_in_path):
                os.remove(tmp_in_path)
            if 'tmp_out_path' in locals() and os.path.exists(tmp_out_path):
                os.remove(tmp_out_path)
        except Exception:
            pass

# ------------------ 工具：地名與座標 ------------------
TW_PLACES = [
    "臺北", "台北", "新北", "基隆", "桃園", "新竹", "苗栗", "臺中", "台中",
    "彰化", "南投", "雲林", "嘉義", "臺南", "台南", "高雄", "屏東",
    "宜蘭", "花蓮", "臺東", "台東", "澎湖", "金門", "連江"
]

def extract_place_simple(text: str) -> Optional[str]:
    for p in TW_PLACES:
        if p in text:
            return p
    return None

def geocode_place(place: str) -> Optional[tuple]:
    try:
        url = "https://nominatim.openstreetmap.org/search"
        headers = {"User-Agent": "life-map-app/1.0", "Accept-Language": "zh-TW"}

        # 快速本地映射：對於高度模糊或常誤判的地名，直接回傳已知座標（避免被國際地名混淆）
        LOCAL_OVERRIDES = {
            "台東": (22.7583, 121.1441),
            "臺東": (22.7583, 121.1441),
            # 可視需求擴充，例如 "澎湖": (...), "金門": (...)
        }
        normalized = (place or "").strip()
        if normalized in LOCAL_OVERRIDES:
            return LOCAL_OVERRIDES[normalized]

        # 台灣的 bounding box（left, top, right, bottom）：用來限制結果只在台灣範圍內
        # 左經 ~119.5、上緯 ~25.5、右經 ~122.2、下緯 ~21.7
        taiwan_viewbox = "119.5,25.5,122.2,21.7"

        # 如果 place 看起來是台灣行政區或常見地名，優先在台灣範圍內搜尋。
        # 檢查是否包含台灣常見縣市關鍵字
        is_tw_hint = any(p in normalized for p in TW_PLACES)

        # 若是台灣疑似地名，先嘗試帶 viewbox+bounded 限制
        if is_tw_hint:
            params = {
                "q": f"{normalized}, Taiwan",
                "format": "json",
                "limit": 1,
                "viewbox": taiwan_viewbox,
                "bounded": 1,
                "addressdetails": 1,
            }
            r = requests.get(url, params=params, headers=headers, timeout=10)
            arr = r.json()
            if arr:
                return float(arr[0]["lat"]), float(arr[0]["lon"])

        # 一般情況下，先嘗試 countrycodes=tw（仍會偏向台灣）
        params = {"q": normalized, "format": "json", "limit": 1, "countrycodes": "tw", "addressdetails": 1}
        r = requests.get(url, params=params, headers=headers, timeout=10)
        arr = r.json()
        if arr:
            return float(arr[0]["lat"]), float(arr[0]["lon"])

        # 若上述台灣優先查無結果，再嘗試在沒有國家限制但加入 'Taiwan' 關鍵字的搜尋
        params = {"q": f"{normalized} Taiwan", "format": "json", "limit": 1, "addressdetails": 1}
        r = requests.get(url, params=params, headers=headers, timeout=10)
        arr = r.json()
        if arr:
            return float(arr[0]["lat"]), float(arr[0]["lon"])

        # 最後回退到不含限制的全球搜尋
        params = {"q": normalized, "format": "json", "limit": 1, "addressdetails": 1}
        r = requests.get(url, params=params, headers=headers, timeout=10)
        arr = r.json()
        if arr:
            return float(arr[0]["lat"]), float(arr[0]["lon"])
    except Exception:
        pass
    return None

# ------------------ Gemini Chat ------------------
@app.post("/api/chat")
async def chat(text: str = Form(...)):
    # 如果沒有安裝 SDK 或未設定 API Key，回傳 503 並提示
    if not HAVE_GEMINI or not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=503, detail="Gemini SDK 未安裝或 GEMINI_API_KEY 未設定。請安裝 google-generative-ai 並設定環境變數。")
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(f"你是小光，一個溫暖的AI夥伴，請親切回答：{text}")
        return {"reply": response.text.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ------------------ Memory CRUD ------------------
@app.post("/api/memories")
def create_memories(item: MemoryCreate):
    session = SessionLocal()
    try:
        place = extract_place_simple(item.text)
        lat, lng = (None, None)
        if place:
            geo = geocode_place(place)
            if geo:
                lat, lng = geo

        m = Memory(text=item.text, place=place, lat=lat, lng=lng)
        session.add(m)
        session.commit()
        session.refresh(m)
        return m.__dict__
    finally:
        session.close()

@app.get("/api/memories")
def list_memories():
    session = SessionLocal()
    try:
        items = session.query(Memory).order_by(Memory.created_at.desc()).all()
        return [m.__dict__ for m in items]
    finally:
        session.close()

@app.put("/api/memories/{mid}")
def update_memories(mid: int, item: MemoryUpdate):
    session = SessionLocal()
    try:
        m = session.get(Memory, mid)
        if not m:
            raise HTTPException(404, "not found")
        if item.text:
            m.text = item.text
        if item.place:
            m.place = item.place
            geo = geocode_place(item.place)
            if geo:
                m.lat, m.lng = geo
        session.commit()
        return {"ok": True}
    finally:
        session.close()


@app.delete("/api/memories/{mid}")
def delete_memory(mid: int):
    """Delete a memory by id. Removes DB record and deletes uploaded photo file if present."""
    session = SessionLocal()
    try:
        m = session.get(Memory, mid)
        if not m:
            raise HTTPException(404, "not found")

        # 刪除實體照片檔案（若存在）
        if m.photo_url:
            try:
                # photo_url 格式預期為 '/uploads/<filename>'
                if m.photo_url.startswith("/uploads/"):
                    fname = m.photo_url.split("/uploads/")[-1]
                    fp = os.path.join(UPLOAD_DIR, fname)
                    if os.path.exists(fp):
                        os.remove(fp)
            except Exception:
                # 不阻塞刪除流程
                pass

        session.delete(m)
        session.commit()
        return {"ok": True}
    finally:
        session.close()


@app.post("/api/admin/regeocode")
def regeocode_memories(mode: Optional[str] = Form("missing"), place_filter: Optional[str] = Form(None)):
    """Re-run geocoding for memories.
    mode: 'all' | 'missing' | 'place' (default 'missing')
    place_filter: when mode=='place', only re-geocode records whose place contains this substring.
    """
    session = SessionLocal()
    changed = []
    tried = 0
    try:
        query = session.query(Memory)
        if mode == 'missing':
            items = query.filter((Memory.lat == None) | (Memory.lng == None)).all()
        elif mode == 'place' and place_filter:
            items = [m for m in query.all() if m.place and place_filter in m.place]
        else:
            items = query.all()

        for m in items:
            tried += 1
            if not m.place:
                continue
            geo = geocode_place(m.place)
            if geo:
                lat, lng = geo
                # only update if different enough
                if (m.lat is None or m.lng is None) or (abs((m.lat or 0) - lat) > 0.0001 or abs((m.lng or 0) - lng) > 0.0001):
                    m.lat, m.lng = lat, lng
                    changed.append(m.id)
        session.commit()
        return {"tried": tried, "changed_count": len(changed), "changed_ids": changed}
    finally:
        session.close()

# ------------------ 上傳圖片 ------------------
@app.post("/api/memories/photo/{mid}")
def upload_photo(mid: int, file: UploadFile = File(...)):
    session = SessionLocal()
    try:
        m = session.get(Memory, mid)
        if not m:
            raise HTTPException(404, "not found")

        raw = file.file.read()
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        img.thumbnail((1000, 1000))
        fname = f"memories_{mid}_{int(datetime.datetime.utcnow().timestamp())}.jpg"
        save_path = os.path.join(UPLOAD_DIR, fname)
        img.save(save_path, "JPEG", quality=85)

        m.photo_url = f"/uploads/{fname}"
        session.commit()
        return {"photo_url": m.photo_url}
    finally:
        session.close()
