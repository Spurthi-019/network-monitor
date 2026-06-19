#!/usr/bin/env python
# Verify all routes are registered

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from api.main import app

print("\n" + "=" * 70)
print("ALL REGISTERED ROUTES")
print("=" * 70)

for route in app.routes:
    if hasattr(route, 'path'):
        if hasattr(route, 'methods'):
            methods = ",".join(sorted(route.methods - {"OPTIONS"}))
            print(f"{methods:15s} {route.path}")
        else:
            print(f"{'GET':15s} {route.path}")

print("=" * 70)
