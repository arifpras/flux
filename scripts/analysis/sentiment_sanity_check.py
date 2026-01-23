#!/usr/bin/env python3
"""
Sentiment Analysis Sanity Check for Investment Candidates
Checks recent news for negative signals before executing trades

Author: Investment Analysis System
Date: 23 January 2026
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Tuple
import re

# INVESTMENT CANDIDATES FROM README
PRIORITY_STOCKS = {
    "IMMEDIATE": {
        "DGIK": {"strategy": "Technical Oversold", "entry": 140, "target": 160},
        "ASII": {"strategy": "Foreign + Fundamentals", "entry": 6775, "target": 7450},
        "BBKP": {"strategy": "Momentum", "entry": 86, "target": 100},
    },
    "WATCH": {
        "UNTR": {"strategy": "Foreign + Fundamentals", "entry": 26000},
        "MERK": {"strategy": "Technical Oversold", "entry": 3200},
        "KLBF": {"strategy": "Foreign Accumulation", "entry": 1200},
    },
    "DIVIDEND": {
        "ADRO": {"strategy": "Dividend Income", "yield": "114%"},
        "PTBA": {"strategy": "Dividend Income", "yield": "72%"},
        "BSSR": {"strategy": "Dividend Income", "yield": "50%"},
    },
    "TECHNICAL": {
        "GMFI": {"strategy": "Foreign + Fundamentals", "entry": 71},
        "CNMA": {"strategy": "Foreign + Fundamentals", "entry": 121},
        "CTRA": {"strategy": "Foreign Accumulation", "entry": 890},
    }
}

# RED FLAGS - Negative sentiment keywords
RED_FLAGS = {
    "CRITICAL": [
        r"default|bankruptcy|insolvency|restructuring",
        r"delisted|suspended|trading halt",
        r"fraud|embezzlement|corruption",
        r"loss of license|regulatory ban",
        r"massive loss|financial crisis",
    ],
    "HIGH": [
        r"downgrade|rating cut",
        r"dividend cut|dividend suspension",
        r"massive write-off|impairment",
        r"major lawsuit|legal action|settlement",
        r"management exodus|ceo resign",
        r"key contract lost|major client loss",
    ],
    "MEDIUM": [
        r"warning|concern|risk|weak|decline",
        r"investigation|probe|inquiry",
        r"debt default|missed payment",
        r"production halt|operational issue",
        r"loss|deficit|negative earnings",
    ]
}

# GREEN FLAGS - Positive sentiment keywords
GREEN_FLAGS = [
    r"upgrade|strong|growth|expansion",
    r"new contract|new market|acquisition",
    r"recovery|rebound|resilience",
    r"dividend increase|special dividend",
    r"new investment|capex|capx",
]

class NewsAlertParser:
    def __init__(self, news_dir: str):
        self.news_dir = Path(news_dir)
        self.alerts = defaultdict(list)
        self.load_alerts()
    
    def load_alerts(self):
        """Load all alert JSON files"""
        if not self.news_dir.exists():
            print(f"⚠️  News cache directory not found: {self.news_dir}")
            return
        
        for json_file in self.news_dir.glob("ALERT_*.json"):
            stock = json_file.stem.split("_")[-1]
            try:
                with open(json_file) as f:
                    data = json.load(f)
                    self.alerts[stock].append(data)
            except Exception as e:
                print(f"❌ Error loading {json_file}: {e}")
    
    def analyze_sentiment(self, text: str) -> Tuple[str, float, List[str]]:
        """
        Analyze text sentiment
        Returns: (sentiment, score, matched_keywords)
        """
        if not text:
            return "NEUTRAL", 0.0, []
        
        text_lower = text.lower()
        matched_keywords = []
        score = 0.0
        
        # Check for critical red flags
        for keyword_pattern in RED_FLAGS["CRITICAL"]:
            if re.search(keyword_pattern, text_lower):
                matched_keywords.append(keyword_pattern)
                score -= 100  # Critical reduction
        
        # Check for high red flags
        for keyword_pattern in RED_FLAGS["HIGH"]:
            if re.search(keyword_pattern, text_lower):
                matched_keywords.append(keyword_pattern)
                score -= 30
        
        # Check for medium red flags
        for keyword_pattern in RED_FLAGS["MEDIUM"]:
            if re.search(keyword_pattern, text_lower):
                matched_keywords.append(keyword_pattern)
                score -= 10
        
        # Check for green flags
        for keyword_pattern in GREEN_FLAGS:
            if re.search(keyword_pattern, text_lower):
                matched_keywords.append(keyword_pattern)
                score += 15
        
        # Determine sentiment
        if score <= -50:
            sentiment = "🔴 CRITICAL NEGATIVE"
        elif score <= -20:
            sentiment = "🟠 NEGATIVE"
        elif score <= -5:
            sentiment = "🟡 SLIGHTLY NEGATIVE"
        elif score <= 5:
            sentiment = "⚪ NEUTRAL"
        elif score <= 20:
            sentiment = "🟢 SLIGHTLY POSITIVE"
        else:
            sentiment = "🟢 POSITIVE"
        
        return sentiment, score, matched_keywords
    
    def check_stock(self, stock: str) -> Dict:
        """Analyze all news for a stock"""
        if stock not in self.alerts:
            return {
                "stock": stock,
                "alerts": 0,
                "sentiment": "⚪ NO NEWS",
                "score": 0.0,
                "articles": [],
                "red_flags": [],
                "recommendation": "PROCEED (No negative news found)",
            }
        
        articles = []
        total_score = 0.0
        red_flags_found = []
        
        for alert_data in self.alerts[stock]:
            if isinstance(alert_data, list):
                articles_list = alert_data
            else:
                articles_list = [alert_data]
            
            for article in articles_list:
                if not isinstance(article, dict):
                    continue
                
                title = article.get("title", "")
                description = article.get("description", "")
                content = article.get("content", "")
                
                # Combine all text
                full_text = f"{title} {description} {content}".strip()
                
                sentiment, score, keywords = self.analyze_sentiment(full_text)
                total_score += score
                
                # Collect critical red flags
                if "🔴 CRITICAL" in sentiment:
                    red_flags_found.append({
                        "title": title,
                        "severity": "CRITICAL",
                        "keywords": keywords
                    })
                elif "🟠 NEGATIVE" in sentiment:
                    red_flags_found.append({
                        "title": title,
                        "severity": "HIGH",
                        "keywords": keywords
                    })
                
                articles.append({
                    "title": title,
                    "sentiment": sentiment,
                    "score": score,
                    "keywords": keywords[:3] if keywords else []
                })
        
        # Determine overall recommendation
        if total_score <= -100:
            recommendation = "🛑 DO NOT TRADE - Critical negative sentiment"
            overall_sentiment = "🔴 CRITICAL NEGATIVE"
        elif total_score <= -40:
            recommendation = "⚠️  CAUTION - Significant negative sentiment, review before trading"
            overall_sentiment = "🟠 NEGATIVE"
        elif total_score <= -10:
            recommendation = "🟡 MONITOR - Minor negative signals, proceed with caution"
            overall_sentiment = "🟡 SLIGHTLY NEGATIVE"
        elif total_score <= 10:
            recommendation = "✅ PROCEED - Neutral sentiment, OK to trade"
            overall_sentiment = "⚪ NEUTRAL"
        else:
            recommendation = "✅ FAVORABLE - Positive sentiment supports trade"
            overall_sentiment = "🟢 POSITIVE"
        
        return {
            "stock": stock,
            "alerts": len(articles),
            "sentiment": overall_sentiment,
            "score": total_score,
            "recommendation": recommendation,
            "articles": sorted(articles, key=lambda x: x["score"]),
            "red_flags": red_flags_found,
        }


def generate_report(parser: NewsAlertParser, output_file: str = None):
    """Generate sentiment check report for all priority stocks"""
    
    print("\n" + "="*80)
    print("📊 SENTIMENT ANALYSIS SANITY CHECK")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    results = {}
    
    # Check all priority stocks
    for category, stocks in PRIORITY_STOCKS.items():
        print(f"\n🔍 {category} PRIORITIES")
        print("-" * 80)
        
        category_results = {}
        
        for stock, details in stocks.items():
            result = parser.check_stock(stock)
            category_results[stock] = result
            results[stock] = result
            
            # Print stock summary
            print(f"\n✦ {stock}")
            print(f"  Strategy: {details.get('strategy', 'N/A')}")
            print(f"  Sentiment: {result['sentiment']}")
            print(f"  Score: {result['score']:+.1f}")
            print(f"  News Count: {result['alerts']}")
            print(f"  ➜ {result['recommendation']}")
            
            # Show critical red flags
            if result['red_flags']:
                print(f"\n  🚨 RED FLAGS DETECTED:")
                for flag in result['red_flags'][:3]:  # Show top 3
                    print(f"     • [{flag['severity']}] {flag['title'][:70]}")
            
            # Show recent articles with negative sentiment
            negative_articles = [a for a in result['articles'] if a['score'] < -5]
            if negative_articles:
                print(f"\n  📰 NEGATIVE NEWS:")
                for article in negative_articles[:2]:  # Show top 2
                    print(f"     • {article['sentiment']} - {article['title'][:65]}")
    
    # Summary table
    print("\n\n" + "="*80)
    print("📋 TRADE DECISION SUMMARY")
    print("="*80 + "\n")
    
    print(f"{'Stock':<8} {'Strategy':<25} {'Sentiment':<20} {'Recommendation':<30}")
    print("-" * 85)
    
    for stock, result in sorted(results.items()):
        strategy = PRIORITY_STOCKS.get("IMMEDIATE", {}).get(stock) or \
                   PRIORITY_STOCKS.get("WATCH", {}).get(stock) or \
                   PRIORITY_STOCKS.get("DIVIDEND", {}).get(stock) or \
                   PRIORITY_STOCKS.get("TECHNICAL", {}).get(stock)
        
        strat_name = strategy.get("strategy", "N/A") if strategy else "N/A"
        
        # Extract action from recommendation
        if "DO NOT TRADE" in result['recommendation']:
            action = "❌ SKIP"
        elif "CAUTION" in result['recommendation']:
            action = "⚠️  VERIFY"
        elif "MONITOR" in result['recommendation']:
            action = "🟡 CAUTION"
        elif "FAVORABLE" in result['recommendation']:
            action = "✅ GO"
        else:
            action = "✅ GO"
        
        print(f"{stock:<8} {strat_name:<25} {result['sentiment']:<20} {action:<30}")
    
    # Save to file
    if output_file:
        with open(output_file, 'w') as f:
            f.write(f"SENTIMENT ANALYSIS SANITY CHECK\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            for stock, result in sorted(results.items()):
                f.write(f"\n{stock}\n")
                f.write(f"  Sentiment: {result['sentiment']}\n")
                f.write(f"  Score: {result['score']:+.1f}\n")
                f.write(f"  Recommendation: {result['recommendation']}\n")
                
                if result['red_flags']:
                    f.write(f"  Red Flags: {len(result['red_flags'])}\n")
                    for flag in result['red_flags'][:2]:
                        f.write(f"    - {flag['title']}\n")
    
    return results


if __name__ == "__main__":
    news_dir = "/Users/arifpras/Library/CloudStorage/Dropbox/perisai/stockscraper/data/news_cache"
    
    parser = NewsAlertParser(news_dir)
    results = generate_report(parser)
    
    # Save report
    output_file = f"data/news_cache/SENTIMENT_CHECK_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    print(f"\n✅ Report saved to: {output_file}")
