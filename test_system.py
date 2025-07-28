#!/usr/bin/env python3
"""
News Reader Elite - System Test Script

This module provides comprehensive testing for all API endpoints and functionality
of the News Reader Elite system. It tests health checks, statistics, news retrieval,
source management, and collection processes.

Main Functions:
- test_health: Tests the health check endpoint
- test_stats: Tests the statistics endpoint
- test_news: Tests the news retrieval endpoint
- test_sources: Tests the sources endpoint
- test_collection: Tests the collection endpoints
- main: Orchestrates all tests and provides summary results

Dependencies:
- requests: For making HTTP requests to the API endpoints
- logging: For consistent logging output

Usage:
Run this script to test all system functionality:
    python test_system.py

Author: Gemini AI Assistant
Last updated: 2024-07-30
"""

import requests
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Configure logging for test output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Configuration
BASE_URL = "http://localhost:8000"
REQUEST_TIMEOUT = 10

def test_health() -> bool:
    """
    Test the health check endpoint.
    
    Returns:
        bool: True if health check passes, False otherwise
    """
    logging.info("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            logging.info(f"✅ Health check passed: {data['status']}")
            return True
        else:
            logging.error(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"❌ Health check error: {e}")
        return False

def test_stats() -> bool:
    """
    Test the statistics endpoint.
    
    Returns:
        bool: True if statistics test passes, False otherwise
    """
    logging.info("📊 Testing statistics...")
    try:
        response = requests.get(f"{BASE_URL}/api/stats", timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                logging.info(f"✅ Stats: DB={data['database_count']}, Sources={len(data['source_stats'])}")
                return True
            else:
                logging.error(f"❌ Stats failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            logging.error(f"❌ Stats request failed: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"❌ Stats error: {e}")
        return False

def test_news() -> bool:
    """
    Test the news endpoint.
    
    Returns:
        bool: True if news test passes, False otherwise
    """
    logging.info("📰 Testing news endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/news?limit=5", timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                logging.info(f"✅ News: {data['count']} articles retrieved")
                return True
            else:
                logging.error(f"❌ News failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            logging.error(f"❌ News request failed: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"❌ News error: {e}")
        return False

def test_sources() -> bool:
    """
    Test the sources endpoint.
    
    Returns:
        bool: True if sources test passes, False otherwise
    """
    logging.info("🔗 Testing sources...")
    try:
        response = requests.get(f"{BASE_URL}/api/sources", timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                api_count = len(data['sources'].get('api', []))
                rss_count = len(data['sources'].get('rss', []))
                logging.info(f"✅ Sources: API={api_count}, RSS={rss_count}")
                return True
            else:
                logging.error(f"❌ Sources failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            logging.error(f"❌ Sources request failed: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"❌ Sources error: {e}")
        return False

def test_collection(collection_type: str) -> bool:
    """
    Test the collection endpoint for a specific collection type.
    
    Args:
        collection_type (str): Type of collection to test ('api' or 'rss')
        
    Returns:
        bool: True if collection test passes, False otherwise
    """
    logging.info(f"🔄 Testing {collection_type} collection...")
    try:
        response = requests.post(f"{BASE_URL}/api/collect/{collection_type}", timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                logging.info(f"✅ {collection_type.upper()} collection completed")
                return True
            else:
                logging.error(f"❌ {collection_type} collection failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            logging.error(f"❌ {collection_type} collection request failed: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"❌ {collection_type} collection error: {e}")
        return False

def run_tests() -> Tuple[int, int, List[Tuple[str, bool]]]:
    """
    Run all system tests and return results.
    
    Returns:
        Tuple[int, int, List[Tuple[str, bool]]]: (passed_count, total_count, test_results)
    """
    tests = [
        ("Health Check", test_health),
        ("Statistics", test_stats),
        ("News Articles", test_news),
        ("Sources", test_sources),
    ]
    
    passed = 0
    total = len(tests)
    results = []
    
    for test_name, test_func in tests:
        logging.info(f"\n{test_name}:")
        result = test_func()
        results.append((test_name, result))
        if result:
            passed += 1
        time.sleep(1)  # Brief pause between tests
    
    return passed, total, results

def main():
    """
    Main function to run all system tests and display results.
    """
    logging.info("🚀 News Reader Elite - System Test")
    logging.info("=" * 50)
    
    # Run all tests
    passed, total, results = run_tests()
    
    # Display summary
    logging.info("\n" + "=" * 50)
    logging.info(f"📈 Test Results: {passed}/{total} passed")
    
    if passed == total:
        logging.info("🎉 All tests passed! System is working correctly.")
    else:
        logging.warning("⚠️  Some tests failed. Please check the system.")
    
    # Display access information
    logging.info(f"\n🌐 Frontend: http://localhost:3000")
    logging.info(f"🔧 API: http://localhost:8000")
    logging.info(f"📖 API Docs: http://localhost:8000/docs")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 