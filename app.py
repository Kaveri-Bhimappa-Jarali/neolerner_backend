import os
import sys
import traceback
from fastapi import FastAPI, Response

root_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(root_dir, "backend")

for p in [root_dir, backend_dir]:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

app = FastAPI(title="NeoLearner Backend Serverless API")

@app.api_route("/", methods=["GET", "HEAD", "OPTIONS"])
@app.api_route("/health", methods=["GET", "HEAD", "OPTIONS"])
@app.api_route("/api/health", methods=["GET", "HEAD", "OPTIONS"])
def base_health():
    return {"status": "ok", "service": "NeoLearner Backend API"}

init_error = None

try:
    from backend.main import app as _backend_app
    app = _backend_app
except Exception as exc:
    init_error = traceback.format_exc()
    sys.stderr.write(f"[CRITICAL VERCEL INIT ERROR]\n{init_error}\n")

    @app.api_route("/debug", methods=["GET"])
    def get_debug_trace():
        return Response(content=f"Backend Import Error Traceback:\n\n{init_error}", media_type="text/plain")

handler = app
__all__ = ["app", "handler"]
