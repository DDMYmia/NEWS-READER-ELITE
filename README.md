# NEWS-READER-ELITE

A comprehensive news collection system with web interface that combines multiple API sources and RSS feeds for comprehensive news gathering.

## 🎉 Status: Fully Functional Web Application

✅ **Backend API**: Litestar server running on http://localhost:8000  
✅ **Frontend**: React + shadcn/ui dashboard on http://localhost:3000  
✅ **Database**: PostgreSQL with 106 articles  
✅ **Sources**: 44 API sources + 40 RSS feeds  
✅ **Collection**: Automated API and RSS collection  
✅ **Real-time**: Live statistics and news display  

## Features

### Web Application
- **Modern UI**: React + shadcn/ui dashboard interface
- **Real-time Updates**: Live news collection and statistics
- **Interactive Controls**: Manual collection triggers and status monitoring
- **Responsive Design**: Mobile-friendly interface

### API News Collectors
- **Multi-API**: NewsAPI.ai, TheNewsAPI, NewsData.io, Tiingo
- **Source Filtering**: 33 configured news sources across 6 categories
- **Deduplication**: Pre-save deduplication with duplicate statistics
- **Auto Mode**: Scheduled collection with configurable intervals (3-minute default)
- **Error Handling**: Comprehensive API error detection and reporting
- **Unified Output Format**: Consistent output format across all collectors

### RSS News Reader
- **RSS Support**: RSS 2.0 and Atom formats
- **Automatic Checking**: RSS feed status and latest update time
- **Retry Mechanism**: Failure retry mechanism (up to 3 attempts)
- **Smart Deduplication**: Based on title and URL
- **Auto Mode**: Scheduled collection with configurable intervals (3-minute default)
- **Unified Output Format**: Consistent output format with API collectors

## Quick Start

### Web Application
```bash
# Start the backend API server
python3 start_app.py

# In another terminal, start the frontend
cd frontend && npm run dev

# Access the application
# Frontend: http://localhost:3000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### System Test
```bash
# Run comprehensive system test
python3 test_system.py
```

### API News Collection (CLI)
```bash
# Manual collection
python3 news_api_collector.py

# Auto collection with 3-minute intervals
python3 news_api_collector.py --auto --interval 3

# Show statistics
python3 news_api_collector.py --stats

# Check configured sources
python3 -c "from news_api_settings import load_sources_from_file; print(load_sources_from_file())"
```

### RSS News Reading (CLI)
```bash
# Manual RSS collection
python3 news_rss_collector.py

# Auto RSS collection with 3-minute intervals
python3 news_rss_collector.py --auto --interval 3
```

## Web API Endpoints

### News Management
- `GET /api/news` - Get news articles (with optional limit and source filtering)
- `GET /api/stats` - Get collection statistics
- `GET /api/sources` - Get configured news sources

### Collection Control
- `POST /api/collect/api` - Trigger API news collection
- `POST /api/collect/rss` - Trigger RSS news collection

### System
- `GET /api/health` - Health check endpoint
- `GET /` - Main dashboard page

## Output Format

### API Collectors
```
NewsAPI.ai: 10 news → Dup 2 → DB + 8 JSON + 8
TheNewsAPI: 3 news → Dup 1 → DB + 2 JSON + 2
NewsData.io: 10 news → Dup 0 → DB + 10 JSON + 10
Tiingo: 10 news → Dup 1 → DB + 9 JSON + 9
```

### RSS Reader
```
✓ Source Name (domain) Latest Time ✓ Fetch Count
⚠️ Source Name (domain) Latest Time ✓ Fetch Count  # Not updated for over 10 days
✗ Source Name - Error Message  # Fetch failed

RSS: 1704 news → Dup 1686 → JSON + 2682
```

## Project Structure

```
NEWS-READER-ELITE/
├── app/                           # Web application
│   ├── main.py                   # Litestar application entry point
│   ├── api/                      # API route handlers
│   ├── models/                   # Data models
│   ├── services/                 # Business logic
│   ├── static/                   # Static files
│   └── templates/                # Jinja2 templates
├── frontend/                     # React frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── dashboard/        # Dashboard page
│   │   │   └── page.tsx          # Home page
│   │   └── components/           # React components
│   └── out/                      # Built static files
├── news_api_settings.py          # API collectors (NewsAPI.ai, TheNewsAPI, etc.)
├── news_api_collector.py         # Main API collection program
├── news_db_utils.py              # Database utilities
├── news_rss_collector.py         # RSS news reader
├── start_app.py                  # Web application launcher
├── requirements.txt              # Python dependencies
├── README.md                     # Project documentation
├── sources/                      # Source configurations
│   ├── 01_api_sources.txt        # API source configuration (33 sources)
│   └── 02_rss_sources.json       # RSS source configuration (40+ sources)
├── outputs/                      # News output files
│   ├── 01_rss_news.json          # RSS news data
│   ├── 02_newsapi_ai.json        # NewsAPI.ai articles
│   ├── 03_thenewsapi.json        # TheNewsAPI articles
│   ├── 04_newsdata.json          # NewsData.io articles
│   └── 05_tiingo.json            # Tiingo articles
└── logs/                         # Log files
    ├── 01_api_collector.log      # API collection logs
    └── 02_rss_collector.log      # RSS collection logs
```

## API Source Categories

- **Major News Media**: 13 sources (reuters.com, bbc.com, cnn.com, etc.)
- **Business & Financial Media**: 5 sources (foxbusiness.com, yahoo.com, etc.)
- **Technology Media**: 6 sources (techcrunch.com, theverge.com, etc.)
- **Political News Media**: 3 sources (washingtonpost.com, theguardian.com, etc.)
- **Science News Media**: 5 sources (nature.com, scientificamerican.com, etc.)
- **Regional News Portals**: 1 source (nzcity.co.nz)

## RSS Source Categories

- **General News**: FT Chinese, Yahoo News
- **World News**: NYT World, Guardian World, Al Jazeera, BBC World, NHK News
- **Technology**: WIRED, Engadget, The Verge, TechCrunch, Ars Technica, 36Kr, SSPAI
- **Business & Finance**: The Economist, Financial Times, Forbes, Business Insider, CNBC, Yahoo Finance
- **Politics**: Politico, RealClearPolitics, The Hill, NBC Politics, BBC Politics
- **Science**: New Scientist, Phys.org, Space.com

## Setup

### 1. Install Dependencies
```bash
# Python dependencies
pip install -r requirements.txt

# Frontend dependencies (if developing)
cd frontend
npm install
```

### 2. Configure Environment (`.env`)
```
NEWSAPI_AI_API_KEY=your_key
THENEWSAPI_API_KEY=your_key
NEWSDATA_API_KEY=your_key
TIINGO_API_KEY=your_key
POSTGRES_HOST=localhost
POSTGRES_DB=news_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
```

### 3. Database Setup
```bash
createdb news_db
```

### 4. Build Frontend (for production)
```bash
cd frontend
npm run build
```

## Development

### Backend Development
```bash
# Start with auto-reload
python3 start_app.py

# Or use uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm run dev
```

## API Design

### Collectors
- **NewsAPIAICollector**: eng, deu, spa, max 10 articles, full content
- **TheNewsAPI**: en, max 3 articles, full content scraping
- **NewsDataCollector**: en, de, es, max 10 articles, query filtering
- **TiingoCollector**: en, max 10 articles, source/tag filtering

### Source Filtering
- **NewsAPI.ai**: `source_uri=['reuters.com', 'bbc.com']`
- **TheNewsAPI**: `domains=['bbc.com', 'techcrunch.com']`
- **NewsData.io**: `all_sources=['reuters.com', 'bbc.com', ...]` (client-side filtering)
- **Tiingo**: `sources=['reuters.com', 'bbc.com']`, `tags=['technology']`

### Deduplication
- Title normalization (remove special chars, lowercase)
- Cross-source checking (JSON files + database)
- URL uniqueness constraint
- Title exact matching

## Database Schema

```sql
CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
    title TEXT, description TEXT, url TEXT UNIQUE,
    image_url TEXT, published_at TIMESTAMP,
    source_name TEXT, source_url TEXT, language TEXT,
    full_content TEXT, authors TEXT[],
    tickers TEXT[], tags TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Error Handling

- **Quota**: "API quota exceeded"
- **Auth**: "Invalid API key (401 Unauthorized)"
- **Rate Limits**: "Rate limit exceeded (429 Too Many Requests)"
- **Network**: "Network error: [details]"

## Dependencies

### Backend
- `litestar[standard]`, `psycopg2`, `requests`, `beautifulsoup4`, `eventregistry`, `python-dotenv`
- `jinja2`, `aiofiles` (for web application)

### Frontend
- `next.js`, `react`, `typescript`, `tailwindcss`
- `shadcn/ui` components

## Notes

- Ensure network connection is stable
- Some RSS sources may have access restrictions
- The program automatically handles SSL certificate issues
- Regularly check the validity of RSS sources
- API quotas may limit collection frequency
- Web application requires frontend to be built (`npm run build`) for production 