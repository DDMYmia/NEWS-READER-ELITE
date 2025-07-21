"""
news_api_settings.py

Unified API collectors for multiple news sources (NewsAPI.ai, TheNewsAPI, NewsData.io, Tiingo).

Main Classes:
- NewsAPIAICollector: Collector for NewsAPI.ai (Event Registry)
- TheNewsAPICollector: Collector for TheNewsAPI
- NewsDataCollector: Collector for NewsData.io
- TiingoCollector: Collector for Tiingo News API

Features:
- Source filtering by domain or source name
- Deduplication based on normalized title and URL
- Unified output format for all collectors
- Database integration for persistent storage and deduplication

Dependencies:
- requests
- eventregistry
- bs4 (BeautifulSoup)
- dotenv
- news_db_utils (local database utility module)

Usage:
Import the required collector classes in news_api_collector.py for scheduled or manual news collection.

Author: TODO
Last updated: TODO
"""
import os
import json
import logging
import requests
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple, Set
from eventregistry import *
from dotenv import load_dotenv
import news_db_utils

# Load environment variables
load_dotenv()

def normalize_title(title: str) -> str:
    """Normalize title for comparison by removing special characters and converting to lowercase."""
    if not title:
        return ""
    # Remove special characters, extra spaces, convert to lowercase
    normalized = re.sub(r'[^\w\s]', '', title.lower())
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized

def get_all_existing_articles() -> Tuple[Set[str], Set[str]]:
    """Get all existing normalized titles and URLs from all JSON files."""
    json_files = [
        'outputs/02_newsapi_ai.json',
        'outputs/03_thenewsapi.json',
        'outputs/04_newsdata.json',
        'outputs/05_tiingo.json'
    ]
    
    all_titles = set()
    all_urls = set()
    
    for file_path in json_files:
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    articles = json.load(f)
                    for article in articles:
                        title = article.get('title', '')
                        url = article.get('url', '')
                        if title:
                            all_titles.add(normalize_title(title))
                        if url:
                            all_urls.add(url)
        except Exception as e:
            logging.warning(f"Failed to read {file_path}: {e}")
    
    return all_titles, all_urls

def deduplicate_articles(articles: List[Dict]) -> Tuple[List[Dict], int]:
    """Deduplicate articles based on normalized title and URL. Returns (unique_articles, duplicate_count)."""
    if not articles:
        return [], 0
    
    # Get existing articles from all files
    existing_titles, existing_urls = get_all_existing_articles()
    
    # Get existing articles from database
    db_titles, db_urls = get_db_existing_articles()
    existing_titles.update(db_titles)
    existing_urls.update(db_urls)
    
    # Deduplicate articles
    unique_articles = []
    seen_titles = set()
    seen_urls = set()
    duplicate_count = 0
    
    for article in articles:
        title = article.get('title', '')
        url = article.get('url', '')
        normalized_title = normalize_title(title)
        
        # Check if duplicate
        is_duplicate = False
        
        # Skip if URL already exists anywhere
        if url in existing_urls or url in seen_urls:
            is_duplicate = True
        
        # Skip if normalized title already exists anywhere
        if normalized_title in existing_titles or normalized_title in seen_titles:
            is_duplicate = True
        
        if is_duplicate:
            duplicate_count += 1
        else:
            # Add to unique articles
            unique_articles.append(article)
            seen_titles.add(normalized_title)
            seen_urls.add(url)
    
    return unique_articles, duplicate_count

def get_db_existing_articles() -> Tuple[Set[str], Set[str]]:
    """Get existing normalized titles and URLs from database."""
    connection = news_db_utils.get_db_connection()
    if not connection:
        return set(), set()
    
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT title, url FROM articles")
        existing_data = cursor.fetchall()
        existing_titles = {normalize_title(row[0]) for row in existing_data if row[0]}
        existing_urls = {row[1] for row in existing_data if row[1]}
        cursor.close()
        connection.close()
        return existing_titles, existing_urls
    except Exception as e:
        logging.warning(f"Failed to get database existing data: {e}")
        if connection:
            connection.close()
        return set(), set()

class NewsAPIAICollector:
    """Collector for NewsAPI.ai (Event Registry)"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("NEWSAPI_AI_API_KEY")
        if not self.api_key:
            raise ValueError("API key not provided. Please set NEWSAPI_AI_API_KEY environment variable.")
        self.er = EventRegistry(apiKey=self.api_key)

    def _transform_article(self, article: Dict) -> Dict:
        """Transform Event Registry article data into unified format."""
        return {
            "title": article.get("title"),
            "description": article.get("body"),
            "url": article.get("url"),
            "image_url": article.get("image"),
            "published_at": article.get("dateTime"),
            "source_name": article.get("source", {}).get("title"),
            "source_url": article.get("source", {}).get("uri"),
            "language": article.get("lang"),
            "full_content": article.get("body"),
            "authors": [author.get("name") for author in article.get("authors", []) if author.get("name")]
        }

    def fetch_articles(
        self,
        lang: str = "en",
        max_items: int = 10,
        source_uri: Optional[List[str]] = None
    ) -> Tuple[List[Dict], Optional[str], int]:
        """Fetch news articles from NewsAPI.ai. Returns (articles, error_message, duplicate_count)."""
        query_params = {
            "dataType": ["news"],
            "lang": lang
        }
        if source_uri:
            query_params["sourceUri"] = QueryItems.OR(source_uri)

        requested_result = RequestArticlesInfo(returnInfo=ReturnInfo(articleInfo=ArticleInfoFlags(bodyLen=-1)))
        query_params["requestedResult"] = requested_result

        q = QueryArticlesIter(**query_params)

        articles = []
        try:
            for art in q.execQuery(self.er, sortBy="date", maxItems=max_items):
                articles.append(self._transform_article(art))
            
            # Deduplicate articles before returning
            unique_articles, duplicate_count = deduplicate_articles(articles)
            return unique_articles, None, duplicate_count
        except Exception as e:
            error_msg = str(e)
            if "quota" in error_msg.lower() or "limit" in error_msg.lower():
                return [], "API quota exceeded", 0
            elif "unauthorized" in error_msg.lower() or "invalid" in error_msg.lower():
                return [], "Invalid API key", 0
            else:
                return [], f"API error: {error_msg}", 0

    def save_articles(self, articles):
        """Save articles to database and JSON file."""
        result = news_db_utils.save_articles_simple(articles, 'outputs/02_newsapi_ai.json')
        return result


class TheNewsAPICollector:
    """Collector for TheNewsAPI"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('THENEWSAPI_API_KEY')
        if not self.api_key:
            raise ValueError("THENEWSAPI_API_KEY not set. Please set your API key in the .env file.")

    def _transform_article(self, article: dict) -> dict:
        """Transform TheNewsAPI article data into unified format."""
        return {
            "title": article.get("title"),
            "description": article.get("snippet"),
            "url": article.get("url"),
            "image_url": article.get("image_url"),
            "published_at": article.get("published_at"),
            "source_name": article.get("source"),
            "source_url": article.get("url"),
            "language": article.get("language"),
            "full_content": article.get("full_content"),
            "authors": article.get("authors")
        }

    def _get_full_article(self, url):
        """Fetch and parse full article content from URL."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'lxml')
            paragraphs = soup.find_all('p')
            full_text = '\n'.join(p.get_text() for p in paragraphs)
            return full_text
        except requests.exceptions.RequestException as e:
            return f"Could not fetch article: {e}"
        except Exception as e:
            return f"Error parsing article: {e}"

    def fetch_articles(self, domains=None, max_items: int = 3) -> Tuple[List[Dict], Optional[str], int]:
        """Fetch news articles from TheNewsAPI. Returns (articles, error_message, duplicate_count)."""
        params = {
            'api_token': self.api_key,
            'language': 'en',
            'limit': max_items,
        }
        if domains:
            params['domains'] = ','.join(domains)
        
        try:
            response = requests.get('https://api.thenewsapi.com/v1/news/all', params=params)
            
            # Check for HTTP errors first
            if response.status_code == 402:
                return [], "API quota exceeded (402 Payment Required)", 0
            elif response.status_code == 401:
                return [], "Invalid API key (401 Unauthorized)", 0
            elif response.status_code == 429:
                return [], "Rate limit exceeded (429 Too Many Requests)", 0
            elif response.status_code != 200:
                return [], f"HTTP error {response.status_code}: {response.text}", 0
            
            response.raise_for_status()
            news_data = response.json()
            transformed_articles = []
            
            for article in news_data.get('data', []):
                full_content = self._get_full_article(article['url'])
                article['full_content'] = full_content
                transformed_articles.append(self._transform_article(article))

            # Deduplicate articles before returning
            unique_articles, duplicate_count = deduplicate_articles(transformed_articles)
            return unique_articles, None, duplicate_count

        except requests.exceptions.RequestException as e:
            return [], f"Network error: {e}", 0
        except Exception as e:
            return [], f"Unexpected error: {e}", 0

    def save_articles(self, articles):
        """Save articles to database and JSON file."""
        result = news_db_utils.save_articles_simple(articles, 'outputs/03_thenewsapi.json')
        return result


class NewsDataCollector:
    """Collector for NewsData.io"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("NEWSDATA_API_KEY")
        if not self.api_key:
            raise ValueError("API key not provided. Please set NEWSDATA_API_KEY environment variable.")
        self.base_url = "https://newsdata.io/api/1/news"

    def _transform_article(self, article: Dict) -> Dict:
        """Transform NewsData.io article data into unified format."""
        return {
            "title": article.get("title"),
            "description": article.get("description"),
            "url": article.get("link"),
            "image_url": article.get("image_url"),
            "published_at": article.get("pubDate"),
            "source_name": article.get("source_id"),
            "source_url": article.get("source_url"),
            "language": article.get("language"),
            "full_content": article.get("content"),
            "authors": article.get("creator")
        }

    def fetch_articles(
        self,
        query: str = "",
        lang: str = "en",
        max_items: int = 10,
        domain: Optional[List[str]] = None,
        country: Optional[str] = None,
        category: Optional[str] = None,
        all_sources: Optional[List[str]] = None
    ) -> Tuple[List[Dict], Optional[str], int]:
        """Fetch news articles from NewsData.io. Returns (articles, error_message, duplicate_count)."""
        params = {
            "apikey": self.api_key,
            "language": lang,
            "size": min(max_items, 50)
        }
        
        if query:
            params["q"] = query
        if domain:
            params["domain"] = ",".join(domain)
        if country:
            params["country"] = country
        if category:
            params["category"] = category

        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            
            # Check for HTTP errors first
            if response.status_code == 402:
                return [], "API quota exceeded", 0
            elif response.status_code == 401:
                return [], "Invalid API key (401 Unauthorized)", 0
            elif response.status_code == 429:
                return [], "Rate limit exceeded (429 Too Many Requests)", 0
            elif response.status_code != 200:
                return [], f"HTTP error {response.status_code}: {response.text}", 0
            
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "success":
                error_msg = data.get("message", "Unknown API error")
                if "quota" in error_msg.lower():
                    return [], "API quota exceeded", 0
                else:
                    return [], f"API error: {error_msg}", 0
            
            articles = []
            for article in data.get("results", [])[:max_items]:
                transformed_article = self._transform_article(article)
                
                # If domain filtering is specified, check if article is from configured sources
                if domain or all_sources:
                    article_source = transformed_article.get("source_name", "").lower()
                    article_url = transformed_article.get("url", "").lower()
                    
                    # Use all_sources for stricter filtering (if provided)
                    filter_sources = all_sources if all_sources else domain
                    
                    # Check if source is in the configured list
                    is_allowed_source = False
                    for allowed_domain in filter_sources:
                        if (allowed_domain.lower() in article_source or 
                            allowed_domain.lower() in article_url):
                            is_allowed_source = True
                            break
                    
                    # If not in the allowed sources list, skip this article
                    if not is_allowed_source:
                        continue
                
                articles.append(transformed_article)
            
            # Deduplicate articles before returning
            unique_articles, duplicate_count = deduplicate_articles(articles)
            return unique_articles, None, duplicate_count

        except requests.exceptions.RequestException as e:
            return [], f"Network error: {e}", 0
        except Exception as e:
            return [], f"Unexpected error: {e}", 0

    def save_articles(self, articles):
        """Save articles to database and JSON file."""
        result = news_db_utils.save_articles_simple(articles, 'outputs/04_newsdata.json')
        return result


class TiingoCollector:
    """Collector for Tiingo News API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("TIINGO_API_KEY")
        if not self.api_key:
            raise ValueError("API key not provided. Please set TIINGO_API_KEY environment variable.")
        self.base_url = "https://api.tiingo.com/tiingo/news"

    def _transform_article(self, article: Dict) -> Dict:
        """Transform Tiingo article data into unified format."""
        return {
            "title": article.get("title"),
            "description": article.get("description"),
            "url": article.get("url"),
            "image_url": article.get("imageUrl"),
            "published_at": article.get("publishedDate"),
            "source_name": article.get("source"),
            "source_url": article.get("url"),
            "language": "en",  # Tiingo primarily provides English content
            "full_content": article.get("content"),
            "authors": article.get("authors"),
            "tickers": article.get("tickers", []),
            "tags": article.get("tags", [])
        }

    def fetch_articles(
        self,
        sources: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        max_items: int = 10,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Tuple[List[Dict], Optional[str], int]:
        """Fetch news articles from Tiingo. Returns (articles, error_message, duplicate_count)."""
        params = {
            "token": self.api_key,
            "limit": min(max_items, 100)  # Tiingo allows up to 100 articles per request
        }
        
        if sources:
            params["sources"] = ",".join(sources)
        if tags:
            params["tags"] = ",".join(tags)
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            
            # Check for HTTP errors first
            if response.status_code == 401:
                return [], "Invalid API key (401 Unauthorized)", 0
            elif response.status_code == 429:
                return [], "Rate limit exceeded (429 Too Many Requests)", 0
            elif response.status_code == 403:
                return [], "API quota exceeded (403 Forbidden)", 0
            elif response.status_code != 200:
                return [], f"HTTP error {response.status_code}: {response.text}", 0
            
            response.raise_for_status()
            articles_data = response.json()
            
            if not isinstance(articles_data, list):
                return [], f"Unexpected response format: {type(articles_data)}", 0
            
            articles = []
            for article in articles_data[:max_items]:
                articles.append(self._transform_article(article))
            
            # Deduplicate articles before returning
            unique_articles, duplicate_count = deduplicate_articles(articles)
            return unique_articles, None, duplicate_count

        except requests.exceptions.RequestException as e:
            return [], f"Network error: {e}", 0
        except Exception as e:
            return [], f"Unexpected error: {e}", 0

    def save_articles(self, articles):
        """Save articles to database and JSON file."""
        result = news_db_utils.save_articles_simple(articles, 'outputs/05_tiingo.json')
        return result


def load_sources_from_file(filepath='sources/01_api_sources.txt'):
    """Load news source domains from file."""
    try:
        with open(filepath, 'r') as f:
            sources = []
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    sources.append(line)
            return sources
    except FileNotFoundError:
        return [] 