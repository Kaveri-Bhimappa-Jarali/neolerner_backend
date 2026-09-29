import os
import sys

# Ensure backend directory is at sys.path[0] and root directory is at sys.path[1]
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(root_dir, "backend")

if backend_dir in sys.path:
    sys.path.remove(backend_dir)
sys.path.insert(0, backend_dir)

if root_dir in sys.path:
    sys.path.remove(root_dir)
sys.path.insert(1, root_dir)

from backend.main import app

app = app
