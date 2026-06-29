import os
import sys
import traceback
from pathlib import Path

os.chdir(Path(__file__).parent)
sys.path.insert(0, str(Path.cwd()))

from fastapi.testclient import TestClient
from app.main import app

print("app title:", app.title)
print("has runtime before client:", hasattr(app.state, "runtime"))

client = TestClient(app)
print("has runtime after client:", hasattr(app.state, "runtime"))
print("runtime state:", getattr(app.state, "runtime", None))

for path in ["/health", "/api/v1/health"]:
    try:
        response = client.get(path)
        print("path", path, "status", response.status_code)
        print(response.text)
    except Exception:
        print("path", path, "raised exception")
        traceback.print_exc()
