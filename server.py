import os
import importlib.util
import sys

# 嘗試由 adminserver/server.py 動態載入模組，並導出變數 app 給啟動器使用
admin_server_path = os.path.join(os.path.dirname(__file__), "adminserver", "server.py")

if not os.path.exists(admin_server_path):
    raise FileNotFoundError(f"Expected admin server file not found: {admin_server_path}")

spec = importlib.util.spec_from_file_location("adminserver_server", admin_server_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# 將 app 暴露在此模組頂層，讓 uvicorn 或其他工具能找到
try:
    app = getattr(module, "app")
except AttributeError:
    raise RuntimeError("The adminserver.server module does not define 'app'")

if __name__ == "__main__":
    # 可以直接使用 `python server.py` 啟動服務（等同 uvicorn server:app）
    import uvicorn
    print("啟動 FastAPI (app) - 監聽 0.0.0.0:8020，開啟後在另一個終端執行 curl http://127.0.0.1:8020/api/health 進行檢查")
    uvicorn.run(app, host="0.0.0.0", port=8020, reload=True)
