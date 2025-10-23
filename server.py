import os
import importlib.util
import sys
import logging
import importlib
from fastapi import FastAPI
from typing import Callable

logger = logging.getLogger("root_server")
logger.setLevel(logging.INFO)

# placeholder app（若真實 app 無法匯入，server 仍會啟動並回傳簡單訊息）
_placeholder = FastAPI(title="rememory-placeholder")
@_placeholder.get("/api/health")
async def _health():
    return {"status": "placeholder", "message": "Admin app not loaded yet"}

# holder to allow swapping the inner app at runtime
_holder = {"app": _placeholder}

class AppProxy:
    def __init__(self, holder: dict):
        self._holder = holder

    async def __call__(self, scope, receive, send):
        # forward ASGI call to current inner app
        app = self._holder.get("app")
        return await app(scope, receive, send)

# ASGI app variable that deployment checks will find
app = AppProxy(_holder)

# 嘗試匯入 adminserver.server.app 並取代 placeholder（匯入失敗不會拋出例外）
try:
    mod = importlib.import_module("adminserver.server")
    admin_app = getattr(mod, "app", None)
    if admin_app is not None:
        _holder["app"] = admin_app
        logger.info("Loaded adminserver.server.app and replaced placeholder.")
    else:
        logger.warning("adminserver.server imported but no 'app' attribute found.")
except Exception as e:
    logger.exception(f"Could not import adminserver.server: {e}")
