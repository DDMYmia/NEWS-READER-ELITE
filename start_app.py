#!/usr/bin/env python3
"""
News Reader Elite - Web Application Launcher
Starts the Litestar backend server with frontend integration.
"""

import uvicorn
import os
import sys
from pathlib import Path

# Add app directory to path
sys.path.append(str(Path(__file__).parent / "app"))

if __name__ == "__main__":
    print("🚀 Starting News Reader Elite...")
    print("📊 Backend API: http://localhost:8000")
    print("🌐 Frontend: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    print("🔧 Health Check: http://localhost:8000/api/health")
    print("\nPress Ctrl+C to stop the server")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 