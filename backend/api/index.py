import os
import sys
import traceback

api_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(api_dir)
root_dir = os.path.dirname(backend_dir)

for path in [backend_dir, root_dir, api_dir]:
    if os.path.exists(path) and path not in sys.path:
        sys.path.insert(0, path)

app = None

try:
    from main import app as _app
    app = _app
except Exception:
    try:
        from backend.main import app as _app
        app = _app
    except Exception as exc2:
        init_error = f"Import Error:\n{traceback.format_exc()}\n\nSecondary:\n{exc2}"
        sys.stderr.write(f"[CRITICAL VERCEL INIT ERROR]\n{init_error}\n")
        from fastapi import FastAPI, Response
        app = FastAPI(title="Vercel Diagnostic Fallback")
        
        @app.get("/api/debug-init")
        def debug_init():
            return Response(content=f"Initialization Error:\n\n{init_error}", media_type="text/plain", status_code=500)

handler = app
__all__ = ["app", "handler"]

