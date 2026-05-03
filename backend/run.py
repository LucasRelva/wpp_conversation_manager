#!/usr/bin/env python
"""
Run the FastAPI server.

Usage:
    python run.py
"""
import uvicorn
import os

if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload_enabled = os.getenv("API_RELOAD", "false").lower() == "true"

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload_enabled,
        log_level="info"
    )
