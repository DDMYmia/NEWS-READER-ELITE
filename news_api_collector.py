import logging
import argparse
import time
import subprocess
import sys
import os
import json
from news_api_settings import NewsAPIAICollector, TheNewsAPICollector, NewsDataCollector, TiingoCollector, load_sources_from_file

import news_db_utils

def get_all_sources():
    """Get all sources from sources/01_api_sources.txt"""
    return load_sources_from_file()

def get_tiingo_tags():
    """Get Tiingo tags"""
    return [
        'technology',
        'earnings', 
        'finance',
        'business',
        'innovation',
        'politics',
        'world',
        'sports'
    ]

def setup_logging(auto_mode=False):
    """Setup logging configuration"""
    if auto_mode:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/01_api_collector.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def get_json_file_counts():
    """Get total article counts from JSON files."""
    counts = {}
    json_files = [
        'outputs/02_newsapi_ai.json',
        'outputs/03_thenewsapi.json',
        'outputs/04_newsdata.json',
        'outputs/05_tiingo.json'
    ]
    
    total_json = 0
    for file_path in json_files:
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    count = len(data) if isinstance(data, list) else 0
                    counts[os.path.basename(file_path)] = count
                    total_json += count
        except Exception:
            counts[os.path.basename(file_path)] = 0
    
    return counts, total_json

def run_newsapi_ai():
    """Run NewsAPI.ai collector"""
    try:
        collector = NewsAPIAICollector()
        source_uris = get_all_sources()
        articles, error, duplicate_count = collector.fetch_articles(
            lang='en', 
            max_items=10,
            source_uri=source_uris
        )
        if error:
            logging.warning(f"NewsAPI.ai: {error}")
            return
        if articles:
            result = collector.save_articles(articles)
            logging.info(f"NewsAPI.ai: {len(articles) + duplicate_count} news → Dup {duplicate_count} → DB + {result['db_count']} JSON + {result['json_count']}")
        else:
            if duplicate_count > 0:
                logging.info(f"NewsAPI.ai: {duplicate_count} news → Dup {duplicate_count} → No fetched")
            else:
                logging.warning("NewsAPI.ai: No articles fetched")
    except Exception as e:
        logging.error(f"NewsAPI.ai: Error - {e}")

def run_thenewsapi():
    """Run TheNewsAPI collector"""
    try:
        collector = TheNewsAPICollector()
        source_domains = get_all_sources()
        articles, error, duplicate_count = collector.fetch_articles(domains=source_domains, max_items=3)
        if error:
            logging.warning(f"TheNewsAPI: {error}")
            return
        if articles:
            result = collector.save_articles(articles)
            logging.info(f"TheNewsAPI: {len(articles) + duplicate_count} news → Dup {duplicate_count} → DB + {result['db_count']} JSON + {result['json_count']}")
        else:
            if duplicate_count > 0:
                logging.info(f"TheNewsAPI: {duplicate_count} news → Dup {duplicate_count} → No fetched")
            else:
                logging.warning("TheNewsAPI: No articles fetched")
    except Exception as e:
        logging.error(f"TheNewsAPI: Error - {e}")

def run_newsdata():
    """Run NewsData.io collector"""
    try:
        collector = NewsDataCollector()
        # Use source filtering, only collect from configured sources
        source_domains = get_all_sources()
        # NewsData.io doesn't support domain parameter, use client-side filtering
        articles, error, duplicate_count = collector.fetch_articles(
            query='technology', 
            lang='en', 
            max_items=10,  # Use default count
            all_sources=source_domains  # Pass all sources for client-side filtering
        )
        if error:
            logging.warning(f"NewsData.io: {error}")
            return
        if articles:
            result = collector.save_articles(articles)
            logging.info(f"NewsData.io: {len(articles) + duplicate_count} news → Dup {duplicate_count} → DB + {result['db_count']} JSON + {result['json_count']}")
        else:
            if duplicate_count > 0:
                logging.info(f"NewsData.io: {duplicate_count} news → Dup {duplicate_count} → No fetched")
            else:
                logging.warning("NewsData.io: No articles fetched")
    except Exception as e:
        logging.error(f"NewsData.io: Error - {e}")

def run_tiingo():
    """Run Tiingo collector"""
    try:
        collector = TiingoCollector()
        sources = get_all_sources()
        tags = get_tiingo_tags()
        articles, error, duplicate_count = collector.fetch_articles(
            sources=sources[:5],  # Use first 5 sources
            tags=tags[:3],        # Use first 3 tags
            max_items=10
        )
        if error:
            logging.warning(f"Tiingo: {error}")
            return
        if articles:
            result = collector.save_articles(articles)
            logging.info(f"Tiingo: {len(articles) + duplicate_count} news → Dup {duplicate_count} → DB + {result['db_count']} JSON + {result['json_count']}")
        else:
            if duplicate_count > 0:
                logging.info(f"Tiingo: {duplicate_count} news → Dup {duplicate_count} → No fetched")
            else:
                logging.warning("Tiingo: No articles fetched")
    except Exception as e:
        logging.error(f"Tiingo: Error - {e}")

def run_collection():
    """Run all collectors"""
    logging.info("Starting news collection...")
    
    run_newsapi_ai()
    run_thenewsapi()
    run_newsdata()
    run_tiingo()
    
    # Get total counts and deduplication stats
    total_db = news_db_utils.get_total_articles_count()
    json_counts, total_json = get_json_file_counts()
    dedup_stats = news_db_utils.get_deduplication_stats()
    
    # Display results
    logging.info(f"Collection completed - Total DB: {total_db} JSON: {total_json}")
    
    # Display deduplication statistics if available
    if dedup_stats:
        logging.info(f"Deduplication stats - Total: {dedup_stats.get('total_articles', 0)}, "
                    f"Unique titles: {dedup_stats.get('unique_titles', 0)}, "
                    f"Duplicates removed: {dedup_stats.get('duplicate_titles', 0)}")

def run_auto_collection(interval_minutes=3):
    """Run collection in auto mode with specified interval"""
    setup_logging(auto_mode=True)
    logging.info(f"Auto collector started - interval: {interval_minutes} minutes")
    
    while True:
        try:
            run_collection()
            logging.info(f"Waiting {interval_minutes} minutes...")
            time.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            logging.info("Auto collector stopped")
            break
        except Exception as e:
            logging.error(f"Main loop error: {e}")
            time.sleep(60)

def main():
    parser = argparse.ArgumentParser(description="News Collector - Manual or Auto Mode")
    parser.add_argument("--auto", action="store_true", help="Run in auto mode with 3-minute intervals")
    parser.add_argument("--interval", type=int, default=3, help="Collection interval in minutes (default: 3)")
    parser.add_argument("--stats", action="store_true", help="Show deduplication statistics only")
    
    args = parser.parse_args()
    
    if args.stats:
        setup_logging(auto_mode=False)
        dedup_stats = news_db_utils.get_deduplication_stats()
        if dedup_stats:
            logging.info("=== Deduplication Statistics ===")
            logging.info(f"Total articles: {dedup_stats.get('total_articles', 0)}")
            logging.info(f"Unique titles: {dedup_stats.get('unique_titles', 0)}")
            logging.info(f"Unique URLs: {dedup_stats.get('unique_urls', 0)}")
            logging.info(f"Duplicates removed: {dedup_stats.get('duplicate_titles', 0)}")
        else:
            logging.error("Failed to get deduplication statistics")
        return
    
    if args.auto:
        run_auto_collection(args.interval)
    else:
        setup_logging(auto_mode=False)
        run_collection()

if __name__ == "__main__":
    main()