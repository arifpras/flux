#!/usr/bin/env python3
"""
Enhanced News Sentiment Monitor using Google News RSS and NewsAPI
More reliable than direct scraping, provides structured data

Setup:
    pip install feedparser newsapi-python beautifulsoup4

Usage:
    python news_sentiment_api.py --stocks ASII,UNTR --hours 24
"""

import feedparser
import requests
from datetime import datetime, timedelta
import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Tuple
import re
import argparse


class NewsAPI_Sentiment:
    """Enhanced sentiment monitor using RSS feeds and APIs"""
    
    CRITICAL_KEYWORDS = {
        'regulatory_indonesian': [
            'dicabut', 'pencabutan izin', 'suspend', 'penghentian', 
            'sanksi', 'denda', 'pelanggaran', 'investigasi',
            'penyelidikan', 'pidana', 'criminal investigation',
            'revoke', 'revocation', 'permit denied', 'license cancelled'
        ],
        'operational_indonesian': [
            'force majeure', 'kecelakaan fatal', 'kebakaran', 
            'banjir besar', 'bencana', 'tutup permanen',
            'shutdown', 'ditutup', 'operasi terhenti',
            'production halt', 'accident', 'disaster'
        ],
        'financial_critical': [
            'default', 'gagal bayar', 'pailit', 'bankrupt',
            'delisting', 'suspend perdagangan', 'trading halt',
            'debt default', 'restructuring', 'bankruptcy'
        ],
        'corporate_crisis': [
            'resign CEO', 'mengundurkan diri', 'skandal', 
            'fraud', 'korupsi', 'manipulation', 'investigation',
            'sued', 'lawsuit', 'gugatan'
        ]
    }
    
    NEGATIVE_INDONESIAN = [
        'rontok', 'anjlok', 'terjun bebas', 'merosot', 'ambruk',
        'tertekan', 'lemah', 'turun tajam', 'penurunan drastis',
        'rugi besar', 'loss', 'deficit', 'reject', 'ditolak',
        'gagal', 'failed', 'warning', 'red flag', 'concern'
    ]
    
    POSITIVE_INDONESIAN = [
        'naik', 'rally', 'menguat', 'rebound', 'profit meningkat',
        'laba naik', 'kinerja positif', 'ekspansi', 'kontrak baru',
        'dividen', 'buyback', 'akuisisi strategis', 'pertumbuhan',
        'melonjak', 'breakthrough', 'partnership', 'expansion'
    ]
    
    def __init__(self, cache_dir: str = "data/news_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def fetch_google_news(self, query: str, hours_back: int = 24) -> List[Dict]:
        """
        Fetch news from Google News RSS feed
        More reliable than scraping individual sites
        """
        articles = []
        
        try:
            from urllib.parse import quote_plus
            
            # URL encode the query properly
            encoded_query = quote_plus(query)
            url = f"https://news.google.com/rss/search?q={encoded_query}+when:{hours_back}h&hl=id&gl=ID&ceid=ID:id"
            
            feed = feedparser.parse(url)
            
            for entry in feed.entries:
                articles.append({
                    'source': 'google_news',
                    'title': entry.get('title', ''),
                    'summary': entry.get('summary', ''),
                    'url': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'query': query
                })
                
        except Exception as e:
            print(f"❌ Error fetching Google News for {query}: {e}")
            
        return articles
    
    def fetch_idx_announcements_page(self, stock_code: str) -> List[Dict]:
        """
        Scrape IDX announcements page
        Direct from source = most reliable for corporate actions
        """
        articles = []
        
        try:
            url = f"https://www.idx.co.id/id/perusahaan-tercatat/pengumuman-perusahaan-tercatat/?kodeEmiten={stock_code}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            
            # Simple extraction (IDX uses table structure)
            if stock_code.upper() in response.text:
                articles.append({
                    'source': 'idx_official',
                    'title': f'IDX has announcements for {stock_code}',
                    'url': url,
                    'published': datetime.now().isoformat(),
                    'query': stock_code,
                    'note': 'Check manually at idx.co.id'
                })
                
        except Exception as e:
            print(f"❌ Error checking IDX for {stock_code}: {e}")
            
        return articles
    
    def calculate_sentiment(self, text: str) -> Tuple[float, str, List[str]]:
        """
        Calculate sentiment score (-100 to +100)
        Returns: (score, category, matched_keywords)
        """
        text_lower = text.lower()
        matched = []
        score = 0
        
        # Critical keywords = -30 each
        for category, keywords in self.CRITICAL_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    score -= 30
                    matched.append(f"🔴 {category.upper()}: '{kw}'")
        
        # Negative keywords = -10 each
        for kw in self.NEGATIVE_INDONESIAN:
            if kw in text_lower:
                score -= 10
                matched.append(f"🟡 NEGATIVE: '{kw}'")
        
        # Positive keywords = +10 each
        for kw in self.POSITIVE_INDONESIAN:
            if kw in text_lower:
                score += 10
                matched.append(f"🟢 POSITIVE: '{kw}'")
        
        # Determine category
        if any('🔴' in m for m in matched):
            category = 'CRITICAL'
        elif score < -20:
            category = 'NEGATIVE'
        elif score > 20:
            category = 'POSITIVE'
        else:
            category = 'NEUTRAL'
        
        return max(-100, min(100, score)), category, matched
    
    def analyze_stock(self, stock_code: str, hours_back: int = 24) -> Dict:
        """
        Comprehensive sentiment analysis for one stock
        """
        print(f"\n📰 Analyzing {stock_code}...")
        
        # Fetch from multiple sources
        articles = []
        
        # Google News (Indonesian financial news)
        queries = [
            f"{stock_code} saham",
            f"{stock_code} bursa",
            f"PT {stock_code}"
        ]
        
        for query in queries:
            articles.extend(self.fetch_google_news(query, hours_back))
        
        # IDX official announcements
        articles.extend(self.fetch_idx_announcements_page(stock_code))
        
        if not articles:
            return {
                'stock': stock_code,
                'score': 0,
                'category': 'NO_NEWS',
                'articles_found': 0,
                'critical_count': 0,
                'negative_count': 0,
                'recommendation': '🟢 No news (neutral)',
                'timestamp': datetime.now().isoformat()
            }
        
        # Analyze each article
        critical_articles = []
        negative_articles = []
        all_scores = []
        all_keywords = []
        
        for article in articles:
            text = f"{article['title']} {article.get('summary', '')}"
            score, category, keywords = self.calculate_sentiment(text)
            
            article['sentiment_score'] = score
            article['sentiment_category'] = category
            article['keywords_matched'] = keywords
            
            all_scores.append(score)
            all_keywords.extend(keywords)
            
            if category == 'CRITICAL':
                critical_articles.append(article)
            elif category == 'NEGATIVE':
                negative_articles.append(article)
        
        # Overall assessment
        avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
        
        if critical_articles:
            overall_category = 'CRITICAL'
            recommendation = f"🔴 IMMEDIATE EXIT - {len(critical_articles)} critical alerts"
        elif avg_score < -20:
            overall_category = 'NEGATIVE'
            recommendation = f"🟡 REDUCE POSITION - Sentiment: {avg_score:.1f}"
        elif avg_score > 20:
            overall_category = 'POSITIVE'
            recommendation = f"🟢 MONITOR ENTRY - Sentiment: {avg_score:.1f}"
        else:
            overall_category = 'NEUTRAL'
            recommendation = f"⚪ HOLD - Sentiment: {avg_score:.1f}"
        
        result = {
            'stock': stock_code,
            'score': round(avg_score, 1),
            'category': overall_category,
            'articles_found': len(articles),
            'critical_count': len(critical_articles),
            'negative_count': len(negative_articles),
            'recommendation': recommendation,
            'critical_articles': critical_articles,
            'all_articles': articles[:10],  # Limit to 10 most recent
            'all_keywords': list(set(all_keywords)),
            'timestamp': datetime.now().isoformat()
        }
        
        # Save alert if critical
        if overall_category == 'CRITICAL':
            self.save_critical_alert(result)
        
        return result
    
    def save_critical_alert(self, data: Dict):
        """Save critical alerts to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.cache_dir / f"ALERT_{timestamp}_{data['stock']}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n⚠️  CRITICAL ALERT SAVED: {filename}")
    
    def monitor_portfolio(self, stocks: List[str], hours_back: int = 24) -> pd.DataFrame:
        """Monitor multiple stocks and return summary"""
        results = []
        
        for stock in stocks:
            analysis = self.analyze_stock(stock, hours_back)
            
            results.append({
                'Stock': stock,
                'Score': analysis['score'],
                'Category': analysis['category'],
                'Articles': analysis['articles_found'],
                '🔴 Critical': analysis['critical_count'],
                '🟡 Negative': analysis['negative_count'],
                'Action': analysis['recommendation']
            })
        
        df = pd.DataFrame(results)
        df = df.sort_values('Score', ascending=True)  # Most negative first
        
        return df


def main():
    parser = argparse.ArgumentParser(description='News Sentiment Monitor (Enhanced)')
    parser.add_argument('--stocks', type=str, required=True, 
                       help='Comma-separated stock codes')
    parser.add_argument('--hours', type=int, default=24,
                       help='Hours to look back (default: 24)')
    parser.add_argument('--output', type=str, default='data/news_cache',
                       help='Output directory')
    
    args = parser.parse_args()
    
    stocks = [s.strip().upper() for s in args.stocks.split(',')]
    
    print(f"\n{'='*70}")
    print(f"  NEWS SENTIMENT ANALYSIS - {datetime.now().strftime('%d %B %Y %H:%M')}")
    print(f"{'='*70}")
    print(f"Stocks: {', '.join(stocks)}")
    print(f"Lookback: {args.hours} hours")
    print(f"{'='*70}")
    
    monitor = NewsAPI_Sentiment(cache_dir=args.output)
    df = monitor.monitor_portfolio(stocks, args.hours)
    
    print(f"\n{df.to_string(index=False)}")
    
    # Save report
    report_file = Path(args.output) / f"sentiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(report_file, index=False)
    
    print(f"\n✅ Report saved: {report_file}")
    
    # Show critical alerts
    critical = df[df['Category'] == 'CRITICAL']
    if not critical.empty:
        print(f"\n{'='*70}")
        print("⚠️  CRITICAL ALERTS - IMMEDIATE ACTION REQUIRED")
        print(f"{'='*70}")
        for _, row in critical.iterrows():
            print(f"  • {row['Stock']}: {row['Action']}")
        print(f"{'='*70}")


if __name__ == '__main__':
    main()
