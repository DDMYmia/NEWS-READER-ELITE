# News Reader Elite

A comprehensive news aggregation system that collects and displays news from multiple sources including APIs and RSS feeds. Built with Python (Litestar) backend and React/Next.js frontend.

## Features

- **Multi-Source Collection**: Integrates with 5 major news APIs and RSS feeds
- **Real-time Processing**: Immediate data processing and storage
- **Dual Database Storage**: PostgreSQL (primary) + MongoDB (backup)
- **Modern Web Interface**: React + Next.js dashboard
- **Advanced Deduplication**: Prevents duplicate articles
- **Flexible Collection**: Manual and automated collection modes

## Quick Start

### Prerequisites
- Python 3.13+
- Node.js 18+
- PostgreSQL database
- API keys for news services

### Setup

1. **Clone and install dependencies**
```bash
pip install -r requirements.txt
cd frontend && npm install
```

2. **Configure environment**
```bash
cp .env.sample .env
# Edit .env with your database credentials and API keys
```

3. **Start the application**
```bash
# Backend
python start_app.py

# Frontend (in another terminal)
cd frontend && npm run dev
```

- **Backend API**: http://localhost:8000
- **Frontend Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs

## Supported News Sources

- NewsAPI.ai (Event Registry)
- TheNewsAPI.com
- NewsData.io
- Tiingo (Financial News)
- AlphaVantage (Market News)
- RSS Feeds (RSS 2.0 and Atom)

## Configuration

### API Sources
Edit `sources/01_api_sources.txt` to configure API sources:
```
reuters.com
bloomberg.com
cnn.com
```

### RSS Sources
Edit `sources/02_rss_sources.json` to configure RSS feeds:
```json
[
  {
    "name": "Reuters",
    "url": "https://feeds.reuters.com/reuters/topNews"
  }
]
```

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/stats` - System statistics
- `GET /api/news` - Retrieve news articles
- `GET /api/sources` - List configured sources
- `POST /api/collect/api` - Trigger API collection
- `POST /api/collect/rss` - Trigger RSS collection

## Testing

Run the system test suite:
```bash
python test_system.py
```

## Project Structure

```
NEWS-READER-ELITE/
├── .env                     # Environment variables (API keys, DB credentials)
├── .env.sample              # Environment variables template
├── app/                     # Litestar Backend Application
│   ├── main.py              # Main Litestar app, API routes, auto collection logic
│   └── litestar_utils.py    # Utility functions for Litestar (logging, data formatting)
├── frontend/                # React/Next.js Frontend Application
│   ├── src/app/dashboard/   # Main dashboard page
│   └── ...                  # Other frontend components and config
├── news_api_settings.py     # API client configurations and BaseCollector definitions
├── news_api_collector.py    # Logic for running all integrated API collectors
├── news_rss_collector.py    # Logic for running RSS feed collector
├── news_postgres_utils.py   # PostgreSQL database utility functions
├── news_mongo_utils.py      # MongoDB database utility functions
├── start_app.py             # Script to launch the backend server
├── requirements.txt         # Python backend dependencies
├── package.json             # Frontend dependencies
├── sources/                 # Configuration files for API and RSS sources
│   ├── 01_api_sources.txt
│   └── 02_rss_sources.json
├── outputs/                 # Directory for local JSON backups of collected news (e.g., 01_rss_news.json)
├── logs/                    # Application log files
├── test_system.py           # System test script
└── README.md                # Project documentation
```