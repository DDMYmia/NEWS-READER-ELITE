from litestar import Litestar, get, post
from litestar.config.cors import CORSConfig
from litestar.response import Response
from litestar.status_codes import HTTP_200_OK
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import existing news collection modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from news_api_collector import main as api_collector_main
from news_rss_collector import run as rss_collector_run
from news_db_utils import get_db_connection

# CORS configuration for frontend
cors_config = CORSConfig(
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

@get("/")
async def index() -> Response:
    """API documentation page"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>News Reader Elite - API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
            .method { color: #007cba; font-weight: bold; }
            .url { color: #333; font-family: monospace; }
        </style>
    </head>
    <body>
        <h1>News Reader Elite - API</h1>
        <p>Welcome to the News Reader Elite API. Use the following endpoints:</p>
        
        <div class="endpoint">
            <span class="method">GET</span> <span class="url">/api/health</span> - Health check
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <span class="url">/api/news?limit=50&source=reuters</span> - Get news articles
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <span class="url">/api/stats</span> - Get collection statistics
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <span class="url">/api/sources</span> - Get configured sources
        </div>
        
        <div class="endpoint">
            <span class="method">POST</span> <span class="url">/api/collect/api</span> - Trigger API collection
        </div>
        
        <div class="endpoint">
            <span class="method">POST</span> <span class="url">/api/collect/rss</span> - Trigger RSS collection
        </div>
        
        <p><strong>Frontend:</strong> <a href="http://localhost:3000" target="_blank">http://localhost:3000</a></p>
        <p><strong>API Docs:</strong> <a href="/docs" target="_blank">/docs</a></p>
    </body>
    </html>
    """
    return Response(html_content, media_type="text/html")

@get("/api/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@get("/api/news")
async def get_news(limit: int = 50, source: Optional[str] = None) -> Dict[str, Any]:
    """Get news articles from database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM articles ORDER BY published_at DESC"
        params = []
        
        if source:
            query += " WHERE source_name ILIKE %s"
            params.append(f"%{source}%")
        
        query += f" LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        articles = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "count": len(articles),
            "articles": articles
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "count": 0,
            "articles": []
        }

@get("/api/stats")
async def get_stats() -> Dict[str, Any]:
    """Get collection statistics"""
    try:
        # Read JSON files for stats
        stats = {}
        
        json_files = [
            "outputs/01_rss_news.json",
            "outputs/02_newsapi_ai.json", 
            "outputs/03_thenewsapi.json",
            "outputs/04_newsdata.json",
            "outputs/05_tiingo.json"
        ]
        
        for file_path in json_files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    source_name = os.path.basename(file_path).replace('.json', '')
                    
                    # Handle different JSON formats
                    if isinstance(data, list):
                        stats[source_name] = len(data)
                    elif isinstance(data, dict) and 'articles' in data:
                        stats[source_name] = len(data['articles'])
                    else:
                        stats[source_name] = 0
        
        # Database stats
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM articles")
            db_count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
        except:
            db_count = 0
        
        return {
            "success": True,
            "database_count": db_count,
            "source_stats": stats,
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@post("/api/collect/api")
async def collect_api_news() -> Dict[str, Any]:
    """Trigger API news collection"""
    try:
        # Run API collector in manual mode
        result = api_collector_main()
        return {
            "success": True,
            "message": "API collection completed",
            "result": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@post("/api/collect/rss")
async def collect_rss_news() -> Dict[str, Any]:
    """Trigger RSS news collection"""
    try:
        # Run RSS collector in manual mode
        result = rss_collector_run()
        return {
            "success": True,
            "message": "RSS collection completed",
            "result": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@get("/api/sources")
async def get_sources() -> Dict[str, Any]:
    """Get configured news sources"""
    try:
        sources = {}
        
        # API sources
        if os.path.exists("sources/01_api_sources.txt"):
            with open("sources/01_api_sources.txt", "r", encoding="utf-8") as f:
                api_sources = [line.strip() for line in f if line.strip()]
                sources["api"] = api_sources
        
        # RSS sources
        if os.path.exists("sources/02_rss_sources.json"):
            with open("sources/02_rss_sources.json", "r", encoding="utf-8") as f:
                rss_sources = json.load(f)
                sources["rss"] = rss_sources
        
        return {
            "success": True,
            "sources": sources
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Create Litestar app
app = Litestar(
    route_handlers=[
        index,
        health_check,
        get_news,
        get_stats,
        collect_api_news,
        collect_rss_news,
        get_sources,
    ],
    cors_config=cors_config,
    debug=True
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 