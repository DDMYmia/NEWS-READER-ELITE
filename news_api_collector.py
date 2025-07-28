#!/usr/bin/env python3
"""
news_api_collector.py

This module orchestrates the collection of news articles from multiple API sources.
It manages the execution of various news API collectors, handles data transformation,
and coordinates saving to both PostgreSQL and MongoDB databases.

Main Functions:
- run_single_collector: Executes a single collector and saves results.
- run_all_collectors: Orchestrates the execution of all configured collectors.
- main: Entry point for running the complete API collection process.

Dependencies:
- news_api_settings: Contains collector classes and utility functions.
- news_postgres_utils: For saving articles to PostgreSQL and MongoDB.
- news_mongo_utils: For MongoDB operations.

Usage:
This module is used by the main application to collect news from all configured APIs.
It can be run independently or as part of the automated collection system.

Author: Gemini AI Assistant
Last updated: 2024-07-30
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import collector classes and utilities
from news_api_settings import (
    NewsAPIAICollector,
    TheNewsAPICollector,
    NewsDataCollector,
    TiingoCollector,
    AlphaVantageCollector,
    load_sources_from_file,
    load_json_sources_from_file
)

# Import database utilities
import news_postgres_utils

def _run_single_collector(collector_class, collector_name: str) -> List[Dict[str, Any]]:
    """
    Executes a single collector and saves the results to the database.
    
    Args:
        collector_class: The collector class to instantiate and run.
        collector_name (str): Name of the collector for logging purposes.
        
    Returns:
        List[Dict[str, Any]]: List of newly saved articles from this collector.
    """
    try:
        collector = collector_class()
        new_articles = collector.run_collector()
        
        if new_articles:
            # Save to database using the unified save function
            result = news_postgres_utils.save_articles_simple(new_articles, collector.output_file)
            logging.info(f"{collector_name}: Fetched {len(new_articles)} articles. Saved to DB: {result['db_count']}, JSON: {result['json_count']}, Mongo: {result['mongo_count']}.")
            return result.get('new_articles', [])
        else:
            logging.info(f"{collector_name}: No new articles fetched or all were duplicates.")
            return []
            
    except Exception as e:
        logging.error(f"Error running {collector_name}: {e}")
        return []

def run_all_collectors() -> List[Dict[str, Any]]:
    """
    Executes all configured news API collectors and returns newly saved articles.
    
    Returns:
        List[Dict[str, Any]]: List of all newly saved articles from all collectors.
    """
    collectors = [
        (NewsAPIAICollector, "NewsAPI.ai"),
        (TheNewsAPICollector, "TheNewsAPI"),
        (NewsDataCollector, "NewsData.io"),
        (TiingoCollector, "Tiingo"),
        (AlphaVantageCollector, "AlphaVantage")
    ]
    
    all_new_articles = []
    
    for collector_class, collector_name in collectors:
        try:
            collector_result = _run_single_collector(collector_class, collector_name)
            
            # Ensure the result is a list
            if isinstance(collector_result, list):
                all_new_articles.extend(collector_result)
            else:
                logging.warning(f"Warning: A collector returned a non-list result of type {type(collector_result)}. Result was ignored.")
                
        except Exception as e:
            logging.error(f"Error in collector {collector_name}: {e}")
            continue
    
    return all_new_articles

def main():
    """
    Main function to run the complete API news collection process.
    This function orchestrates the collection from all APIs and provides summary statistics.
    """
    logging.info("Starting API news collection...")
    
    # Run all collectors
    all_new_articles = run_all_collectors()
    
    # Log summary
    logging.info(f"API collection finished. Total new articles this run: {len(all_new_articles)}.")
    
    # Get total count from database
    total_count = news_postgres_utils.get_total_articles_count()
    logging.info(f"Total articles in database: {total_count}")
    
    return all_new_articles

if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    new_articles = main()
    logging.info(f"Total new articles saved to DB and JSON: {len(new_articles)}")