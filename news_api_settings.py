"""
news_api_settings.py

Unified API collectors for multiple news sources (NewsAPI.ai, TheNewsAPI, NewsData.io, Tiingo, AlphaVantage).

Main Classes:
- BaseCollector: Abstract base class for all news API collectors.
- NewsAPIAICollector: Collector for NewsAPI.ai (Event Registry).
- TheNewsAPICollector: Collector for TheNewsAPI.com.
- NewsDataCollector: Collector for NewsData.io.
- TiingoCollector: Collector for Tiingo Financial News.
- AlphaVantageCollector: Collector for AlphaVantage Market News and Sentiment.

Features:
- Configurable API keys and base URLs.
- Standardized article transformation to a unified format.
- Local JSON file saving for each API.
- Integration with news_postgres_utils for database persistence and deduplication.
- Utility functions for loading API and RSS sources.

Dependencies:
- requests: For making HTTP requests to external APIs.
- python-dateutil: For robust parsing of various datetime formats.
- python-dotenv: For loading environment variables.
- news_postgres_utils: For saving articles to the database.

Usage:
Collector instances are used by `news_api_collector.py` to fetch, transform, and save articles.

Author: Gemini AI Assistant
Last updated: 2024-07-30
"""

# Python Standard Library Imports
import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta

# Third-party Imports
import requests
from dateutil import parser as dateutil_parser
from dotenv import load_dotenv

# Local Utility Imports
from utils.date_utils import parse_and_validate_published_date # Import the common date utility

# Load environment variables from .env file
load_dotenv()

# --- Logging Configuration ---
# Removed centralized logging configuration and log_print function, as it's now handled in start_app.py
# The logging calls will now rely on the root logger configured in start_app.py.

# --- API Key Loading and Base URLs ---
NEWSAPI_AI_API_KEY = os.getenv("NEWSAPI_AI_API_KEY")
THENEWSAPI_API_KEY = os.getenv("THENEWSAPI_API_KEY")
NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")
TIINGO_API_KEY = os.getenv("TIINGO_API_KEY")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

NEWSAPI_AI_BASE_URL = "https://eventregistry.org/api/v1/article/getArticles"
THENEWSAPI_BASE_URL = "https://api.thenewsapi.com/v1/news/all"
NEWSDATA_BASE_URL = "https://newsdata.io/api/1/latest"
TIINGO_BASE_URL = "https://api.tiingo.com/tiingo/news"
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

# --- Source File Configuration ---
API_SOURCES_FILE = "sources/01_api_sources.txt"
RSS_SOURCES_FILE = "sources/02_rss_sources.json"

# --- Output File Configuration ---
NEWS_FILE_RSS = "outputs/01_rss_news.json"
NEWS_FILE_NEWSAPI_AI = "outputs/02_newsapi_ai.json"
NEWS_FILE_THENEWSAPI = "outputs/03_thenewsapi.json"
NEWS_FILE_NEWSDATA = "outputs/04_newsdata.json"
NEWS_FILE_TIINGO = "outputs/05_tiingo.json"
NEWS_FILE_ALPHA_VANTAGE = "outputs/06_alpha_vantage.json"

# --- Utility Functions ---
def load_sources_from_file(file_path: str) -> List[str]:
    """Loads a list of sources (e.g., domain names) from a text file, one source per line.

    Args:
        file_path (str): The path to the source file.

    Returns:
        List[str]: A list of sources.
    """
    sources = []
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                sources = [line.strip() for line in f if line.strip()]
        except Exception as e:
            logging.error(f"Error loading sources from {file_path}: {e}") # Use logging.error
    return sources

def load_json_sources_from_file(file_path: str) -> List[Dict]:
    """Loads a list of JSON objects (e.g., RSS feeds with name and URL) from a JSON file.

    Args:
        file_path (str): The path to the JSON source file.

    Returns:
        List[Dict]: A list of dictionaries, each representing a source.
    """
    sources = []
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                sources = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logging.error(f"Error loading JSON sources from {file_path}: {e}") # Use logging.error
    return sources

# --- Base Collector Class ---
class BaseCollector:
    """Abstract base class for all news API collectors.
    Provides common methods for fetching, transforming, and saving articles.
    """
    def __init__(self, api_key: str, base_url: str, output_file: str):
        self.api_key = api_key
        self.base_url = base_url
        self.output_file = output_file
        self.deduplicated_articles = self._load_existing_articles()

    def _load_existing_articles(self) -> List[Dict]:
        """Loads existing articles from the output JSON file for internal deduplication before saving.

        Returns:
            List[Dict]: A list of articles already present in the JSON file.
        """
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logging.error(f"Error loading existing articles from {self.output_file}: {e}") # Use logging.error
        return []

    def _save_articles(self, articles: List[Dict]) -> List[Dict]:
        """Saves articles to the output JSON file and updates the internal deduplication list.
        This method handles local JSON backup. Actual database deduplication is handled by `news_db_utils`.

        Args:
            articles (List[Dict]): A list of transformed articles to save.

        Returns:
            List[Dict]: A list of articles that were newly added to the JSON file.
        """
        existing_urls = {article['url'] for article in self.deduplicated_articles if 'url' in article}
        newly_added = []
        for article in articles:
            if 'url' in article and article['url'] not in existing_urls:
                self.deduplicated_articles.append(article)
                newly_added.append(article)
                existing_urls.add(article['url'])
        
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            # Ensure datetime objects are converted to ISO format for JSON serialization
            serializable_articles = []
            for article in self.deduplicated_articles:
                temp_article = article.copy()
                if 'published_at' in temp_article and isinstance(temp_article['published_at'], datetime):
                    temp_article['published_at'] = temp_article['published_at'].isoformat()
                serializable_articles.append(temp_article)

            json.dump(serializable_articles, f, ensure_ascii=False, indent=2)
        
        return newly_added

    def _fetch_data(self, params: Dict) -> Optional[Dict]:
        """Fetches data from the API endpoint.

        Args:
            params (Dict): Dictionary of query parameters for the API request.

        Returns:
            Optional[Dict]: The JSON response from the API, or None if an error occurred or API key is missing.
        """
        if not self.api_key:
            logging.warning(f"API key not provided for {self.__class__.__name__}. Skipping fetch.") # Use logging.warning
            return None
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status() # Raise an exception for HTTP errors
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching data from {self.__class__.__name__}: {e}") # Use logging.error
            return None

    # Removed _parse_and_validate_published_date from here as it's now a common utility in utils/date_utils.py

    def fetch_articles(self) -> List[Dict]:
        """Abstract method to fetch articles from the specific API.
        Must be implemented by subclasses.

        Returns:
            List[Dict]: A list of raw articles fetched from the API.
        """
        raise NotImplementedError("fetch_articles method must be implemented by subclasses")

    def _transform_article(self, article: Dict) -> Optional[Dict]:
        """Abstract method to transform raw article data into a unified format.
        Must be implemented by subclasses.

        Args:
            article (Dict): The raw article dictionary from the API response.

        Returns:
            Optional[Dict]: The transformed article dictionary, or None if transformation fails.
        """
        raise NotImplementedError("_transform_article method must be implemented by subclasses")

    def run_collector(self) -> List[Dict]:
        """Runs the collection process for a specific API: fetches, transforms, and saves articles.

        Returns:
            List[Dict]: A list of articles that were newly added to the JSON file in this run.
        """
        logging.info(f"Running {self.__class__.__name__}...") # Use logging.info
        fetched_articles = self.fetch_articles()
        transformed_articles = [
            self._transform_article(article) for article in fetched_articles
            if self._transform_article(article) is not None # Filter out None after transformation
        ]
        newly_saved_articles = self._save_articles(transformed_articles)
        return newly_saved_articles

# --- Specific Collector Implementations ---
class NewsAPIAICollector(BaseCollector):
    """Collector for NewsAPI.ai (EventRegistry)."""
    def __init__(self):
        super().__init__(NEWSAPI_AI_API_KEY, NEWSAPI_AI_BASE_URL, NEWS_FILE_NEWSAPI_AI)

    def fetch_articles(self) -> List[Dict]:
        sources_list = load_sources_from_file(API_SOURCES_FILE)
        if not sources_list:
            logging.warning("NewsAPI.ai: No sources configured. Returning empty list.") # Use logging.warning
            return []

        params = {
            "action": "getArticles",
            "query": {
                "$query": {
                    "forceMaxDataTimeWindow": 31,
                    "categoryUri": "dmoz/News"
                },
                "$filter": {
                    "is" : "en"
                }
            },
            "resultType": "articles",
            "articlesIncludeSource": True,
            "articlesIncludeArticleCategories": True,
            "articlesIncludeConceptRates": True,
            "articlesIncludeConcepts": True,
            "articlesIncludeTitle": True,
            "articlesIncludeBody": True,
            "articlesIncludeDate": True,
            "articlesPage": 1,
            "articlesCount": 100, # Fetch up to 100 articles per request
            "apiKey": self.api_key
        }

        data = self._fetch_data(params)
        articles = []
        if data and 'articles' in data and 'results' in data['articles']:
            articles = data['articles']['results']
        return articles

    def _transform_article(self, article: Dict) -> Optional[Dict]:
        published_at = parse_and_validate_published_date(article.get("date")) # Use common helper

        return {
            "title": article.get("title"),
            "description": article.get("body"),
            "url": article.get("url"),
            "image_url": article.get("image"),
            "published_at": published_at,
            "source_name": article.get("source", {}).get("title"),
            "source_url": article.get("source", {}).get("uri"),
            "language": article.get("lang"),
            "full_content": article.get("body"),
            "authors": [],
            "tickers": [],
            "topics": [cat['name'] for cat in article.get("categories", []) if 'name' in cat]
        }

class TheNewsAPICollector(BaseCollector):
    """Collector for TheNewsAPI.com."""
    def __init__(self):
        super().__init__(THENEWSAPI_API_KEY, THENEWSAPI_BASE_URL, NEWS_FILE_THENEWSAPI)

    def fetch_articles(self) -> List[Dict]:
        sources_list = load_sources_from_file(API_SOURCES_FILE)
        if not sources_list:
            logging.warning("TheNewsAPI: No sources configured. Returning empty list.") # Use logging.warning
            return []
        
        params = {
            "api_token": self.api_key,
            "language": "en",
            "limit": 100,
            "search": "",
        }
        data = self._fetch_data(params)
        articles = []
        if data and 'data' in data:
            articles = data['data']
        return articles

    def _transform_article(self, article: Dict) -> Optional[Dict]:
        published_at = parse_and_validate_published_date(article.get("published_at")) # Use common helper

        return {
            "title": article.get("title"),
            "description": article.get("snippet"),
            "url": article.get("url"),
            "image_url": article.get("image_url"),
            "published_at": published_at,
            "source_name": article.get("source"),
            "source_url": article.get("url"),
            "language": article.get("language"),
            "full_content": article.get("description"),
            "authors": article.get("authors", []),
            "tickers": [],
            "topics": []
        }

class NewsDataCollector(BaseCollector):
    """Collector for NewsData.io."""
    def __init__(self):
        super().__init__(NEWSDATA_API_KEY, NEWSDATA_BASE_URL, NEWS_FILE_NEWSDATA)

    def fetch_articles(self) -> List[Dict]:
        sources_list = load_sources_from_file(API_SOURCES_FILE)
        if not sources_list:
            logging.warning("NewsData.io: No sources configured. Returning empty list.") # Use logging.warning
            return []

        params = {
            "apikey": self.api_key,
            "language": "en",
            "q": "world news",
            "size": 10,
        }
        data = self._fetch_data(params)
        articles = []
        if data and 'results' in data:
            articles = data['results']
        return articles

    def _transform_article(self, article: Dict) -> Optional[Dict]:
        published_at = parse_and_validate_published_date(article.get("pubDate")) # Use common helper

        return {
            "title": article.get("title"),
            "description": article.get("description"),
            "url": article.get("link"),
            "image_url": article.get("image_url"),
            "published_at": published_at,
            "source_name": article.get("source_id"),
            "source_url": article.get("source_url"),
            "language": article.get("language"),
            "full_content": article.get("content"),
            "authors": article.get("creator", []),
            "tickers": [],
            "topics": article.get("category", [])
        }

class TiingoCollector(BaseCollector):
    """Collector for Tiingo (Financial News).
    Tiingo API focuses on financial news and does not use a domains/sources file like general news APIs.
    """
    def __init__(self):
        super().__init__(TIINGO_API_KEY, TIINGO_BASE_URL, NEWS_FILE_TIINGO)

    def fetch_articles(self) -> List[Dict]:
        params = {
            "token": self.api_key,
            "limit": 100,
        }
        data = self._fetch_data(params)
        return data if isinstance(data, list) else []

    def _transform_article(self, article: Dict) -> Optional[Dict]:
        published_at = parse_and_validate_published_date(article.get("publishedDate")) # Use common helper

        return {
            "title": article.get("title"),
            "description": article.get("description"),
            "url": article.get("url"),
            "image_url": None,
            "published_at": published_at,
            "source_name": article.get("source"),
            "source_url": article.get("url"),
            "language": 'en',
            "full_content": article.get("articleBody"),
            "authors": article.get("authors", []),
            "tickers": article.get("tags", []),
            "topics": []
        }

class AlphaVantageCollector(BaseCollector):
    """Collector for AlphaVantage Market News and Sentiment.
    This API provides financial news and sentiment data, covering stocks, cryptocurrencies, and forex.
    """
    def __init__(self):
        super().__init__(ALPHA_VANTAGE_API_KEY, ALPHA_VANTAGE_BASE_URL, NEWS_FILE_ALPHA_VANTAGE)

    def fetch_articles(self) -> List[Dict]:
        params = {
            "function": "NEWS_SENTIMENT",
            "limit": 100,
            "apikey": self.api_key,
        }
        data = self._fetch_data(params)
        articles = []
        if data and 'feed' in data:
            articles = data['feed']
        return articles

    def _transform_article(self, article: Dict) -> Optional[Dict]:
        # Use common helper with explicit format for AlphaVantage's specific date format
        published_at = parse_and_validate_published_date(article.get("time_published", ""), '%Y%m%dT%H%M%S')

        # Safe extraction with type checking
        authors = []
        for author in article.get("authors", []):
            if isinstance(author, dict) and author.get("name"):
                authors.append(author.get("name"))
            elif isinstance(author, str):
                authors.append(author)
        
        tickers = []
        for item in article.get("tickers_sentiment", []):
            if isinstance(item, dict) and item.get("ticker"):
                tickers.append(item.get("ticker"))
            elif isinstance(item, str):
                tickers.append(item)
        
        topics = []
        for item in article.get("topics", []):
            if isinstance(item, dict) and item.get("topic"):
                topics.append(item.get("topic"))
            elif isinstance(item, str):
                topics.append(item)

        return {
            "title": article.get("title"),
            "description": article.get("summary"), # Changed to summary based on observation
            "url": article.get("url"),
            "image_url": article.get("banner_image"),
            "published_at": published_at,
            "source_name": article.get("source"),
            "source_url": article.get("source_domain"),
            "language": article.get("language"),
            "full_content": article.get("content"),
            "authors": authors,
            "tickers": tickers,
            "topics": topics
        } 