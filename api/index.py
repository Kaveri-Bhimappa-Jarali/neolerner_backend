import os
import sys
import traceback

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
backend_dir = os.path.join(root_dir, "backend")

for p in [root_dir, backend_dir, current_dir]:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

app = None

try:
    from backend.main import app as _backend_app
    app = _backend_app
except Exception as exc1:
    try:
        from main import app as _main_app
        app = _main_app
    except Exception as exc2:
        init_error = f"Import Error 1:\n{traceback.format_exc()}\n\nImport Error 2:\n{exc2}"
        sys.stderr.write(f"[CRITICAL VERCEL INIT ERROR]\n{init_error}\n")
        from fastapi import FastAPI, Response
        app = FastAPI(title="Vercel Diagnostic Fallback")
        
        @app.get("/api/debug-init")
        def debug_init():
            return Response(content=f"Initialization Error:\n\n{init_error}", media_type="text/plain", status_code=500)

handler = app
__all__ = ["app", "handler"]

