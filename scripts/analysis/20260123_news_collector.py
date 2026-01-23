#!/usr/bin/env python3
"""
News Fetcher for Recommended Stocks
Fetches real news from various sources for sentiment analysis
Fills the news cache for continued monitoring
"""

import requests
import json
from pathlib import Path
from datetime import datetime, timedelta
import time

# RECOMMENDED STOCKS FROM REPORT (focus on Priority 1 and High Conviction)
PRIORITY_STOCKS = {
    "DGIK": "Priority 1 - Technical Oversold",
    "ASII": "Priority 1 - Foreign Accumulation",
    "BBKP": "Priority 1 - Momentum",
    "UNTR": "High Conviction - Foreign + Fundamentals",
    "KLBF": "High Conviction - Foreign Accumulation",
    "ADRO": "Dividend Income",
    "PTBA": "Dividend Income",
    "MEGA": "Dividend Income (Feb/Mar)",
}

class NewsCollector:
    """Collect news from multiple sources"""
    
    def __init__(self, cache_dir):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.timeout = 10
    
    def fetch_news_api(self, query, ticker):
        """Fetch news from NewsAPI (if available)"""
        # Using public news sources about Indonesian stocks
        # In production, integrate with actual news APIs
        try:
            # This is a placeholder - implement with actual API
            pass
        except Exception as e:
            print(f"⚠️  Error fetching news for {ticker}: {e}")
            return []
    
    def fetch_google_news(self, ticker):
        """Fetch news from Google News RSS"""
        try:
            # Google News RSS URL for Indonesian stocks
            url = f"https://news.google.com/rss/search?q=IDX+{ticker}+stock&hl=id&gl=ID&ceid=ID:id"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
            }
            
            response = self.session.get(url, headers=headers, timeout=5)
            articles = []
            
            if response.status_code == 200:
                # Parse RSS feed (simplified)
                # In production, use feedparser library
                # For now, return empty (will implement with actual RSS parser)
                pass
            
            return articles
        except Exception as e:
            print(f"⚠️  Could not fetch Google News for {ticker}: {e}")
            return []
    
    def fetch_local_sources(self, ticker):
        """Fetch news from Indonesian financial news sources"""
        local_sources = {
            "idx": f"https://www.idx.co.id/",  # IDX official
            "liputan6": f"https://bisnis.liputan6.com/",
            "kompas": f"https://money.kompas.com/",
        }
        
        # Placeholder for actual news fetching
        # This would connect to web scrapers or APIs
        return []
    
    def cache_news(self, ticker, articles):
        """Save news to local cache"""
        cache_file = self.cache_dir / f"{ticker}_news.json"
        
        existing = []
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        
        # Merge with new articles (avoid duplicates)
        existing_titles = {a.get('title') for a in existing}
        new_articles = [a for a in articles if a.get('title') not in existing_titles]
        
        all_articles = existing + new_articles
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(all_articles, f, indent=2, ensure_ascii=False)
        
        return len(new_articles)
    
    def fetch_all(self):
        """Fetch news for all priority stocks"""
        print("=" * 80)
        print("NEWS COLLECTION FOR RECOMMENDED STOCKS".center(80))
        print("=" * 80)
        print(f"\nStarting news collection: {datetime.now()}\n")
        
        total_collected = 0
        
        for ticker, category in PRIORITY_STOCKS.items():
            print(f"📰 {ticker:8} │ {category}")
            
            articles = []
            
            # Try different sources
            articles.extend(self.fetch_google_news(ticker))
            time.sleep(0.5)  # Rate limiting
            
            articles.extend(self.fetch_local_sources(ticker))
            time.sleep(0.5)
            
            articles.extend(self.fetch_news_api(ticker, f"IDX {ticker}"))
            
            if articles:
                saved = self.cache_news(ticker, articles)
                print(f"         │ ✓ Cached {saved} new articles")
                total_collected += saved
            else:
                print(f"         │ ✗ No articles found (will retry later)")
        
        print(f"\n✅ Collection complete: {total_collected} new articles cached")
        print("\nNote: To enable full news collection, configure:")
        print("  1. NewsAPI.org integration")
        print("  2. Indonesian news source scrapers")
        print("  3. IDX official announcements RSS feed")

def main():
    workspace = Path("/Users/arifpras/Library/CloudStorage/Dropbox/perisai/stockscraper")
    cache_dir = workspace / "data" / "news_cache"
    
    collector = NewsCollector(cache_dir)
    collector.fetch_all()
    
    print(f"\n📁 Cache location: {cache_dir}")
    print("   Sentiment analyzer will use this cache automatically")

if __name__ == "__main__":
    main()
