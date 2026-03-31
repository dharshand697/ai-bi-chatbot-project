"""
InsightAI — Backend Startup Script
Run this instead of uvicorn directly:
    python start_server.py
"""
import os
import sys
import signal

# Block keyboard interrupt from killing the process immediately
def handle_signal(sig, frame):
    print("\n[Server] Received stop signal. Shutting down gracefully...")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_signal)
if hasattr(signal, 'SIGTERM'):
    signal.signal(signal.SIGTERM, handle_signal)

# Set working directory to project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)

print("=" * 50)
print("  InsightAI Backend Server")
print("=" * 50)
print(f"  Project dir : {BASE_DIR}")
print(f"  URL         : http://127.0.0.1:8000")
print(f"  Health check: http://127.0.0.1:8000/health")
print("  Press Ctrl+C once to stop")
print("=" * 50)

import uvicorn

uvicorn.run(
    "api.main:app",
    host="127.0.0.1",
    port=8000,
    reload=False,       # reload=False prevents the subprocess that was getting killed
    log_level="info",
    access_log=True,
)
