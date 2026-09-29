import os
import sys
import traceback

# Ensure root directory and backend directory are in Python search path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
backend_dir = os.path.join(root_dir, "backend")

for p in [root_dir, backend_dir, current_dir]:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

try:
    from backend.main import app as _app
    app = _app
except Exception as exc:
    try:
        from main import app as _app
        app = _app
    except Exception as exc_inner:
        err_msg = f"Primary Import Error:\n{traceback.format_exc()}\n\nSecondary Import Error:\n{exc_inner}"
        sys.stderr.write(f"[CRITICAL VERCEL INIT ERROR]\n{err_msg}\n")
        from fastapi import FastAPI, Response
        app = FastAPI(title="Vercel Diagnostic Fallback")
        
        @app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"])
        def diagnostic_fallback(full_path: str):
            return Response(content=f"Initialization Traceback:\n\n{err_msg}", media_type="text/plain", status_code=200)

handler = app
__all__ = ["app", "handler"]
