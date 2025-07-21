#!/usr/bin/env python3
"""
RSS-NEWS-READER - Simplified Version
Check RSS feed status and fetch news
"""
import argparse
import json
import logging
import ssl
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.request import Request, urlopen
import urllib.error

import requests

# Configuration
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'sources'
LOG_DIR = BASE_DIR / 'logs'
SOURCES_FILE = DATA_DIR / '02_rss_sources.json'
NEWS_FILE = BASE_DIR / 'outputs' / '01_rss_news.json'
LOG_FILE = LOG_DIR / '02_rss_collector.log'

# Create directories
DATA_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)
NEWS_FILE.parent.mkdir(exist_ok=True)

# Logger setup
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

# SSL settings
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def log_print(msg, level='info'):
    """Print and log message"""
    print(msg)
    getattr(logger, level)(msg)

def load_sources():
    """Load RSS sources"""
    if not SOURCES_FILE.exists():
        log_print(f'Source file not found: {SOURCES_FILE}', 'error')
        return []
    try:
        with open(SOURCES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log_print(f'Failed to load sources: {e}', 'error')
        return []

def get_latest_date(items, is_atom=False):
    """Get latest publication date"""
    latest = None
    date_tag = '{http://www.w3.org/2005/Atom}published' if is_atom else 'pubDate'
    
    for item in items:
        date_elem = item.find(date_tag)
        if date_elem is not None and date_elem.text:
            try:
                dt = parsedate_to_datetime(date_elem.text)
                if not latest or dt > latest:
                    latest = dt
            except:
                try:
                    from dateutil import parser as dateutil_parser
                    dt = dateutil_parser.parse(date_elem.text)
                    if not latest or dt > latest:
                        latest = dt
                except:
                    continue
    return latest

def parse_item(item, source, is_atom=False):
    """Parse news item"""
    if is_atom:
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        title = item.find('{http://www.w3.org/2005/Atom}title')
        link = item.find('{http://www.w3.org/2005/Atom}link')
        pub_date = item.find('{http://www.w3.org/2005/Atom}published')
        summary = item.find('{http://www.w3.org/2005/Atom}summary')
        
        return {
            'source_id': source.get('id'),
            'source_name': source.get('name', ''),
            'title': title.text.strip() if title is not None and title.text else '',
            'link': link.get('href') if link is not None else '',
            'published': pub_date.text.strip() if pub_date is not None and pub_date.text else '',
            'summary': summary.text.strip() if summary is not None and summary.text else '',
            'fetched_at': datetime.now(timezone.utc).isoformat()
        }
    else:
        title = item.find('title')
        link = item.find('link')
        pub_date = item.find('pubDate')
        desc = item.find('description')
        
        return {
            'source_id': source.get('id'),
            'source_name': source.get('name', ''),
            'title': title.text.strip() if title is not None and title.text else '',
            'link': link.text.strip() if link is not None and link.text else '',
            'published': pub_date.text.strip() if pub_date is not None and pub_date.text else '',
            'summary': desc.text.strip() if desc is not None and desc.text else '',
            'fetched_at': datetime.now(timezone.utc).isoformat()
        }

def check_source(source):
    """Check RSS source status"""
    url = source.get('url')
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            root = ET.fromstring(r.content)
            is_atom = 'feed' in root.tag
            items = root.findall('.//item') or root.findall('.//entry')
            latest = get_latest_date(items, is_atom)
            return True, len(items), latest, None
        else:
            return False, 0, None, f'HTTP {r.status_code}'
    except Exception as e:
        return False, 0, None, str(e)

def fetch_source(source):
    """Fetch RSS source"""
    url = source.get('url')
    name = source.get('name', 'Unknown')
    
    # Retry mechanism
    for attempt in range(3):
        try:
            if attempt > 0:
                time.sleep(2)
            else:
                time.sleep(1)
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            req = Request(url, headers=headers)
            
            with urlopen(req, context=ssl_context, timeout=30) as response:
                content = response.read().decode('utf-8', errors='ignore')
            break
            
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:
                continue
            elif attempt == 2:
                return []
            else:
                raise
        except Exception as e:
            if attempt < 2:
                continue
            else:
                return []
    
    try:
        root = ET.fromstring(content)
        is_atom = 'feed' in root.tag
        items = []
        
        if is_atom:
            for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                items.append(parse_item(entry, source, True))
        else:
            for item in root.findall('.//item'):
                items.append(parse_item(item, source, False))
        
        return items
    except Exception:
        return []

def remove_duplicates(news_items):
    """Remove duplicates"""
    unique = {}
    duplicates = 0
    for item in news_items:
        title = item.get('title', '').strip()
        link = item.get('link', '').strip()
        if title and link:
            key = f"{title}|{link}"
            if key not in unique:
                unique[key] = item
            else:
                duplicates += 1
    log_print(f'Removed {duplicates} duplicate items')
    return list(unique.values())

def run():
    """Main function"""
    sources = load_sources()
    if not sources:
        return
    
    log_print(f'Checking and fetching {len(sources)} RSS sources...')
    ten_days_ago = datetime.now(timezone.utc) - timedelta(days=10)
    
    # Load existing news
    existing_news = []
    if NEWS_FILE.exists():
        try:
            with open(NEWS_FILE, 'r', encoding='utf-8') as f:
                existing_news = json.load(f)
            log_print(f'Loaded {len(existing_news)} existing news items')
        except Exception as e:
            log_print(f'Failed to load existing news: {e}', 'warning')
    
    # Check and fetch
    new_news = []
    for source in sources:
        try:
            success, count, latest_date, err = check_source(source)
            if success:
                latest_str = latest_date.strftime('%Y-%m-%d %H:%M:%S') if latest_date else 'No date'
                outdated = latest_date and latest_date.replace(tzinfo=timezone.utc) < ten_days_ago
                
                items = fetch_source(source)
                new_news.extend(items)
                
                status = "⚠️" if outdated else "✓"
                url_short = source.get('url', '').split('//')[-1].split('/')[0]
                log_print(f"{status} {source['name']} ({url_short}) {latest_str} ✓ {len(items)}")
            else:
                log_print(f"✗ {source['name']} - {err}")
        except Exception as e:
            log_print(f"✗ {source['name']} - {str(e)}", 'error')
    
    # Merge and deduplicate
    all_news = existing_news + new_news
    unique_news = remove_duplicates(all_news)
    
    # Save
    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(unique_news, f, ensure_ascii=False, indent=2)
    
    log_print(f'RSS: {len(new_news)} news → Dup {len(all_news) - len(unique_news)} → JSON + {len(unique_news)}')
    log_print(f'Total unique items: {len(unique_news)}')
    log_print(f'Saved to {NEWS_FILE}')

def run_auto_collection(interval_minutes=3):
    """Run RSS collection in auto mode with specified interval"""
    log_print(f"RSS auto collector started - interval: {interval_minutes} minutes")
    
    while True:
        try:
            run()
            log_print(f"Waiting {interval_minutes} minutes...")
            time.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            log_print("RSS auto collector stopped")
            break
        except Exception as e:
            log_print(f"RSS main loop error: {e}", 'error')
            time.sleep(60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RSS-NEWS-READER")
    parser.add_argument("action", nargs='?', default="run", 
                       help="Action: run(default) - Check and fetch all RSS sources")
    parser.add_argument("--auto", action="store_true", help="Run in auto mode with 3-minute intervals")
    parser.add_argument("--interval", type=int, default=3, help="Collection interval in minutes (default: 3)")
    args = parser.parse_args()
    
    if args.auto:
        run_auto_collection(args.interval)
    elif args.action in ["run", "checkfetch"]:
        run()
    else:
        print("Usage: python rss_collector.py [run] [--auto] [--interval MINUTES]")