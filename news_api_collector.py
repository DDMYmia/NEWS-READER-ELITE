"""
news_api_collector.py

This module orchestrates the execution of various news API collectors.
It runs each collector, saves the newly fetched articles to both PostgreSQL and MongoDB,
and records statistics for each run.

Functions:
- get_json_file_counts: Retrieves article counts from local JSON files.
- run_newsapi_ai: Executes the NewsAPI.ai collector.
- run_thenewsapi: Executes TheNewsAPI.com collector.
- run_newsdata: Executes NewsData.io collector.
- run_tiingo: Executes the Tiingo collector.
- run_alpha_vantage: Executes the AlphaVantage collector.
- main: The primary function to run all configured API news collectors.

Dependencies:
- news_api_settings: Contains definitions for individual API collectors and utility functions.
- news_db_utils: Provides functions for saving articles to the database and getting database statistics.

Usage:
Call the `main()` function to initiate a full API news collection run.

Author: Gemini AI Assistant
Last updated: 2024-07-30
"""

import os
import json
import logging
from typing import List, Dict

# Import collector classes and utility functions from news_api_settings
from news_api_settings import (
    NewsAPIAICollector,
    TheNewsAPICollector,
    NewsDataCollector,
    TiingoCollector,
    AlphaVantageCollector,
    log_print,
    NEWS_FILE_NEWSAPI_AI,
    NEWS_FILE_THENEWSAPI,
    NEWS_FILE_NEWSDATA,
    NEWS_FILE_TIINGO,
    NEWS_FILE_ALPHA_VANTAGE
)

# Import database utility functions
import news_postgres_utils


def get_json_file_counts() -> Dict[str, int]:
    """Gets the current article counts from all relevant JSON output files.

    Returns:
        Dict[str, int]: A dictionary mapping output file names (without path/extension) to their article counts.
    """
    counts = {}
    json_files = [
        NEWS_FILE_NEWSAPI_AI, NEWS_FILE_THENEWSAPI, NEWS_FILE_NEWSDATA,
        NEWS_FILE_TIINGO, NEWS_FILE_ALPHA_VANTAGE
    ]
    for file_path in json_files:
        file_name = os.path.basename(file_path).replace('.json', '')
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    counts[file_name] = len(data) if isinstance(data, list) else 0
        except Exception as e:
            log_print(f"Error reading JSON file {file_path}: {e}", 'error')
            counts[file_name] = 0
    return counts

def run_newsapi_ai() -> List[Dict]:
    """Runs the NewsAPI.ai collector to fetch, transform, and save articles.

    Returns:
        List[Dict]: A list of newly saved articles (after deduplication and DB insertion).
    """
    collector = NewsAPIAICollector()
    new_articles = collector.run_collector() # Returns articles newly added to JSON
    if new_articles:
        result = news_postgres_utils.save_articles_simple(new_articles, NEWS_FILE_NEWSAPI_AI)
        log_print(f"NewsAPI.ai: Fetched {len(new_articles)} articles. Saved to DB: {result['db_count']}, JSON: {result['json_count']}, Mongo: {result['mongo_count']}.")
    else:
        log_print("NewsAPI.ai: No new articles fetched or all were duplicates.")
    return new_articles

def run_thenewsapi() -> List[Dict]:
    """Runs TheNewsAPI.com collector to fetch, transform, and save articles.

    Returns:
        List[Dict]: A list of newly saved articles (after deduplication and DB insertion).
    """
    collector = TheNewsAPICollector()
    new_articles = collector.run_collector()
    if new_articles:
        result = news_postgres_utils.save_articles_simple(new_articles, NEWS_FILE_THENEWSAPI)
        log_print(f"TheNewsAPI: Fetched {len(new_articles)} articles. Saved to DB: {result['db_count']}, JSON: {result['json_count']}, Mongo: {result['mongo_count']}.")
    else:
        log_print("TheNewsAPI: No new articles fetched or all were duplicates.")
    return new_articles

def run_newsdata() -> List[Dict]:
    """Runs the NewsData.io collector to fetch, transform, and save articles.

    Returns:
        List[Dict]: A list of newly saved articles (after deduplication and DB insertion).
    """
    collector = NewsDataCollector()
    new_articles = collector.run_collector()
    if new_articles:
        result = news_postgres_utils.save_articles_simple(new_articles, NEWS_FILE_NEWSDATA)
        log_print(f"NewsData.io: Fetched {len(new_articles)} articles. Saved to DB: {result['db_count']}, JSON: {result['json_count']}, Mongo: {result['mongo_count']}.")
    else:
        log_print("NewsData.io: No new articles fetched or all were duplicates.")
    return new_articles

def run_tiingo() -> List[Dict]:
    """Runs the Tiingo collector to fetch, transform, and save articles.

    Returns:
        List[Dict]: A list of newly saved articles (after deduplication and DB insertion).
    """
    collector = TiingoCollector()
    new_articles = collector.run_collector()
    if new_articles:
        result = news_postgres_utils.save_articles_simple(new_articles, NEWS_FILE_TIINGO)
        log_print(f"Tiingo: Fetched {len(new_articles)} articles. Saved to DB: {result['db_count']}, JSON: {result['json_count']}, Mongo: {result['mongo_count']}.")
    else:
        log_print("Tiingo: No new articles fetched or all were duplicates.")
    return new_articles

def run_alpha_vantage() -> List[Dict]:
    """Runs the AlphaVantage collector to fetch, transform, and save articles.

    Returns:
        List[Dict]: A list of newly saved articles (after deduplication and DB insertion).
    """
    collector = AlphaVantageCollector()
    new_articles = collector.run_collector()
    if new_articles:
        result = news_postgres_utils.save_articles_simple(new_articles, NEWS_FILE_ALPHA_VANTAGE)
        log_print(f"AlphaVantage: Fetched {len(new_articles)} articles. Saved to DB: {result['db_count']}, JSON: {result['json_count']}, Mongo: {result['mongo_count']}.")
    else:
        log_print("AlphaVantage: No new articles fetched or all were duplicates.")
    return new_articles

def main() -> List[Dict]:
    """Main function to run all API news collectors.
    This function executes each configured API collector and aggregates the newly saved articles.

    Returns:
        List[Dict]: A combined list of all newly saved articles from all API collectors in this run.
    """
    log_print("Starting API news collection...")
    
    all_new_articles = []

    # Run each collector and extend the list of new articles
    new_from_newsapi_ai = run_newsapi_ai()
    if new_from_newsapi_ai: all_new_articles.extend(new_from_newsapi_ai)

    new_from_thenewsapi = run_thenewsapi()
    if new_from_thenewsapi: all_new_articles.extend(new_from_thenewsapi)

    new_from_newsdata = run_newsdata()
    if new_from_newsdata: all_new_articles.extend(new_from_newsdata)

    new_from_tiingo = run_tiingo()
    if new_from_tiingo: all_new_articles.extend(new_from_tiingo)

    new_from_alpha_vantage = run_alpha_vantage()
    if new_from_alpha_vantage: all_new_articles.extend(new_from_alpha_vantage)
    
    log_print(f"API collection finished. Total new articles this run: {len(all_new_articles)}.")
    return all_new_articles

if __name__ == "__main__":
    # Example of running the main API collection function
    new_articles = main()
    log_print(f"Total new articles saved to DB and JSON: {len(new_articles)}")
    # You can further process or inspect new_articles if needed