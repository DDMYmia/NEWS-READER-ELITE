from litestar import Litestar, get, post, websocket
from litestar.config.cors import CORSConfig
from litestar.response import Response
from litestar.status_codes import HTTP_200_OK
from litestar.connection import WebSocket
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import threading
import asyncio
import queue
import time

# Import existing news collection modules
from news_api_collector import main as api_collector_main
from news_rss_collector import run as rss_collector_run
import news_postgres_utils # Renamed from news_db_utils
import news_mongo_utils

# Log queue and WebSocket client management
log_queue = queue.Queue()
ws_clients = set()

# Import utility functions and set the shared log_queue
from app.litestar_utils import log_push, _format_articles_for_push, set_log_queue
set_log_queue(log_queue)  # Ensure both modules use the same queue instance

from news_api_settings import (
    NEWS_FILE_NEWSAPI_AI,
    NEWS_FILE_THENEWSAPI,
    NEWS_FILE_NEWSDATA,
    NEWS_FILE_TIINGO,
    NEWS_FILE_ALPHA_VANTAGE,
    NEWS_FILE_RSS
)

# CORS configuration for frontend
cors_config = CORSConfig(
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Automatic API collection task management
auto_api_thread = None
auto_api_stop_event = threading.Event()
# Automatic RSS collection task management
auto_rss_thread = None
auto_rss_stop_event = threading.Event()
# New entry counts (articles newly saved in current session)
auto_api_new_count = 0
auto_rss_new_count = 0
# Last collection times
last_api_collection_time: Optional[datetime] = None
last_rss_collection_time: Optional[datetime] = None
# Error flags
api_error_occurred: bool = False
rss_error_occurred: bool = False

def auto_api_loop(interval=180):
    """Automatic API collection loop."""
    global auto_api_new_count, last_api_collection_time, api_error_occurred
    log_push(f"[AUTO-API] Auto API collection started, interval={interval}s")
    while not auto_api_stop_event.is_set():
        api_error_occurred = False # Reset error flag at start of loop
        try:
            log_push("[AUTO-API] Collecting all API news...")
            new_api_articles = api_collector_main()
            last_api_collection_time = datetime.now() # Update last collection time
            
            # Always log the collection results, regardless of new articles count
            log_push(f"[AUTO-API] Collected {len(new_api_articles)} new API articles.")
            
            if new_api_articles:
                auto_api_new_count += len(new_api_articles)
                log_push(f"[AUTO-API] New articles: {len(new_api_articles)}. PG: {news_postgres_utils.get_total_articles_count()}, Mongo: {news_mongo_utils.get_total_articles_count_mongo()}")
                log_push("", data_payload={
                    "type": "news_update", "api_new": auto_api_new_count, "rss_new": auto_rss_new_count,
                    "total_articles": news_postgres_utils.get_total_articles_count(),
                    "total_articles_mongo": news_mongo_utils.get_total_articles_count_mongo(),
                    "new_articles_list": _format_articles_for_push(new_api_articles[:10])
                })
            else:
                log_push("[AUTO-API] No new articles found (all duplicates or fetch errors).")
                # Still send an update to refresh frontend stats, even if no new articles
                log_push("", data_payload={
                    "type": "news_update", "api_new": auto_api_new_count, "rss_new": auto_rss_new_count,
                    "total_articles": news_postgres_utils.get_total_articles_count(),
                    "total_articles_mongo": news_mongo_utils.get_total_articles_count_mongo(),
                    "new_articles_list": []
                })
            log_push("[AUTO-API] Collection round finished.")
        except Exception as e:
            api_error_occurred = True # Set error flag
            log_push(f"[AUTO-API] Error in auto_api_loop: {e}")
        
        for _ in range(interval):
            if auto_api_stop_event.is_set(): break
            time.sleep(1)
    log_push("[AUTO-API] Auto API collection stopped.")

def auto_rss_loop(interval=180):
    """Automatic RSS collection loop."""
    global auto_rss_new_count, last_rss_collection_time, rss_error_occurred
    log_push(f"[AUTO-RSS] Auto RSS collection started, interval={interval}s")
    while not auto_rss_stop_event.is_set():
        rss_error_occurred = False # Reset error flag at start of loop
        try:
            log_push("[AUTO-RSS] Collecting RSS news...")
            new_rss_articles = rss_collector_run()
            last_rss_collection_time = datetime.now() # Update last collection time
            
            # Always log the collection results, regardless of new articles count
            log_push(f"[AUTO-RSS] Collected {len(new_rss_articles)} new RSS articles.")
            
            if new_rss_articles:
                auto_rss_new_count += len(new_rss_articles)
                log_push(f"[AUTO-RSS] New articles: {len(new_rss_articles)}. PG: {news_postgres_utils.get_total_articles_count()}, Mongo: {news_mongo_utils.get_total_articles_count_mongo()}")
                log_push("", data_payload={
                    "type": "news_update", "api_new": auto_api_new_count, "rss_new": auto_rss_new_count,
                    "total_articles": news_postgres_utils.get_total_articles_count(),
                    "total_articles_mongo": news_mongo_utils.get_total_articles_count_mongo(),
                    "new_articles_list": _format_articles_for_push(new_rss_articles[:10])
                })
            else:
                log_push("[AUTO-RSS] No new articles found (all duplicates or fetch errors).")
                # Still send an update to refresh frontend stats, even if no new articles
                log_push("", data_payload={
                    "type": "news_update", "api_new": auto_api_new_count, "rss_new": auto_rss_new_count,
                    "total_articles": news_postgres_utils.get_total_articles_count(),
                    "total_articles_mongo": news_mongo_utils.get_total_articles_count_mongo(),
                    "new_articles_list": []
                })
        except Exception as e:
            rss_error_occurred = True # Set error flag
            log_push(f"[AUTO-RSS] Error in auto_rss_loop: {e}")

        for _ in range(interval):
            if auto_rss_stop_event.is_set(): break
            time.sleep(1)
    log_push("[AUTO-RSS] Auto RSS collection stopped.")

@get("/api/news")
async def get_news_api(limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """Get news articles from the database with pagination."""
    try:
        articles = news_postgres_utils.get_news(limit=limit, offset=offset)
        return {"success": True, "count": len(articles), "articles": articles}
    except Exception as e:
        return {"success": False, "error": str(e), "count": 0, "articles": []}

@get("/api/stats")
async def get_stats() -> Dict[str, Any]:
    """Returns statistics about the collected news from databases and JSON files."""
    try:
        pg_count = news_postgres_utils.get_total_articles_count()
        mongo_count = news_mongo_utils.get_total_articles_count_mongo()
        
        file_counts = {}
        json_files = {
            "rss_file_count": NEWS_FILE_RSS,
            "newsapi_ai_file_count": NEWS_FILE_NEWSAPI_AI,
            "thenewsapi_file_count": NEWS_FILE_THENEWSAPI,
            "newsdata_file_count": NEWS_FILE_NEWSDATA,
            "tiingo_file_count": NEWS_FILE_TIINGO,
            "alpha_vantage_file_count": NEWS_FILE_ALPHA_VANTAGE,
        }
        
        for key, file_path in json_files.items():
            count = 0
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        count = len(data)
                except (json.JSONDecodeError, FileNotFoundError):
                    pass
            file_counts[key] = count
        
        # Calculate total JSON file count
        total_json_file_count = sum(file_counts.values())

        stats = {
            "success": True,
            "database_count": pg_count,
            "mongodb_backup_count": mongo_count,
            "last_updated": datetime.now().isoformat(),
            "last_api_collection_time": last_api_collection_time.isoformat() if last_api_collection_time else None,
            "last_rss_collection_time": last_rss_collection_time.isoformat() if last_rss_collection_time else None,
            "total_json_file_count": total_json_file_count, # Add total JSON file count
        }
        stats.update(file_counts)
        return stats
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@post("/api/collect/api")
async def collect_api_news() -> Dict[str, Any]:
    """Manually trigger API news collection."""
    global auto_api_new_count, api_error_occurred
    api_error_occurred = False # Reset error flag for manual collection
    try:
        new_articles = api_collector_main()
        if new_articles:
            auto_api_new_count += len(new_articles)
            log_push("", data_payload={
                "type": "news_update", "api_new": auto_api_new_count, "rss_new": auto_rss_new_count,
                "total_articles": news_postgres_utils.get_total_articles_count(),
                "total_articles_mongo": news_mongo_utils.get_total_articles_count_mongo(),
                "new_articles_list": _format_articles_for_push(new_articles[:10])
            })
        return {"success": True, "message": f"API collection completed. New articles: {len(new_articles)}"}
    except Exception as e:
        api_error_occurred = True
        return {"success": False, "error": str(e)}

@post("/api/collect/rss")
async def collect_rss_news() -> Dict[str, Any]:
    """Manually trigger RSS news collection."""
    global auto_rss_new_count, rss_error_occurred
    rss_error_occurred = False # Reset error flag for manual collection
    try:
        new_articles = rss_collector_run()
        if new_articles:
            auto_rss_new_count += len(new_articles)
            log_push("", data_payload={
                "type": "news_update", "api_new": auto_api_new_count, "rss_new": auto_rss_new_count,
                "total_articles": news_postgres_utils.get_total_articles_count(),
                "total_articles_mongo": news_mongo_utils.get_total_articles_count_mongo(),
                "new_articles_list": _format_articles_for_push(new_articles[:10])
            })
        return {"success": True, "message": f"RSS collection completed. New articles: {len(new_articles)}"}
    except Exception as e:
        rss_error_occurred = True
        return {"success": False, "error": str(e)}

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

# WebSocket log push
@websocket("/ws/logs")
async def ws_logs(socket: WebSocket) -> None:
    ws_clients.add(socket)
    try:
        await socket.accept()
        log_push("[Console] Connected to backend log stream.") # Use log_push for consistency
        while True:
            try:
                msg = log_queue.get(timeout=1)
                try:
                    # Attempt to parse as JSON, if failed, send raw message
                    # (Although now all messages from log_push should be JSON)
                    await socket.send_text(msg)
                except Exception as e:
                    print(f"WebSocket send_text error: {e}")
                    break  # Exit loop on send failure
            except queue.Empty:
                try:
                    await asyncio.sleep(0.1)
                except asyncio.CancelledError:
                    print("WebSocket sleep cancelled, closing connection.")
                    break
            except Exception as e:
                print(f"WebSocket inner loop error: {e}")
                break
    except Exception as e:
        print(f"WebSocket connection closed: {e}")
    finally:
        ws_clients.discard(socket)
        print("WebSocket client disconnected.")

# API: Start/Stop Automatic API Collection
def start_auto_api(interval=180):
    global auto_api_thread
    if auto_api_thread and auto_api_thread.is_alive():
        return False
    auto_api_stop_event.clear()
    auto_api_thread = threading.Thread(target=auto_api_loop, args=(interval,), daemon=True)
    auto_api_thread.start()
    return True

def stop_auto_api():
    auto_api_stop_event.set()
    return True

# API: Start/Stop Automatic RSS Collection
def start_auto_rss(interval=180):
    global auto_rss_thread
    if auto_rss_thread and auto_rss_thread.is_alive():
        return False
    auto_rss_stop_event.clear()
    auto_rss_thread = threading.Thread(target=auto_rss_loop, args=(interval,), daemon=True)
    auto_rss_thread.start()
    return True

def stop_auto_rss():
    auto_rss_stop_event.set()
    return True

@post("/api/auto/start")
async def api_auto_start(data: Dict[str, Any]) -> Dict[str, Any]:
    interval = int(data.get("interval", 180))
    start_api_success = start_auto_api(interval)
    start_rss_success = start_auto_rss(interval)
    
    if start_api_success or start_rss_success:
        log_push(f"[API] Auto collection (API and/or RSS) started via API, interval={interval}s")
        return {"success": True, "message": "Auto collection started."}
    else:
        return {"success": False, "message": "Auto collection already running."}

@post("/api/auto/stop")
async def api_auto_stop() -> Dict[str, Any]:
    stop_auto_api()
    stop_auto_rss()
    log_push("[API] Auto collection stopped via API.")
    return {"success": True, "message": "Auto collection stopped."}

@post("/api/auto/start_api")
async def api_auto_start_api(data: Dict[str, Any]) -> Dict[str, Any]:
    interval = int(data.get("interval", 180))
    started = start_auto_api(interval)
    if started:
        log_push(f"[API] Auto API collection started via API, interval={interval}s")
        return {"success": True, "message": "Auto API collection started."}
    else:
        return {"success": False, "message": "Auto API collection already running."}

@post("/api/auto/stop_api")
async def api_auto_stop_api() -> Dict[str, Any]:
    stop_auto_api()
    log_push("[API] Auto API collection stopped via API.")
    return {"success": True, "message": "Auto API collection stopped."}

@post("/api/auto/start_rss")
async def api_auto_start_rss(data: Dict[str, Any]) -> Dict[str, Any]:
    interval = int(data.get("interval", 180))
    started = start_auto_rss(interval)
    if started:
        log_push(f"[API] Auto RSS collection started via API, interval={interval}s")
        return {"success": True, "message": "Auto RSS collection started."}
    else:
        return {"success": False, "message": "Auto RSS collection already running."}

@post("/api/auto/stop_rss")
async def api_auto_stop_rss() -> Dict[str, Any]:
    stop_auto_rss()
    log_push("[API] Auto RSS collection stopped via API.")
    return {"success": True, "message": "Auto RSS collection stopped."}

@get("/api/auto/status")
async def api_auto_status() -> Dict[str, Any]:
    """Returns auto collection status including historical totals for API and RSS articles."""
    try:
        # Get historical totals from JSON files
        api_total = 0
        rss_total = 0
        
        # Calculate API total from all API JSON files
        api_files = {
            "newsapi_ai_file_count": NEWS_FILE_NEWSAPI_AI,
            "thenewsapi_file_count": NEWS_FILE_THENEWSAPI,
            "newsdata_file_count": NEWS_FILE_NEWSDATA,
            "tiingo_file_count": NEWS_FILE_TIINGO,
            "alpha_vantage_file_count": NEWS_FILE_ALPHA_VANTAGE,
        }
        
        for key, file_path in api_files.items():
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        api_total += len(data)
                except (json.JSONDecodeError, FileNotFoundError):
                    pass
        
        # Calculate RSS total from RSS JSON file
        if os.path.exists(NEWS_FILE_RSS):
            try:
                with open(NEWS_FILE_RSS, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, list):
                    rss_total = len(data)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        return {
            "api_running": auto_api_thread and auto_api_thread.is_alive(),
            "rss_running": auto_rss_thread and auto_rss_thread.is_alive(),
            "api_new": auto_api_new_count,  # Current session new count
            "rss_new": auto_rss_new_count,  # Current session new count
            "api_total": api_total,  # Historical total from all API sources
            "rss_total": rss_total,  # Historical total from RSS sources
            "api_error_occurred": api_error_occurred,
            "rss_error_occurred": rss_error_occurred,
        }
    except Exception as e:
        return {
            "api_running": auto_api_thread and auto_api_thread.is_alive(),
            "rss_running": auto_rss_thread and auto_rss_thread.is_alive(),
            "api_new": auto_api_new_count,
            "rss_new": auto_rss_new_count,
            "api_total": 0,
            "rss_total": 0,
            "api_error_occurred": api_error_occurred,
            "rss_error_occurred": rss_error_occurred,
            "error": str(e)
        }

@post("/api/auto/reset_new")
async def api_auto_reset_new(data: Dict[str, Any]) -> Dict[str, Any]:
    global auto_api_new_count, auto_rss_new_count
    if data.get("type") == "api":
        auto_api_new_count = 0
    elif data.get("type") == "rss":
        auto_rss_new_count = 0
    return {"success": True}

# Command API
def handle_command(cmd: str) -> Dict[str, Any]: # Changed return type to Dict[str, Any]
    global auto_api_new_count, auto_rss_new_count, api_error_occurred, rss_error_occurred
    cmd = cmd.strip().lower()

    if cmd in ["collect", "collect api"]:
        log_push("[CMD] Manual API collection triggered (including AlphaVantage).")
        api_error_occurred = False # Reset error flag for manual collection
        try:
            new_articles = api_collector_main()
            new_count_from_this_run = len(new_articles)
            auto_api_new_count += new_count_from_this_run
            total_articles_in_db = news_postgres_utils.get_total_articles_count()
            
            # Convert datetime objects to ISO format strings for new_articles_list before pushing
            # This is now handled by _format_articles_for_push, so no explicit loop needed here.

            log_push("", data_payload={
                "type": "news_update",
                "api_new": auto_api_new_count,
                "rss_new": auto_rss_new_count,
                "total_articles": total_articles_in_db,
                "total_articles_mongo": news_mongo_utils.get_total_articles_count_mongo(),
                "new_articles_list": _format_articles_for_push(new_articles[:10]) # Limit to 10 articles
            })
            return {"success": True, "result": f"API collection completed. New articles: {new_count_from_this_run}"}
        except Exception as e:
            api_error_occurred = True
            return {"success": False, "result": f"API collection error: {e}"}
    elif cmd in ["collect rss"]:
        log_push("[CMD] Manual RSS collection triggered.")
        rss_error_occurred = False # Reset error flag for manual collection
        try:
            new_rss_articles = rss_collector_run()
            new_count_from_this_run = len(new_rss_articles)
            auto_rss_new_count += new_count_from_this_run
            total_articles_in_db = news_postgres_utils.get_total_articles_count()

            # Convert datetime objects to ISO format strings for new_articles_list before pushing
            # This is now handled by _format_articles_for_push, so no explicit loop needed here.

            log_push("", data_payload={
                "type": "news_update",
                "api_new": auto_api_new_count,
                "rss_new": auto_rss_new_count,
                "total_articles": total_articles_in_db,
                "total_articles_mongo": news_mongo_utils.get_total_articles_count_mongo(),
                "new_articles_list": _format_articles_for_push(new_rss_articles[:10]) # Limit to 10 articles
            })
            return {"success": True, "result": f"RSS collection completed. New articles: {new_count_from_this_run}"}
        except Exception as e:
            rss_error_occurred = True
            return {"success": False, "result": f"RSS collection error: {e}"}
    elif cmd in ["auto start", "start auto"]:
        return {"success": False, "result": "Please use the new API/RSS auto buttons above (or start_api/start_rss commands)."}
    elif cmd in ["auto stop", "stop auto"]:
        return {"success": False, "result": "Please use the new API/RSS auto buttons above (or stop_api/stop_rss commands)."}
    elif cmd in ["status"]:
        api_running = auto_api_thread and auto_api_thread.is_alive()
        rss_running = auto_rss_thread and auto_rss_thread.is_alive()
        pg_count = news_postgres_utils.get_total_articles_count()
        mongo_count = news_mongo_utils.get_total_articles_count_mongo()
        # Return a dictionary directly as api_command expects it now
        return {"success": True, "api_running": api_running, "rss_running": rss_running, "pg_articles": pg_count, "mongo_articles": mongo_count, "api_error_occurred": api_error_occurred, "rss_error_occurred": rss_error_occurred}
    elif cmd in ["help", "?"]:
        return {"success": True, "result": "Commands: collect, collect rss, status, help"}
    else:
        return {"success": False, "result": f"Unknown command: {cmd}"}

@post("/api/command")
async def api_command(data: Dict[str, Any]) -> Dict[str, Any]:
    cmd = data.get("cmd", "")
    result = handle_command(cmd)
    # Only log non-status commands
    if cmd.strip().lower() not in ["status"]:
        # Ensure result is a string for logging, if handle_command returns a dict
        log_message = result.get("result", str(result)) if isinstance(result, dict) else str(result)
        log_push(f"[CMD] {cmd} => {log_message}")
    
    # handle_command now always returns a dict, so just return it
    return result

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
        
        <div class="endpoint">
            <span class="method">POST</span> <span class="url">/api/auto/start</span> - Start auto collection
        </div>
        <div class="endpoint">
            <span class="method">POST</span> <span class="url">/api/auto/stop</span> - Stop auto collection
        </div>
        <div class="endpoint">
            <span class="method">POST</span> <span class="url">/api/command</span> - Execute command
        </div>
        <div class="endpoint">
            <span class="method">WS</span> <span class="url">/ws/logs</span> - Real-time logs
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

# Create Litestar app
app = Litestar(
    route_handlers=[
        index,
        health_check,
        get_news_api, # Correctly named
        get_stats,
        collect_api_news,
        collect_rss_news,
        get_sources,
        ws_logs,
        api_auto_start,
        api_auto_stop,
        api_command,
        api_auto_start_api,
        api_auto_stop_api,
        api_auto_start_rss,
        api_auto_stop_rss,
        api_auto_status,
        api_auto_reset_new,
    ],
    cors_config=cors_config,
    debug=True
) 