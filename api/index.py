import os
import sys
import traceback

# Ensure parent directory (backend/) is at the top of sys.path so main, models, database, etc. can be imported
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

try:
    from main import app
except Exception as e:
    print(f"[VERCEL IMPORT ERROR] Failed to import main: {e}")
    traceback.print_exc()

    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(title="NeoLearner Fallback API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
    def fallback(path: str):
        return {
            "status": "error",
            "service": "NeoLearner Backend API (Import Error Fallback)",
            "error": str(e),
            "requested_path": path,
            "traceback": traceback.format_exc()
        }

__all__ = ["app"]
