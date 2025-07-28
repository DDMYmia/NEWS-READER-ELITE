"""
news_mongo_utils.py

This module provides utility functions for interacting with a MongoDB database.
It handles MongoDB connection, saving articles with deduplication (upsert),
and retrieving article counts from the MongoDB collection.

Functions:
- get_mongo_client: Establishes a connection to the MongoDB server.
- save_articles_to_mongo: Saves a list of articles to MongoDB using bulk upserts.
- get_total_articles_count_mongo: Retrieves the total number of articles in the MongoDB collection.

Dependencies:
- pymongo: MongoDB driver for Python.
- python-dotenv: For loading environment variables.

Usage:
Used by `news_db_utils.py` for parallel article storage and by `app/main.py` for fetching statistics.

Author: Gemini AI Assistant
Last updated: 2024-07-30
"""

import os
import logging
from typing import List, Dict, Any
from pymongo import MongoClient, UpdateOne
from pymongo.errors import ConnectionFailure, OperationFailure
from datetime import datetime

# Load environment variables from .env file
from dotenv import load_dotenv
# Removed redundant load_dotenv() as it's handled in start_app.py
# load_dotenv()

# --- MongoDB Configuration ---
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "news_db_backup")
MONGO_COLLECTION_NAME = "articles" # Collection name for storing news articles

def get_mongo_client() -> MongoClient | None:
    """Establishes and returns a connection to the MongoDB server."""
    try:
        client = MongoClient(host=MONGO_HOST, port=MONGO_PORT, serverSelectionTimeoutMS=5000)
        # The ismaster command is cheap and does not require auth.
        client.admin.command('ismaster')
        logging.info("MongoDB connection successful.")
        return client
    except ConnectionFailure as e:
        logging.error(f"MongoDB connection failed: {e}")
        return None

def save_articles_to_mongo(articles: List[Dict[str, Any]]) -> int:
    """
    Saves a list of articles to MongoDB using bulk upserts to prevent duplicates.
    Returns the number of articles newly inserted or modified.
    """
    if not articles:
        return 0

    client = get_mongo_client()
    if not client:
        return 0

    try:
        db = client[MONGO_DB_NAME]
        collection = db[MONGO_COLLECTION_NAME]

        # Prepare bulk operations
        bulk_operations = []
        for article in articles:
            # Use URL as the unique identifier for an article
            filter_query = {"url": article.get("url")}
            
            # Prepare the update document
            update_document = {"$set": article}
            
            # Add an upsert operation to the list
            # If a document with the URL exists, it's updated; otherwise, it's inserted.
            bulk_operations.append(UpdateOne(filter_query, update_document, upsert=True))

        if not bulk_operations:
            return 0

        # Execute bulk write
        result = collection.bulk_write(bulk_operations)
        
        # result.upserted_count are new documents, result.modified_count are existing ones
        saved_count = result.upserted_count + result.modified_count
        logging.info(f"MongoDB: Saved {saved_count} articles ({result.upserted_count} new, {result.modified_count} updated).")
        return saved_count

    except OperationFailure as e:
        logging.error(f"MongoDB bulk write operation failed: {e}")
        return 0
    finally:
        if client:
            client.close()

def get_total_articles_count_mongo() -> int:
    """Get total number of articles in the MongoDB collection."""
    client = get_mongo_client()
    if not client:
        return 0
    
    try:
        db = client[MONGO_DB_NAME]
        collection = db[MONGO_COLLECTION_NAME]
        count = collection.count_documents({})
        return count
    except OperationFailure as e:
        logging.error(f"Failed to get article count from MongoDB: {e}")
        return 0
    finally:
        if client:
            client.close() 