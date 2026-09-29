import sys
import os
import traceback

root_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(root_dir, "backend")

for p in [root_dir, backend_dir]:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

try:
    from backend.main import app as _app
    app = _app
except Exception as exc:
    err_msg = traceback.format_exc()
    sys.stderr.write(f"[CRITICAL VERCEL INIT ERROR]\n{err_msg}\n")
    from fastapi import FastAPI, Response
    app = FastAPI(title="Vercel Diagnostic Fallback")
    
    @app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"])
    def diagnostic_fallback(full_path: str):
        return Response(content=f"Initialization Traceback:\n\n{err_msg}", media_type="text/plain", status_code=200)

handler = app
__all__ = ["app", "handler"]
