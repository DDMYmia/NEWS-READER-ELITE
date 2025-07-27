# NEWS-READER-ELITE

A unified web-based news collection system designed for efficient data gathering, storage, and real-time display. It integrates multiple external news APIs (NewsAPI.ai, TheNewsAPI, NewsData.io, Tiingo, AlphaVantage) and RSS feeds. The system features real-time data processing, robust storage with PostgreSQL (primary) and MongoDB (backup), advanced deduplication, source filtering, and both automated and manual collection capabilities. The backend is built with Litestar (Python), and the frontend with React + Next.js + shadcn/ui.

## Features

-   **Modern Web Dashboard**: Intuitive user interface built with React, Next.js, and shadcn/ui.
-   **Real-time News Feed**: Immediate display of newly collected articles via WebSocket push.
-   **Multi-API Integration**: Collects news from:
    -   NewsAPI.ai (Event Registry)
    -   TheNewsAPI.com
    -   NewsData.io
    -   Tiingo (Financial News)
    -   AlphaVantage (Market News & Sentiment)
-   **RSS Feed Support**: Compatible with RSS 2.0 and Atom feeds.
-   **Dual Database Storage**:
    -   **PostgreSQL**: Primary persistent storage for news articles.
    -   **MongoDB**: Parallel backup storage for redundancy and flexible data access.
-   **Advanced Deduplication**: Prevents duplicate articles based on URL uniqueness across all sources and databases.
-   **Source Filtering**: Configurable to fetch news from specific sources.
-   **Flexible Collection Modes**: Supports both manual on-demand collection and automated scheduled collection.
-   **Live Log Streaming**: Real-time operational logs streamed to the frontend console for monitoring.
-   **Unified Article Format**: All collected articles are transformed into a consistent schema for easy processing and display.

## Technical Stack

-   **Backend**: Python 3.13+
    -   **Framework**: [Litestar](https://litestar.dev/) (ASGI framework for building perform performant APIs)
    -   **ASGI Server**: [Uvicorn](https://www.uvicorn.org/)
    -   **Database ORM/Driver**: [psycopg](https://www.psycopg.org/psycopg3/) (PostgreSQL), [PyMongo](https://pymongo.readthedocs.io/) (MongoDB)
    -   **Environment Management**: [python-dotenv](https://pypi.org/project/python-dotenv/)
    -   **Date Parsing**: [python-dateutil](https://dateutil.readthedocs.io/en/stable/)
    -   **HTTP Requests**: [requests](https://requests.readthedocs.io/en/latest/)
    -   **XML Parsing**: `xml.etree.ElementTree`
-   **Frontend**: JavaScript/TypeScript
    -   **Framework**: [Next.js](https://nextjs.org/) (React Framework)
    -   **UI Components**: [shadcn/ui](https://ui.shadcn.com/)
    -   **Package Manager**: [npm](https://www.npmjs.com/)

## Getting Started

To get started with the NEWS-READER-ELITE, follow these simple steps:

1.  **Environment Setup**:
    *   Create a `.env` file in the project root directory. You can use the provided `.env.sample` as a template. Fill in your actual API keys and database credentials.
    *   Ensure PostgreSQL and MongoDB databases are running and accessible with the configured credentials.

### Running the Application

Simply run the following commands in separate terminal windows:

1.  **Start Backend API Server**:
    ```bash
    python3 start_app.py
    ```
    (Access at `http://localhost:8000` for API, `http://localhost:8000/docs` for API docs, `http://localhost:8000/api/health` for health check)

2.  **Start Frontend Development Server**:
    ```bash
    cd frontend
    npm run dev
    ```
    (Access at `http://localhost:3000` for Dashboard)

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
