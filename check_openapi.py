#!/usr/bin/env python
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from api.main import app

# Get the OpenAPI schema which includes all routes
schema = app.openapi()
if schema:
    print("\n" + "=" * 70)
    print("ROUTES FROM OPENAPI SCHEMA")
    print("=" * 70)
    paths = schema.get("paths", {})
    for path in sorted(paths.keys()):
        methods_dict = paths[path]
        methods = [m.upper() for m in methods_dict.keys() if m not in ["parameters"]]
        methods_str = ",".join(sorted(methods))
        print(f"{methods_str:20s} {path}")
    print("=" * 70)
