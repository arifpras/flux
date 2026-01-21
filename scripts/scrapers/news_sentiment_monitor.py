#!/usr/bin/env python3
"""
News Sentiment Monitor for Indonesian Stock Market
Scrapes financial news and scores sentiment to detect regulatory/corporate risks

Usage:
    python news_sentiment_monitor.py --stocks ASII,UNTR,ADRO
    python news_sentiment_monitor.py --all  # Check all IDX stocks
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from datetime import datetime, timedelta
import re
from typing import Dict, List, Tuple
import argparse
from pathlib import Path

class IndonesianNewsSentiment:
    """Monitor Indonesian financial news for sentiment analysis"""
    
    # High-risk keywords (immediate red flags)
    CRITICAL_KEYWORDS = {
        'regulatory': ['dicabut', 'pencabutan', 'suspend', 'penghentian', 'sanksi', 
                      'denda', 'pelanggaran', 'investigasi', 'pidana', 'criminal'],
        'operational': ['force majeure', 'kecelakaan', 'kebakaran', 'banjir', 
                       'bencana', 'tutup', 'shutdown', 'ditutup'],
        'financial': ['default', 'gagal bayar', 'pailit', 'bangkrut', 'delisting', 
                     'suspend perdagangan', 'suspend saham'],
        'corporate': ['resign', 'mengundurkan diri', 'skandal', 'fraud', 
                     'korupsi', 'manipulation']
    }
    
    # Negative sentiment keywords
    NEGATIVE_KEYWORDS = [
        'rontok', 'anjlok', 'terjun', 'merosot', 'ambruk', 'tertekan',
        'lemah', 'turun tajam', 'penurunan', 'rugi', 'loss', 'deficit',
        'reject', 'ditolak', 'gagal', 'failed', 'warning'
    ]
    
    # Positive sentiment keywords
    POSITIVE_KEYWORDS = [
        'naik', 'rally', 'menguat', 'rebound', 'profit', 'laba', 
        'kinerja positif', 'ekspansi', 'kontrak baru', 'dividen',
        'buyback', 'akuisisi', 'pertumbuhan', 'melonjak'
    ]
    
    NEWS_SOURCES = {
        'detik_finance': 'https://finance.detik.com/bursa-dan-valas',
        'cnbc_indonesia': 'https://www.cnbcindonesia.com/market',
        'kontan_investasi': 'https://investasi.kontan.co.id/news',
        'bisnis_market': 'https://market.bisnis.com/read',
        'idx_announcements': 'https://idx.co.id/id/perusahaan-tercatat/pengumuman-perusahaan-tercatat/'
    }
    
    def __init__(self, cache_dir: str = "data/news_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.today = datetime.now().strftime('%Y%m%d')
        
    def scrape_detik_finance(self, stock_code: str) -> List[Dict]:
        """Scrape Detik Finance for stock-related news"""
        articles = []
        
        try:
            # Search for stock code
            search_url = f"https://finance.detik.com/search?query={stock_code}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Parse article links (adjust selectors based on actual HTML)
            for article in soup.find_all('article', limit=10):
                try:
                    title_elem = article.find('h3') or article.find('h2')
                    link_elem = article.find('a')
                    date_elem = article.find('time') or article.find('span', class_='date')
                    
                    if title_elem and link_elem:
                        articles.append({
                            'source': 'detik_finance',
                            'title': title_elem.get_text(strip=True),
                            'url': link_elem.get('href', ''),
                            'date': date_elem.get_text(strip=True) if date_elem else 'today',
                            'stock_code': stock_code
                        })
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error scraping Detik Finance for {stock_code}: {e}")
            
        return articles
    
    def scrape_idx_announcements(self, stock_code: str) -> List[Dict]:
        """Scrape IDX official announcements"""
        # Note: IDX website may require authentication or specific API
        # This is a placeholder for the implementation
        return []
    
    def calculate_sentiment_score(self, text: str) -> Tuple[float, str, List[str]]:
        """
        Calculate sentiment score from text
        Returns: (score, category, matched_keywords)
        Score: -100 to +100
        """
        text_lower = text.lower()
        matched_keywords = []
        score = 0
        category = 'NEUTRAL'
        
        # Check for critical keywords (highest priority)
        for risk_type, keywords in self.CRITICAL_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    score -= 30
                    matched_keywords.append(f"CRITICAL_{risk_type}: {keyword}")
                    category = 'CRITICAL'
        
        # Check negative keywords
        for keyword in self.NEGATIVE_KEYWORDS:
            if keyword in text_lower:
                score -= 10
                matched_keywords.append(f"NEGATIVE: {keyword}")
                if category != 'CRITICAL':
                    category = 'NEGATIVE'
        
        # Check positive keywords
        for keyword in self.POSITIVE_KEYWORDS:
            if keyword in text_lower:
                score += 10
                matched_keywords.append(f"POSITIVE: {keyword}")
                if category == 'NEUTRAL':
                    category = 'POSITIVE'
        
        # Cap score at -100 to +100
        score = max(-100, min(100, score))
        
        return score, category, matched_keywords
    
    def analyze_stock_sentiment(self, stock_code: str, hours_lookback: int = 24) -> Dict:
        """
        Analyze sentiment for a specific stock
        Returns summary with overall score and flagged articles
        """
        print(f"\n🔍 Analyzing sentiment for {stock_code}...")
        
        # Gather articles from multiple sources
        all_articles = []
        all_articles.extend(self.scrape_detik_finance(stock_code))
        # all_articles.extend(self.scrape_idx_announcements(stock_code))
        
        if not all_articles:
            return {
                'stock_code': stock_code,
                'overall_score': 0,
                'overall_category': 'NO_NEWS',
                'articles_analyzed': 0,
                'critical_alerts': [],
                'negative_alerts': [],
                'timestamp': datetime.now().isoformat()
            }
        
        # Analyze each article
        critical_alerts = []
        negative_alerts = []
        total_score = 0
        
        for article in all_articles:
            score, category, keywords = self.calculate_sentiment_score(article['title'])
            article['sentiment_score'] = score
            article['sentiment_category'] = category
            article['matched_keywords'] = keywords
            
            total_score += score
            
            if category == 'CRITICAL':
                critical_alerts.append(article)
            elif category == 'NEGATIVE':
                negative_alerts.append(article)
        
        # Calculate overall sentiment
        avg_score = total_score / len(all_articles) if all_articles else 0
        
        if critical_alerts:
            overall_category = 'CRITICAL'
        elif avg_score < -20:
            overall_category = 'NEGATIVE'
        elif avg_score > 20:
            overall_category = 'POSITIVE'
        else:
            overall_category = 'NEUTRAL'
        
        result = {
            'stock_code': stock_code,
            'overall_score': round(avg_score, 2),
            'overall_category': overall_category,
            'articles_analyzed': len(all_articles),
            'critical_alerts': critical_alerts,
            'negative_alerts': negative_alerts,
            'all_articles': all_articles,
            'timestamp': datetime.now().isoformat()
        }
        
        return result
    
    def monitor_watchlist(self, stock_codes: List[str]) -> pd.DataFrame:
        """
        Monitor sentiment for multiple stocks
        Returns DataFrame with summary
        """
        results = []
        
        for stock_code in stock_codes:
            sentiment = self.analyze_stock_sentiment(stock_code)
            
            results.append({
                'Stock': stock_code,
                'Score': sentiment['overall_score'],
                'Category': sentiment['overall_category'],
                'Articles': sentiment['articles_analyzed'],
                'Critical': len(sentiment['critical_alerts']),
                'Negative': len(sentiment['negative_alerts']),
                'Status': '🔴 EXIT' if sentiment['overall_category'] == 'CRITICAL' 
                         else '🟡 WATCH' if sentiment['overall_category'] == 'NEGATIVE'
                         else '🟢 OK'
            })
            
            # Save detailed report
            if sentiment['overall_category'] in ['CRITICAL', 'NEGATIVE']:
                self.save_alert_report(sentiment)
        
        df = pd.DataFrame(results)
        df = df.sort_values('Score', ascending=True)
        
        return df
    
    def save_alert_report(self, sentiment_data: Dict):
        """Save detailed report for critical/negative sentiment"""
        stock_code = sentiment_data['stock_code']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        filename = self.cache_dir / f"{timestamp}_{stock_code}_ALERT.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(sentiment_data, f, indent=2, ensure_ascii=False)
        
        print(f"⚠️  Alert saved: {filename}")
    
    def generate_daily_report(self, stock_codes: List[str]) -> str:
        """Generate human-readable daily sentiment report"""
        df = self.monitor_watchlist(stock_codes)
        
        report = f"""
═══════════════════════════════════════════════════════════
  DAILY NEWS SENTIMENT REPORT - {datetime.now().strftime('%d %B %Y')}
═══════════════════════════════════════════════════════════

{df.to_string(index=False)}

LEGEND:
🔴 EXIT    - Critical regulatory/operational risk detected
🟡 WATCH   - Negative sentiment, monitor closely
🟢 OK      - Neutral or positive sentiment

ALERT THRESHOLD:
- Critical Score: < -30 (immediate exit recommended)
- Negative Score: -30 to -10 (reduce position)
- Neutral Score: -10 to +10 (hold)
- Positive Score: > +10 (monitor for entry)

═══════════════════════════════════════════════════════════
"""
        return report


def load_watchlist() -> List[str]:
    """Load stocks from watchlist or active trades"""
    watchlist_path = Path("results/watchlist_final_20stocks.txt")
    
    if watchlist_path.exists():
        with open(watchlist_path, 'r') as f:
            stocks = [line.strip() for line in f if line.strip()]
        return stocks[:10]  # Limit to top 10 to avoid rate limiting
    
    # Default watchlist if file doesn't exist
    return ['ADRO', 'ASII', 'UNTR', 'BBRI', 'BMRI', 'TLKM', 'BBCA', 'ANTM']


def main():
    parser = argparse.ArgumentParser(description='Monitor Indonesian stock market news sentiment')
    parser.add_argument('--stocks', type=str, help='Comma-separated stock codes (e.g., ASII,UNTR,ADRO)')
    parser.add_argument('--all', action='store_true', help='Monitor all stocks in watchlist')
    parser.add_argument('--output', type=str, default='data/news_cache', help='Output directory')
    
    args = parser.parse_args()
    
    # Determine stocks to monitor
    if args.stocks:
        stock_codes = [s.strip().upper() for s in args.stocks.split(',')]
    elif args.all:
        stock_codes = load_watchlist()
    else:
        # Default: check active trades and top candidates
        stock_codes = ['ADRO', 'ASII', 'UNTR']
    
    print(f"📰 Monitoring sentiment for: {', '.join(stock_codes)}")
    
    # Initialize monitor
    monitor = IndonesianNewsSentiment(cache_dir=args.output)
    
    # Generate report
    report = monitor.generate_daily_report(stock_codes)
    print(report)
    
    # Save report
    report_file = Path(args.output) / f"sentiment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ Report saved: {report_file}")


if __name__ == '__main__':
    main()
