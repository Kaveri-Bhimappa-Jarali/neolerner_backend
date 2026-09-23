import os
import sys

# Ensure root and backend directories are in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(root_dir, "backend")

for p in (root_dir, backend_dir):
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

from main import app

__all__ = ["app"]
