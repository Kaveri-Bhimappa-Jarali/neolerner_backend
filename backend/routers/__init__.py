import os
import sys

_router_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_router_dir)
_root_dir = os.path.dirname(_backend_dir)

for _p in [_root_dir, _backend_dir, _router_dir]:
    if os.path.exists(_p) and _p not in sys.path:
        sys.path.insert(0, _p)
