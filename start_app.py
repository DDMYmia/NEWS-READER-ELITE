#!/usr/bin/env python3
"""
News Reader Elite - Web Application Launcher

This module serves as the main entry point for the News Reader Elite backend server.
It configures logging, loads environment variables, and starts the Litestar ASGI server
with the integrated frontend.

Main Functions:
- log_print: Utility function for consistent logging output (deprecated, use logging directly)
- main: Entry point that starts the server

Dependencies:
- uvicorn: ASGI server for running the Litestar application
- python-dotenv: For loading environment variables
- logging: For application logging

Usage:
Run this script to start the backend server:
    python start_app.py

Author: Gemini AI Assistant
Last updated: 2024-07-30
"""

import uvicorn
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Define application constants
APP_HOST = "0.0.0.0"
APP_PORT = 8000

# Load environment variables from .env file
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# Configure logging centrally
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def main():
    """
    Main function to start the News Reader Elite backend server.
    """
    logging.info("🚀 Starting News Reader Elite...")
    logging.info(f"📊 Backend API: http://localhost:{APP_PORT}")
    logging.info(f"🌐 Frontend: http://localhost:3000")
    logging.info(f"📖 API Docs: http://localhost:{APP_PORT}/docs")
    logging.info(f"🔧 Health Check: http://localhost:{APP_PORT}/api/health")
    logging.info("\nPress Ctrl+C to stop the server")
    
    # Start the uvicorn server
    uvicorn.run(
        "app.main:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main() 