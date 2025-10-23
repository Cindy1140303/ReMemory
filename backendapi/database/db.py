from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os
import urllib.parse

# 載入 .env
load_dotenv()

# ✅ 從環境變數讀取
DB_SERVER = os.getenv("DB_SERVER", "localhost")
DB_NAME   = os.getenv("DB_NAME", "life_map")
DB_USER   = os.getenv("DB_USER", "sa")
DB_PASS   = os.getenv("DB_PASS", "YourPasswordHere")

# ✅ 編碼密碼，避免特殊字元錯誤
DB_PASS_ENCODED = urllib.parse.quote_plus(DB_PASS)

# ✅ 建立連線字串（MSSQL + ODBC）
DB_URL = f"mssql+pyodbc://{DB_USER}:{DB_PASS_ENCODED}@{DB_SERVER}/{DB_NAME}?driver=ODBC+Driver+17+for+SQL+Server"

# ✅ 初始化 SQLAlchemy
engine = create_engine(DB_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()
