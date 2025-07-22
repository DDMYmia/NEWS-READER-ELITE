# NEWS-READER-ELITE

A unified web-based news collection system integrating NewsAPI.ai, TheNewsAPI, NewsData.io, Tiingo, and RSS feeds. Features include real-time dashboard, PostgreSQL storage, deduplication, source filtering, and automated/manual collection. Built with Litestar (Python backend) and React + shadcn/ui (frontend). All configuration, error handling, and advanced usage are documented in code comments and source files.

## Features
- Modern web dashboard (React + shadcn/ui)
- Real-time news collection and statistics
- Multi-API integration: NewsAPI.ai, TheNewsAPI, NewsData.io, Tiingo
- RSS 2.0 & Atom support
- Source filtering and deduplication
- PostgreSQL persistent storage
- Manual and scheduled (auto) collection
- Live log streaming and interactive console
- Unified output format for all sources

## Quick Start
```bash
# 1. Install backend dependencies
pip install -r requirements.txt

# 2. Start backend API server
python3 start_app.py

# 3. In another terminal, start frontend
cd frontend && npm install && npm run dev

# 4. Access the app
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
```

## Project Structure
```
NEWS-READER-ELITE/
├── app/                 # Backend (Litestar)
│   └── main.py          # API entry point
├── frontend/            # Frontend (React)
│   └── src/app/         # Main dashboard
├── news_api_settings.py # API collectors
├── news_api_collector.py# API collection logic
├── news_rss_collector.py# RSS collection logic
├── news_db_utils.py     # DB utilities
├── start_app.py         # Backend launcher
├── requirements.txt     # Python deps
├── README.md            # Documentation
├── sources/             # Source configs
├── outputs/             # News output files
└── logs/                # Log files
``` 