import sys
import os
import traceback

root_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(root_dir, "backend")

for p in [root_dir, backend_dir]:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

app = None

try:
    from backend.main import app as _app
    app = _app
except Exception as exc:
    init_error = traceback.format_exc()
    sys.stderr.write(f"[CRITICAL VERCEL INIT ERROR]\n{init_error}\n")
    from fastapi import FastAPI, Response
    app = FastAPI(title="Vercel Diagnostic Fallback")
    
    @app.get("/api/debug-init")
    def debug_init():
        return Response(content=f"Initialization Error:\n\n{init_error}", media_type="text/plain", status_code=500)

handler = app
__all__ = ["app", "handler"]

