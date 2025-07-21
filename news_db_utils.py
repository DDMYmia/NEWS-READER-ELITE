import os
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from typing import List, Dict

# Load environment variables
load_dotenv()

def get_db_connection():
    """Get PostgreSQL database connection."""
    try:
        connection = psycopg2.connect(
            host=os.environ.get('POSTGRES_HOST', 'localhost'),
            port=os.environ.get('POSTGRES_PORT', '5432'),
            database=os.environ.get('POSTGRES_DB', 'news_db'),
            user=os.environ.get('POSTGRES_USER', 'postgres'),
            password=os.environ.get('POSTGRES_PASSWORD', '')
        )
        return connection
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        return None

def insert_articles_simple(articles: List[Dict]) -> int:
    """Insert articles into PostgreSQL database (articles already deduplicated)."""
    if not articles:
        return 0
        
    connection = get_db_connection()
    if not connection:
        return 0
        
    try:
        cursor = connection.cursor()
        
        # Create table if not exists
        create_table_query = """
        CREATE TABLE IF NOT EXISTS articles (
            id SERIAL PRIMARY KEY,
            title TEXT,
            description TEXT,
            url TEXT UNIQUE,
            image_url TEXT,
            published_at TIMESTAMP,
            source_name TEXT,
            source_url TEXT,
            language TEXT,
            full_content TEXT,
            authors TEXT[],
            tickers TEXT[],
            tags TEXT[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute(create_table_query)
        
        # Insert articles (already deduplicated)
        insert_query = """
        INSERT INTO articles (title, description, url, image_url, published_at, 
                            source_name, source_url, language, full_content, authors, tickers, tags)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (url) DO NOTHING
        """
        
        inserted_count = 0
        for article in articles:
            try:
                cursor.execute(insert_query, (
                    article.get('title'),
                    article.get('description'),
                    article.get('url'),
                    article.get('image_url'),
                    article.get('published_at'),
                    article.get('source_name'),
                    article.get('source_url'),
                    article.get('language'),
                    article.get('full_content'),
                    article.get('authors', []),
                    article.get('tickers', []),
                    article.get('tags', [])
                ))
                
                if cursor.rowcount > 0:
                    inserted_count += 1
                    
            except Exception as e:
                logging.warning(f"Failed to insert article '{article.get('title', 'Unknown')}': {e}")
                continue
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return inserted_count
        
    except Exception as e:
        logging.error(f"Database operation failed: {e}")
        if connection:
            try:
                connection.rollback()
            except:
                pass
            connection.close()
        return 0

def save_articles_to_json_simple(articles: List[Dict], filename: str) -> int:
    """Save articles to JSON file (articles already deduplicated)."""
    if not articles:
        return 0
        
    try:
        # Load existing articles from current file
        existing_articles = []
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    existing_articles = json.load(f)
            except json.JSONDecodeError:
                existing_articles = []
        
        # Add new articles (already deduplicated)
        existing_articles.extend(articles)
        
        # Save to file
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(existing_articles, f, ensure_ascii=False, indent=2)
        
        return len(articles)
        
    except Exception as e:
        logging.error(f"JSON save failed: {e}")
        return 0

def save_articles_simple(articles: List[Dict], json_filename: str) -> Dict:
    """Save articles to both database and JSON file (articles already deduplicated)."""
    if not articles:
        return {'db_count': 0, 'json_count': 0}
    
    db_count = insert_articles_simple(articles)
    json_count = save_articles_to_json_simple(articles, json_filename)
    
    return {'db_count': db_count, 'json_count': json_count}

def get_total_articles_count() -> int:
    """Get total number of articles in database."""
    connection = get_db_connection()
    if not connection:
        return 0
        
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM articles")
        count = cursor.fetchone()[0]
        cursor.close()
        connection.close()
        return count
    except Exception as e:
        logging.error(f"Failed to get article count: {e}")
        if connection:
            connection.close()
        return 0

def get_deduplication_stats() -> Dict:
    """Get deduplication statistics."""
    connection = get_db_connection()
    if not connection:
        return {}
        
    try:
        cursor = connection.cursor()
        
        # Get total articles
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_count = cursor.fetchone()[0]
        
        # Get unique titles
        cursor.execute("SELECT COUNT(DISTINCT title) FROM articles WHERE title IS NOT NULL")
        unique_titles = cursor.fetchone()[0]
        
        # Get unique URLs
        cursor.execute("SELECT COUNT(DISTINCT url) FROM articles WHERE url IS NOT NULL")
        unique_urls = cursor.fetchone()[0]
        
        cursor.close()
        connection.close()
        
        return {
            'total_articles': total_count,
            'unique_titles': unique_titles,
            'unique_urls': unique_urls,
            'duplicate_titles': total_count - unique_titles if total_count > unique_titles else 0
        }
        
    except Exception as e:
        logging.error(f"Failed to get deduplication stats: {e}")
        if connection:
            connection.close()
        return {}