import os
import sys

backend_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(backend_dir)

for path in [backend_dir, root_dir]:
    if os.path.exists(path):
        if path in sys.path:
            sys.path.remove(path)
        sys.path.insert(0, path)

try:
    from backend.main import app
except ImportError:
    from main import app

handler = app
__all__ = ["app", "handler"]
