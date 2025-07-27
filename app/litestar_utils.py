"""
app/litestar_utils.py

This module provides utility functions specifically designed for Litestar application,
focusing on real-time logging and data formatting for WebSocket communication.

Functions:
- log_push: Pushes log messages or structured data payloads to a global queue for WebSocket clients.
- _format_articles_for_push: Formats news articles for consistent transmission over WebSocket.

Global Variables:
- log_queue: A queue used to buffer log messages and data updates before sending to WebSocket clients.

Dependencies:
- json, queue, datetime, typing: Standard Python libraries.

Author: Gemini AI Assistant
Last updated: 2024-07-30
"""

import json
import queue
from datetime import datetime
from typing import List, Dict, Any, Optional

# This will be set by main.py to ensure we use the same queue instance
log_queue: queue.Queue[str] = None

def set_log_queue(queue_instance: queue.Queue):
    """Set the log queue instance from main.py to avoid circular imports."""
    global log_queue
    log_queue = queue_instance

def log_push(msg: str, data_payload: Optional[Dict[str, Any]] = None):
    if log_queue is None:
        print(f"Warning: log_queue not initialized. Message: {msg}")
        return
        
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if data_payload:
        message = {"type": "data_update", "timestamp": timestamp, "payload": data_payload}
        log_queue.put(json.dumps(message))
    else:
        # Ensure all log messages are also JSON formatted for consistent frontend parsing
        log_entry_json = {"type": "log", "timestamp": timestamp, "message": msg}
        log_queue.put(json.dumps(log_entry_json))

def _format_articles_for_push(articles: List[Dict]) -> List[Dict]:
    """Helper to format articles before pushing to WebSocket."""
    for article in articles:
        if 'published_at' in article and isinstance(article.get('published_at'), datetime):
            article['published_at'] = article['published_at'].isoformat()
        if 'id' in article and not isinstance(article.get('id'), str):
            article['id'] = str(article['id'])
    return articles 