import importlib
import logging
from fastapi import FastAPI

logger = logging.getLogger("root_server")
logger.setLevel(logging.INFO)

# Placeholder app
_placeholder = FastAPI(title="rememory-placeholder")

@_placeholder.get("/api/health")
async def _health():
    return {"status": "placeholder", "message": "Admin app not loaded yet"}

_holder = {"app": _placeholder}

class AppProxy:
    def __init__(self, holder: dict):
        self._holder = holder

    async def __call__(self, scope, receive, send):
        app = self._holder.get("app")
        return await app(scope, receive, send)

app = AppProxy(_holder)

try:
    mod = importlib.import_module("adminserver.server")
    admin_app = getattr(mod, "app", None)
    if admin_app is not None:
        _holder["app"] = admin_app
        logger.info("Loaded adminserver.server.app and replaced placeholder.")
    else:
        logger.warning("adminserver.server imported but no 'app' attribute found.")
except Exception as e:
    logger.warning(f"Could not import adminserver.server: {e}")
    _holder["app"] = _placeholder
