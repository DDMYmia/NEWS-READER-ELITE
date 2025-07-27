#!/usr/bin/env python3
"""
News Reader Elite - Web Application Launcher
Starts the Litestar backend server with frontend integration.
"""

import uvicorn
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Define application constants
APP_HOST = "0.0.0.0"
APP_PORT = 8000

# Load environment variables from .env file
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# Debugging: Print API keys to verify loading - 已修复，删除调试输出
# print(f"DEBUG: NEWSAPI_AI_API_KEY: {os.environ.get("NEWSAPI_AI_API_KEY")}")
# print(f"DEBUG: THENEWSAPI_API_KEY: {os.environ.get("THENEWSAPI_API_KEY")}")
# print(f"DEBUG: NEWSDATA_API_KEY: {os.environ.get("NEWSDATA_API_KEY")}")
# print(f"DEBUG: TIINGO_API_KEY: {os.environ.get("TIINGO_API_KEY")}")

if __name__ == "__main__":
    print("🚀 Starting News Reader Elite...")
    print(f"📊 Backend API: http://localhost:{APP_PORT}")
    print(f"🌐 Frontend: http://localhost:{APP_PORT}") # Frontend might be on a different port (e.g. 3000), update as needed
    print(f"📖 API Docs: http://localhost:{APP_PORT}/docs")
    print(f"🔧 Health Check: http://localhost:{APP_PORT}/api/health")
    print("\nPress Ctrl+C to stop the server")
    
    uvicorn.run(
        "app.main:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=False,
        log_level="info"
    ) 