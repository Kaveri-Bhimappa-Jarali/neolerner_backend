import os
import sys

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

from backend.main import app

__all__ = ["app"]
