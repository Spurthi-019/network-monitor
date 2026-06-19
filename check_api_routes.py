#!/usr/bin/env python
# Quick test to verify all API endpoints are registered

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from api.main import app
from logger_setup import setup_logging

setup_logging()

print("\n" + "=" * 60)
print("  FASTAPI ROUTES REGISTERED")
print("=" * 60)

# List all routes
for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        methods = ",".join(sorted(route.methods or ['GET']))
        print(f"  {methods:10s} {route.path}")

print("\n" + "=" * 60)
print("  API READY")
print("=" * 60)
print("\nTo start the server, run:")
print("  python api/main.py")
print("\nThen visit:")
print("  http://localhost:8000         - Health check")
print("  http://localhost:8000/docs    - Interactive API docs")
print("  http://localhost:8000/redoc   - ReDoc docs")
print("\n" + "=" * 60)
