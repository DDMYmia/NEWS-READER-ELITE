# NEWS-COLLECTOR-ELITE

A comprehensive news collection system that combines multiple API sources and RSS feeds for comprehensive news gathering.

## Features

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

### API News Collection
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

### RSS News Reading
```bash
# Manual RSS collection
python3 news_rss_collector.py

# Auto RSS collection with 3-minute intervals
python3 news_rss_collector.py --auto --interval 3
```

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
NEWS-COLLECTOR-ELITE/
├── news_api_settings.py        # API collectors (NewsAPI.ai, TheNewsAPI, etc.)
├── news_api_collector.py       # Main API collection program
├── news_db_utils.py            # Database utilities
├── news_rss_collector.py       # RSS news reader
├── requirements.txt            # Dependencies
├── README.md                   # Project documentation
├── sources/                    # Source configurations
│   ├── 01_api_sources.txt      # API source configuration (33 sources)
│   └── 02_rss_sources.json     # RSS source configuration (40+ sources)
├── outputs/                    # News output files
│   ├── 01_rss_news.json        # RSS news data
│   ├── 02_newsapi_ai.json      # NewsAPI.ai articles
│   ├── 03_thenewsapi.json      # TheNewsAPI articles
│   ├── 04_newsdata.json        # NewsData.io articles
│   └── 05_tiingo.json          # Tiingo articles
└── logs/                       # Log files
    ├── 01_api_collector.log    # API collection logs
    └── 02_rss_collector.log    # RSS collection logs
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

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install requests python-dateutil
   ```

2. **Configure Environment** (`.env`):
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

3. **Database Setup**:
   ```bash
   createdb news_db
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

- `psycopg2`, `requests`, `beautifulsoup4`, `eventregistry`, `python-dotenv`
- `requests`, `python-dateutil` (for RSS reader)

## Notes

- Ensure network connection is stable
- Some RSS sources may have access restrictions
- The program automatically handles SSL certificate issues
- Regularly check the validity of RSS sources
- API quotas may limit collection frequency 