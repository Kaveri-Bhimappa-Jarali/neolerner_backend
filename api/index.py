import os
import sys
import pg8000  # Explicit entrypoint import for Vercel dependency bundling

# Ensure root directory is in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.exists(root_dir) and root_dir not in sys.path:
    sys.path.insert(0, root_dir)

try:
    from main import app
except ImportError:
    try:
        from backend.main import app
    except ImportError:
        import main
        app = main.app

handler = app

__all__ = ["app", "handler"]
