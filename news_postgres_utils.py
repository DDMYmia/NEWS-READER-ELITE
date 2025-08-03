"""
news_postgres_utils.py

This module provides utility functions for interacting with the PostgreSQL database.
It handles database connection, table creation, article insertion with deduplication,
and retrieval of articles and statistics.

Functions:
- get_db_connection: Establishes a connection to the PostgreSQL database.
- create_tables: Creates necessary tables (e.g., 'articles') if they don't exist.
- insert_articles_simple: Inserts articles into the database, handling URL-based deduplication.
- save_articles_to_json_simple: Saves articles to a local JSON file.
- save_articles_simple: A high-level function to save articles to both PostgreSQL, MongoDB, and JSON.
- get_total_articles_count: Retrieves the total number of articles in the PostgreSQL database.
- get_deduplication_stats: Provides deduplication statistics from the PostgreSQL database.
- get_news: Fetches news articles from the database with pagination.

Dependencies:
- psycopg: PostgreSQL adapter for Python.
- python-dotenv: For loading environment variables.
- news_mongo_utils: For saving articles to MongoDB.

Author: Gemini AI Assistant
Last updated: 2024-07-30
"""

import os
import json
import logging
import psycopg
from typing import List, Dict, Tuple, Any
from datetime import datetime

# Load environment variables from .env file
from dotenv import load_dotenv
# Removed redundant load_dotenv() as it's handled in start_app.py
# load_dotenv()

# Import MongoDB utility for parallel saving
from news_mongo_utils import save_articles_to_mongo

def get_db_connection() -> psycopg.Connection | None:
    """Establishes and returns a connection to the PostgreSQL database.

    Returns:
        psycopg.Connection | None: A psycopg connection object if successful, None otherwise.
    """
    try:
        conn_str = f"dbname={os.getenv('POSTGRES_DB')} user={os.getenv('POSTGRES_USER')} password={os.getenv('POSTGRES_PASSWORD')} host={os.getenv('POSTGRES_HOST', 'localhost')} port={os.getenv('POSTGRES_PORT', '5432')}"
        conn = psycopg.connect(conn_str)
        logging.info("PostgreSQL connection successful.")
        return conn
    except psycopg.OperationalError as e:
        logging.error(f"Database connection failed: {e}")
        return None

def create_tables():
    """Creates the 'articles' table in the PostgreSQL database if it does not already exist.

    The table schema includes fields for article metadata, with 'url' as a unique constraint
    to prevent duplicate entries.
    """
    with get_db_connection() as conn:
        if not conn:
            return
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS articles (
                        id SERIAL PRIMARY KEY,
                        title TEXT,
                        description TEXT,
                        url TEXT UNIQUE,
                        image_url TEXT,
                        published_at TIMESTAMPTZ,
                        source_name TEXT,
                        source_url TEXT,
                        language TEXT,
                        full_content TEXT,
                        authors TEXT[],
                        tickers TEXT[],
                        topics TEXT[], -- Renamed from tags to topics for consistency
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                conn.commit()
                logging.info("Table 'articles' created or already exists.")
        except psycopg.Error as e:
            logging.error(f"Failed to create tables: {e}")
            conn.rollback()


def insert_articles_simple(articles: List[Dict[str, Any]]) -> Tuple[int, List[Dict[str, Any]]]:
    """Inserts a list of articles into the PostgreSQL database, skipping duplicates based on URL.

    Args:
        articles (List[Dict[str, Any]]): A list of article dictionaries to insert.

    Returns:
        Tuple[int, List[Dict[str, Any]]]: A tuple containing:
            - The number of articles successfully inserted.
            - A list of the articles that were successfully inserted (after deduplication).
    """
    if not articles:
        return 0, []

    with get_db_connection() as conn:
        if not conn:
            return 0, []

        inserted_count = 0
        inserted_articles = []
        
        insert_query = """
        INSERT INTO articles (title, description, url, image_url, published_at, 
                            source_name, source_url, language, full_content, authors, tickers, topics) -- Updated to topics
        VALUES (%(title)s, %(description)s, %(url)s, %(image_url)s, %(published_at)s, 
                %(source_name)s, %(source_url)s, %(language)s, %(full_content)s, 
                ARRAY[%(authors)s], ARRAY[%(tickers)s], ARRAY[%(topics)s]) -- Updated to topics
        ON CONFLICT (url) DO NOTHING
        RETURNING id;
        """
        
        try:
            with conn.cursor() as cur:
                for article in articles:
                    # psycopg3 can directly adapt dicts to SQL using %(key)s placeholders
                    # Ensure authors, tickers, topics are lists (PostgreSQL array type expects lists/tuples)
                    authors_list = article.get('authors', [])
                    if not isinstance(authors_list, list): authors_list = [authors_list]

                    tickers_list = article.get('tickers', [])
                    if not isinstance(tickers_list, list): tickers_list = [tickers_list]

                    topics_list = article.get('topics', []) # Changed from tags to topics
                    if not isinstance(topics_list, list): topics_list = [topics_list]

                    params = {
                        'title': article.get('title'),
                        'description': article.get('description'),
                        'url': article.get('url'),
                        'image_url': article.get('image_url'),
                        'published_at': article.get('published_at'),
                        'source_name': article.get('source_name'),
                        'source_url': article.get('source_url'),
                        'language': article.get('language'),
                        'full_content': article.get('full_content'),
                        'authors': authors_list,
                        'tickers': tickers_list,
                        'topics': topics_list # Changed from tags to topics
                    }
                    result = cur.execute(insert_query, params)
                    
                    if result.fetchone() is not None:
                        inserted_count += 1
                        inserted_articles.append(article)

                conn.commit()
                logging.info(f"Successfully inserted {inserted_count} new articles into PostgreSQL.")

        except psycopg.Error as e:
            logging.error(f"PostgreSQL insertion failed: {e}")
            conn.rollback()
            return 0, []
            
        return inserted_count, inserted_articles

def save_articles_to_json_simple(articles: List[Dict], filename: str) -> int:
    """Saves a list of articles to a specified JSON file.

    This function appends new articles to existing ones in the file and overwrites the file.
    It handles the conversion of `datetime` objects to ISO format for JSON serialization.

    Args:
        articles (List[Dict]): A list of article dictionaries to save.
        filename (str): The path to the JSON file.

    Returns:
        int: The number of articles written to the JSON file (this count is for the new articles added in this batch).
    """
    if not articles:
        return 0
        
    try:
        existing_articles = []
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    existing_articles = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                existing_articles = []
        
        # Add new articles (assuming deduplication is handled upstream or by database)
        existing_articles.extend(articles)
        
        # Convert datetime objects to ISO format strings for JSON serialization
        for article in existing_articles:
            if 'published_at' in article and isinstance(article['published_at'], datetime):
                article['published_at'] = article['published_at'].isoformat()
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(existing_articles, f, ensure_ascii=False, indent=2)
        
        return len(articles)
        
    except Exception as e:
        logging.error(f"JSON save failed: {e}")
        return 0

def save_articles_simple(articles: List[Dict], json_filename: str) -> Dict[str, Any]:
    """Saves articles to PostgreSQL, MongoDB, and a local JSON file.

    This is a wrapper function that orchestrates saving articles to all configured storage types.

    Args:
        articles (List[Dict]): A list of article dictionaries to save.
        json_filename (str): The specific JSON file path to save articles to.

    Returns:
        Dict[str, Any]: A dictionary containing counts of articles saved to each storage type
                        ('db_count', 'json_count', 'mongo_count') and a list of newly inserted articles in DB.
    """
    if not articles:
        return {'db_count': 0, 'json_count': 0, 'mongo_count': 0, 'new_articles': []}
    
    # Save to PostgreSQL
    db_count, new_db_articles = insert_articles_simple(articles)
    
    # Save to JSON file
    json_count = save_articles_to_json_simple(articles, json_filename)
    
    # Save to MongoDB backup
    mongo_count = save_articles_to_mongo(articles)
    
    return {'db_count': db_count, 'json_count': json_count, 'mongo_count': mongo_count, 'new_articles': new_db_articles}

def get_total_articles_count() -> int:
    """Retrieves the total number of articles stored in the PostgreSQL database.

    Returns:
        int: The total count of articles, or 0 if an error occurs.
    """
    try: # Added try-except block
        with get_db_connection() as conn:
            if not conn:
                return 0
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM articles")
                count = cur.fetchone()[0]
                return count
    except psycopg.Error as e: # Catch psycopg errors
        logging.error(f"Failed to get article count from PostgreSQL: {e}")
        return 0

def get_deduplication_stats() -> Dict[str, int]:
    """Retrieves deduplication statistics from the PostgreSQL database.

    This function provides insights into the uniqueness of titles and URLs stored.

    Returns:
        Dict[str, int]: A dictionary containing total articles, unique titles, unique URLs,
                        and the count of duplicate titles (based on normalization).
                        Returns an empty dictionary if an error occurs.
    """
    try: # Added try-except block
        with get_db_connection() as conn:
            if not conn:
                return {}
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM articles")
                total_count = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(DISTINCT title) FROM articles WHERE title IS NOT NULL")
                unique_titles = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(DISTINCT url) FROM articles WHERE url IS NOT NULL")
                unique_urls = cur.fetchone()[0]
                
                # Re-calculate duplicate titles based on the current articles in DB
                cur.execute("SELECT COUNT(*) FROM (SELECT title FROM articles WHERE title IS NOT NULL GROUP BY title HAVING COUNT(*) > 1) AS duplicate_titles;")
                # Fetchone can return None if no rows are found, handle this case
                duplicate_titles_count = cur.fetchone()[0] if cur.rowcount > 0 else 0 

                return {
                    'total_articles': total_count,
                    'unique_titles': unique_titles,
                    'unique_urls': unique_urls,
                    'duplicate_titles': duplicate_titles_count # Now correctly calculated
                }
    except psycopg.Error as e: # Catch psycopg errors
        logging.error(f"Failed to get deduplication stats from PostgreSQL: {e}")
        return {}

def get_news(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """Fetches news articles from the PostgreSQL database with pagination.

    Args:
        limit (int): The maximum number of articles to fetch. Defaults to 100.
        offset (int): The number of articles to skip from the beginning. Defaults to 0.

    Returns:
        List[Dict[str, Any]]: A list of article dictionaries, with `published_at` converted to ISO format strings.
    """
    with get_db_connection() as conn:
        if not conn:
            return []
        try:
            conn.row_factory = psycopg.rows.dict_row # Return rows as dictionaries
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, title, description, url, image_url, published_at, 
                           source_name, source_url, language, full_content, 
                           authors, tickers, topics, created_at -- Updated to topics
                    FROM articles
                    WHERE published_at <= DATE_TRUNC('day', NOW()) + INTERVAL '2 day' - INTERVAL '1 microsecond'
                    ORDER BY published_at DESC, id DESC
                    LIMIT %s OFFSET %s
                """, (limit, offset))
                
                articles = cur.fetchall()
                
                # Convert datetime objects to ISO 8601 strings for JSON serialization
                for article in articles:
                    for key, value in article.items():
                        if isinstance(value, datetime):
                            article[key] = value.isoformat()
                return articles
        except psycopg.Error as e:
            logging.error(f"Failed to fetch news from PostgreSQL: {e}")
            return []