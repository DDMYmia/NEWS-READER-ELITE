from litestar import Litestar, get, post, websocket
from litestar.config.cors import CORSConfig
from litestar.response import Response
from litestar.status_codes import HTTP_200_OK
from litestar.connection import WebSocket
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import threading
import asyncio
import queue
import time

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

# 日志队列和WebSocket客户端管理
log_queue = queue.Queue()
ws_clients = set()

# 自动API采集任务管理
auto_api_thread = None
auto_api_stop_event = threading.Event()
# 自动RSS采集任务管理
auto_rss_thread = None
auto_rss_stop_event = threading.Event()
# 新增条目计数
auto_api_new_count = 0
auto_rss_new_count = 0

# 日志推送函数

def log_push(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {msg}"
    log_queue.put(log_entry)

# 自动采集任务

def auto_collect_loop(interval=180):
    log_push(f"[AUTO] Auto collection started, interval={interval}s")
    while not auto_collect_stop_event.is_set():
        try:
            log_push("[AUTO] Collecting API news...")
            api_collector_main()
            log_push("[AUTO] Collecting RSS news...")
            rss_collector_run()
            log_push("[AUTO] Collection round finished.")
        except Exception as e:
            log_push(f"[AUTO] Error: {e}")
        for _ in range(interval):
            if auto_collect_stop_event.is_set():
                break
            time.sleep(1)
    log_push("[AUTO] Auto collection stopped.")

def auto_api_loop(interval=180):
    global auto_api_new_count
    log_push(f"[AUTO-API] Auto API collection started, interval={interval}s")
    while not auto_api_stop_event.is_set():
        try:
            log_push("[AUTO-API] Collecting API news...")
            before = get_db_count()
            api_collector_main()
            after = get_db_count()
            new_count = max(0, after - before)
            auto_api_new_count += new_count
            log_push(f"[AUTO-API] New articles: {new_count}")
            log_push("[AUTO-API] Collection round finished.")
        except Exception as e:
            log_push(f"[AUTO-API] Error: {e}")
        for _ in range(interval):
            if auto_api_stop_event.is_set():
                break
            time.sleep(1)
    log_push("[AUTO-API] Auto API collection stopped.")

def auto_rss_loop(interval=180):
    global auto_rss_new_count
    log_push(f"[AUTO-RSS] Auto RSS collection started, interval={interval}s")
    while not auto_rss_stop_event.is_set():
        try:
            log_push("[AUTO-RSS] Collecting RSS news...")
            before = get_rss_count()
            rss_collector_run()
            after = get_rss_count()
            new_count = max(0, after - before)
            auto_rss_new_count += new_count
            log_push(f"[AUTO-RSS] New articles: {new_count}")
            log_push("[AUTO-RSS] Collection round finished.")
        except Exception as e:
            log_push(f"[AUTO-RSS] Error: {e}")
        for _ in range(interval):
            if auto_rss_stop_event.is_set():
                break
            time.sleep(1)
    log_push("[AUTO-RSS] Auto RSS collection stopped.")

def get_db_count():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM articles")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count
    except:
        return 0

def get_rss_count():
    try:
        with open("outputs/01_rss_news.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return len(data)
            elif isinstance(data, dict) and 'articles' in data:
                return len(data['articles'])
        return 0
    except:
        return 0

# WebSocket 日志推送
@websocket("/ws/logs")
async def ws_logs(socket: WebSocket) -> None:
    ws_clients.add(socket)
    try:
        await socket.accept()
        await socket.send_text("[Console] Connected to backend log stream.")
        while True:
            try:
                msg = log_queue.get(timeout=1)
                try:
                    await socket.send_text(msg)
                except Exception as e:
                    print(f"WebSocket send_text error: {e}")
                    break  # 发送失败直接退出循环
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

# API: 启动/停止自动API采集
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

# API: 启动/停止自动RSS采集
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
    started = start_auto_collection(interval)
    if started:
        log_push(f"[API] Auto collection started via API, interval={interval}s")
        return {"success": True, "message": "Auto collection started."}
    else:
        return {"success": False, "message": "Auto collection already running."}

@post("/api/auto/stop")
async def api_auto_stop() -> Dict[str, Any]:
    stop_auto_collection()
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
    return {
        "api_running": auto_api_thread and auto_api_thread.is_alive(),
        "rss_running": auto_rss_thread and auto_rss_thread.is_alive(),
        "api_new": auto_api_new_count,
        "rss_new": auto_rss_new_count
    }

@post("/api/auto/reset_new")
async def api_auto_reset_new(data: Dict[str, Any]) -> Dict[str, Any]:
    global auto_api_new_count, auto_rss_new_count
    if data.get("type") == "api":
        auto_api_new_count = 0
    elif data.get("type") == "rss":
        auto_rss_new_count = 0
    return {"success": True}

# 命令API
def handle_command(cmd: str) -> str:
    cmd = cmd.strip().lower()
    if cmd in ["collect", "collect api"]:
        log_push("[CMD] Manual API collection triggered.")
        try:
            api_collector_main()
            return "API collection completed."
        except Exception as e:
            return f"API collection error: {e}"
    elif cmd in ["collect rss"]:
        log_push("[CMD] Manual RSS collection triggered.")
        try:
            rss_collector_run()
            return "RSS collection completed."
        except Exception as e:
            return f"RSS collection error: {e}"
    elif cmd in ["auto start", "start auto"]:
        return "Please use the new API/RSS auto buttons above."
    elif cmd in ["auto stop", "stop auto"]:
        return "Please use the new API/RSS auto buttons above."
    elif cmd in ["status"]:
        api_running = auto_api_thread and auto_api_thread.is_alive()
        rss_running = auto_rss_thread and auto_rss_thread.is_alive()
        return f"API auto: {api_running}, RSS auto: {rss_running}"
    elif cmd in ["help", "?"]:
        return "Commands: collect, collect rss, status, help"
    else:
        return f"Unknown command: {cmd}"

@post("/api/command")
async def api_command(data: Dict[str, Any]) -> Dict[str, Any]:
    cmd = data.get("cmd", "")
    result = handle_command(cmd)
    # 只记录非 status 命令
    if cmd.strip().lower() not in ["status"]:
        log_push(f"[CMD] {cmd} => {result}")
    return {"success": True, "result": result}

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
        ws_logs, # Add WebSocket handler to route_handlers
        api_auto_start, # Add auto start handler
        api_auto_stop, # Add auto stop handler
        api_command, # Add command handler
        api_auto_start_api, # Add auto start API handler
        api_auto_stop_api, # Add auto stop API handler
        api_auto_start_rss, # Add auto start RSS handler
        api_auto_stop_rss, # Add auto stop RSS handler
        api_auto_status, # Add auto status handler
        api_auto_reset_new, # Add auto reset new handler
    ],
    cors_config=cors_config,
    debug=True
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 