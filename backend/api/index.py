import os
import sys

# Ensure parent directory is in sys.path so main, models, database, etc. can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from main import app
except Exception as e:
    import traceback
    print(f"[FATAL VERCEL BOOT ERROR] Failed to import main application: {e}")
    traceback.print_exc()
    raise e

__all__ = ["app"]
