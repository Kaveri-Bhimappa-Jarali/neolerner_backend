import os
import sys
import traceback

current_file_dir = os.path.dirname(os.path.abspath(__file__))
cwd = os.getcwd()

search_dirs = [
    current_file_dir,
    os.path.dirname(current_file_dir),
    cwd,
    os.path.dirname(cwd)
]

root_dir = None
for d in search_dirs:
    if os.path.isdir(os.path.join(d, "backend")):
        root_dir = d
        break

if not root_dir:
    root_dir = current_file_dir

backend_dir = os.path.join(root_dir, "backend")

for path in [root_dir, backend_dir]:
    if os.path.exists(path):
        if path in sys.path:
            sys.path.remove(path)
        sys.path.insert(0, path)

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
