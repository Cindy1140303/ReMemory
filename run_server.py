from dotenv import load_dotenv
import os

# 讀取專案根的 .env，將 GEMINI_API_KEY 等載入環境
load_dotenv()

import uvicorn

if __name__ == '__main__':
    # 將工作目錄設為該檔所在目錄
    uvicorn.run('server:app', host='127.0.0.1', port=8010, reload=True)
