from dotenv import load_dotenv
import os
import sys

# 加入 web/src 和 backendapi 目錄到 Python 路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
web_src_path = os.path.join(project_root, 'web', 'src')
backendapi_path = os.path.join(project_root, 'backendapi')
sys.path.insert(0, web_src_path)
sys.path.insert(0, backendapi_path)

# 讀取專案根的 .env，將 GEMINI_API_KEY 等載入環境
load_dotenv(os.path.join(project_root, '.env'))

import uvicorn

if __name__ == '__main__':
    # 將工作目錄設為專案根目錄
    os.chdir(project_root)
    # 執行 web/src 目錄中的 server.py
    uvicorn.run('server:app', host='127.0.0.1', port=8010, reload=True)
