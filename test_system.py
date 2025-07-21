#!/usr/bin/env python3
"""
News Reader Elite - System Test Script
Tests all API endpoints and functionality.
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_stats():
    """Test statistics endpoint"""
    print("📊 Testing statistics...")
    try:
        response = requests.get(f"{BASE_URL}/api/stats")
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"✅ Stats: DB={data['database_count']}, Sources={len(data['source_stats'])}")
                return True
            else:
                print(f"❌ Stats failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Stats request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Stats error: {e}")
        return False

def test_news():
    """Test news endpoint"""
    print("📰 Testing news endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/news?limit=5")
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"✅ News: {data['count']} articles retrieved")
                return True
            else:
                print(f"❌ News failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ News request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ News error: {e}")
        return False

def test_sources():
    """Test sources endpoint"""
    print("🔗 Testing sources...")
    try:
        response = requests.get(f"{BASE_URL}/api/sources")
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                api_count = len(data['sources'].get('api', []))
                rss_count = len(data['sources'].get('rss', []))
                print(f"✅ Sources: API={api_count}, RSS={rss_count}")
                return True
            else:
                print(f"❌ Sources failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Sources request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Sources error: {e}")
        return False

def test_collection(collection_type):
    """Test collection endpoint"""
    print(f"🔄 Testing {collection_type} collection...")
    try:
        response = requests.post(f"{BASE_URL}/api/collect/{collection_type}")
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"✅ {collection_type.upper()} collection completed")
                return True
            else:
                print(f"❌ {collection_type} collection failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ {collection_type} collection request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {collection_type} collection error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 News Reader Elite - System Test")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health),
        ("Statistics", test_stats),
        ("News Articles", test_news),
        ("Sources", test_sources),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
        time.sleep(1)
    
    print("\n" + "=" * 50)
    print(f"📈 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! System is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the system.")
    
    print(f"\n🌐 Frontend: http://localhost:3000")
    print(f"🔧 API: http://localhost:8000")
    print(f"📖 API Docs: http://localhost:8000/docs")

if __name__ == "__main__":
    main() 