import os
import sys

# Ensure backend and root directories are in sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.exists(backend_dir) and backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

try:
    from main import app
except ImportError:
    try:
        from backend.main import app
    except ImportError:
        import main
        app = main.app

app = app
