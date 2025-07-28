"""
news_rss_collector.py

This module is responsible for collecting news articles from various RSS feeds.
It fetches, parses, and transforms RSS feed items into a unified format,
and then saves them to both PostgreSQL and MongoDB databases, as well as a local JSON file.

Functions:
- load_sources: Loads RSS feed URLs from a configuration file.
- fetch_source: Fetches and parses articles from a single RSS feed.
- parse_item: Transforms a single RSS item into a standardized article dictionary.
- run: The main function to orchestrate the RSS news collection process.

Dependencies:
- requests: For making HTTP requests to fetch RSS feeds.
- xml.etree.ElementTree: For parsing XML content of RSS feeds.
- python-dateutil: For robust parsing of various date formats.
- news_db_utils: For saving articles to the database.
- news_api_settings: For utility functions like `log_print` and `load_json_sources_from_file`.

Author: Gemini AI Assistant
Last updated: 2024-07-30
"""

import requests
import xml.etree.ElementTree as ET
import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime # For RFC 2822 date parsing
# from dateutil import parser as dateutil_parser # Not directly used anymore, replaced by common utility

# Import local utility modules
import news_postgres_utils
from news_api_settings import load_json_sources_from_file # Removed log_print, Re-use load_json_sources_from_file
from utils.date_utils import parse_and_validate_published_date # Import common date utility

# --- Configuration ---
RSS_SOURCES_FILE = "sources/02_rss_sources.json"
NEWS_FILE_RSS = "outputs/01_rss_news.json"

# --- Logging Configuration (consistent with other modules) ---
# This module now relies on the root logger configured in start_app.py.

def load_sources() -> List[Dict]:
    """Loads RSS feed sources from the configured JSON file.

    Returns:
        List[Dict]: A list of dictionaries, each representing an RSS source with 'name' and 'url'.
    """
    return load_json_sources_from_file(RSS_SOURCES_FILE)

def fetch_source(source: Dict) -> List[Dict]:
    """Fetches and parses articles from a single RSS feed source.

    Args:
        source (Dict): A dictionary containing 'name' and 'url' of the RSS feed.

    Returns:
        List[Dict]: A list of raw articles from the RSS feed.
    """
    articles = []
    try:
        response = requests.get(source['url'], timeout=10)
        response.raise_for_status() # Raise an exception for HTTP errors
        root = ET.fromstring(response.content)

        # RSS feeds can have different structures (e.g., <item> for RSS 2.0, <entry> for Atom)
        items = root.findall('.//item') or root.findall('.//entry')

        for item in items:
            transformed_article = parse_item(item, source) # Pass the full source dictionary
            if transformed_article:
                articles.append(transformed_article)

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching RSS from {source['name']} ({source['url']}): {e}") # Use logging.error
    except ET.ParseError as e:
        logging.error(f"Error parsing XML from {source['name']} ({source['url']}): {e}") # Use logging.error
    except Exception as e:
        logging.error(f"Unexpected error for {source['name']}: {e}") # Use logging.error
    return articles

def parse_item(item: Any, source: Dict) -> Optional[Dict]: # Updated to accept source: Dict
    """Parses a single RSS/Atom item/entry into a unified article format.

    Args:
        item (Any): The XML element representing an RSS item or Atom entry.
        source (Dict): The dictionary representing the RSS source.

    Returns:
        Optional[Dict]: A dictionary representing the transformed article, or None if parsing fails.
    """
    title_element = item.find('title')
    title = title_element.text if title_element is not None else "No Title"

    link_element = item.find('link')
    url = link_element.text if link_element is not None else item.attrib.get('href') # For Atom feeds
    if not url: return None

    # Attempt to get description/summary
    description_element = item.find('description') or item.find('{http://www.w3.org/2005/Atom}summary')
    description = description_element.text if description_element is not None else ''

    # Attempt to get full content (often in <content:encoded> or similar)
    full_content_element = item.find('{http://purl.org/rss/1.0/modules/content/}encoded') or \
                           item.find('{http://www.w3.org/2005/Atom}content')
    full_content = full_content_element.text if full_content_element is not None else description

    # Parse published date using common utility
    pub_date_element = item.find('pubDate') or item.find('{http://www.w3.org/2005/Atom}published')
    published_at = parse_and_validate_published_date(pub_date_element.text) if pub_date_element is not None else None
    if published_at is None: # Fallback if parsing fails or no date element
        published_at = datetime.now(timezone.utc) - timedelta(hours=1) # Fallback to 1 hour ago UTC

    # Optional fields, often not present in RSS
    image_url = item.find('image') or item.find('{http://search.yahoo.com/mrss/}thumbnail')
    image_url = image_url.attrib.get('url') if image_url is not None else None
    
    language = item.find('language')
    language = language.text if language is not None else 'en' # Default to English

    authors = [] # RSS feeds often don't specify authors in a structured way
    tickers = []
    topics = [tag.text for tag in item.findall('category') if tag.text is not None] # Changed from tags to topics

    return {
        "title": title,
        "description": description,
        "url": url,
        "image_url": image_url,
        "published_at": published_at,
        "source_name": source['name'],
        "source_url": source.get('link', url), # RSS often uses feed link as source URL
        "language": language,
        "full_content": full_content,
        "authors": authors,
        "tickers": tickers,
        "topics": topics # Changed from tags to topics
    }

def run() -> List[Dict]:
    """Main function to run the RSS news collection process.

    This function loads RSS sources, fetches articles from each, transforms them,
    and then saves new/deduplicated articles to both the database (PostgreSQL and MongoDB)
    and a local JSON file.

    Returns:
        List[Dict]: A list of newly saved articles (after deduplication and DB insertion).
    """
    sources = load_sources()
    if not sources:
        logging.warning("RSS: No sources configured. Returning empty list.") # Use logging.warning
        return []
    
    logging.info(f'Checking and fetching {len(sources)} RSS sources...') # Use logging.info
    
    fetched_articles = []
    for source in sources:
        try:
            items = fetch_source(source)
            fetched_articles.extend(items)
            url_short = source.get('url', '').split('//')[-1].split('/')[0]
            logging.info(f"✓ {source['name']} ({url_short}) fetched {len(items)} items.") # Use logging.info
        except Exception as e:
            logging.error(f"✗ {source['name']} - {str(e)}") # Use logging.error
    
    if fetched_articles:
        logging.info(f"Attempting to save {len(fetched_articles)} RSS articles to DB and JSON.") # Use logging.info
        result = news_postgres_utils.save_articles_simple(fetched_articles, NEWS_FILE_RSS)
        logging.info(f"RSS: Fetched {len(fetched_articles)} articles. Saved to DB: {result['db_count']}, JSON: {result['json_count']}, Mongo: {result['mongo_count']}. Total new articles: {len(result.get('new_articles', []))}") # Use logging.info
        logging.info(f"Total unique items in DB: {news_postgres_utils.get_total_articles_count()}") # Use logging.info
        return result.get('new_articles', [])
    else:
        logging.info("RSS: No new articles fetched or all were duplicates.") # Use logging.info
        return []

if __name__ == "__main__":
    logging.info("Starting RSS collection...") # Use logging.info
    new_articles = run()
    logging.info(f"RSS collection finished. Total new articles: {len(new_articles)}") # Use logging.info