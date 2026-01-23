#!/usr/bin/env python3
"""
Sentiment Analysis for Recommended Stocks
Checks news sentiment for all stocks recommended in 20260122_STRATEGY_REPORT_CONCISE.txt
Prevents entry into stocks with negative news
"""

import json
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import re

# RECOMMENDED STOCKS FROM REPORT
RECOMMENDED_STOCKS = {
    # Strategy 1: Dividend Income
    "ADRO": {"strategy": "Dividend Income", "yield": "114%"},
    "PTBA": {"strategy": "Dividend Income", "yield": "72%"},
    "ITMG": {"strategy": "Dividend Income", "yield": "66%"},
    "LPPF": {"strategy": "Dividend Income", "yield": "55%"},
    "BSSR": {"strategy": "Dividend Income", "yield": "50%"},
    "MEGA": {"strategy": "Dividend Income (Feb/Mar)", "yield": "5-6%"},
    
    # Strategy 2: Foreign Accumulation on Weakness
    "BRMS": {"strategy": "Foreign Accumulation", "foreign_buy": "139M"},
    "ELTY": {"strategy": "Foreign Accumulation", "foreign_buy": "92M", "warning": "EXTREME DECLINE"},
    "BKSL": {"strategy": "Foreign Accumulation", "foreign_buy": "62M"},
    "GMFI": {"strategy": "Foreign Accumulation", "foreign_buy": "56M"},
    "ASII": {"strategy": "Foreign Accumulation", "foreign_buy": "52M"},
    "PTRO": {"strategy": "Foreign Accumulation", "foreign_buy": "39M"},
    "CTRA": {"strategy": "Foreign Accumulation", "foreign_buy": "30M"},
    "KLBF": {"strategy": "Foreign Accumulation", "foreign_buy": "21M"},
    
    # Strategy 3: Foreign Accumulation + Fundamentals (HIGH CONVICTION)
    "CNMA": {"strategy": "Foreign + Fundamentals", "conviction": "HIGH"},
    "UNTR": {"strategy": "Foreign + Fundamentals / Technical", "conviction": "HIGHEST"},
    
    # Strategy 4: Short-term Momentum
    "BBKP": {"strategy": "Momentum", "momentum": "Accelerating"},
    "PBRX": {"strategy": "Momentum", "momentum": "Breakout"},
    "ELIT": {"strategy": "Momentum", "momentum": "Extended"},
    "PSKT": {"strategy": "Momentum", "momentum": "Continuing"},
    "KREN": {"strategy": "Momentum", "momentum": "Volatile"},
    
    # Strategy 6: Technical Oversold + Fundamentals (HIGH CONVICTION)
    "DGIK": {"strategy": "Technical Oversold", "conviction": "HIGHEST", "priority": 1},
    "MERK": {"strategy": "Technical Oversold", "conviction": "HIGHEST"},
    "SUNI": {"strategy": "Technical Oversold", "conviction": "HIGH"},
}

# NEGATIVE KEYWORDS FOR SENTIMENT ANALYSIS
NEGATIVE_KEYWORDS = [
    "collapse", "crash", "plunge", "bankruptcy", "bankrupt", "default",
    "fraud", "scandal", "corruption", "corruption investigation",
    "suspend", "suspended", "halt", "halted", "delisting",
    "massive loss", "loss", "weak", "weakness", "weakness",
    "downgrade", "downgraded", "sell", "negative", "concern",
    "risk", "investigate", "investigation", "police", "kpk",
    "layoff", "layoffs", "retrench", "restructure", "close",
    "accident", "incident", "incident", "disaster", "emergency",
    "lawsuit", "suit", "legal", "court", "court", "judge",
    "dividend cut", "dividend suspension", "no dividend",
    "miss earnings", "missed earnings", "beat miss",
    "guidance lower", "lower guidance", "outlook negative",
    "war", "conflict", "crisis", "emergency", "disaster",
    "supply chain", "supply disruption", "disruption",
    "recall", "product recall", "defect", "defective",
    "death", "fatality", "fatalities", "damage", "damage",
    "debt", "debt issue", "covenant", "default", "refinance",
    "ebitda negative", "negative ebitda", "burn",
]

POSITIVE_KEYWORDS = [
    "recovery", "recover", "rebound", "bounce", "surge",
    "approval", "approved", "approved", "partnership", "partner",
    "deal", "deal", "acquisition", "acquire", "new contract",
    "profit", "profitable", "profitable", "growth", "growing",
    "upgrade", "upgraded", "upgraded", "outperform", "beat",
    "innovation", "innovative", "breakthrough", "breakthrough",
    "dividend", "dividend increase", "special dividend",
    "expansion", "expand", "expand", "new project", "project",
    "pipeline", "promising", "success", "successful", "successful",
    "rally", "rally", "strength", "strong", "strength",
]

class SentimentAnalyzer:
    def __init__(self, news_cache_dir):
        self.news_cache_dir = Path(news_cache_dir)
        self.stock_news = defaultdict(list)
        self.sentiment_scores = {}
        
    def load_news_cache(self):
        """Load all news from cache"""
        if not self.news_cache_dir.exists():
            print(f"⚠️  News cache directory not found: {self.news_cache_dir}")
            return False
            
        for file in self.news_cache_dir.glob("*.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            ticker = item.get('ticker', '').upper()
                            if ticker in RECOMMENDED_STOCKS:
                                self.stock_news[ticker].append(item)
                    elif isinstance(data, dict):
                        ticker = data.get('ticker', '').upper()
                        if ticker in RECOMMENDED_STOCKS:
                            self.stock_news[ticker].append(data)
            except Exception as e:
                print(f"⚠️  Error loading {file}: {e}")
                
        return len(self.stock_news) > 0
    
    def analyze_sentiment(self, text):
        """Analyze sentiment of text"""
        if not text:
            return 0, []
        
        text_lower = text.lower()
        negative_count = sum(1 for word in NEGATIVE_KEYWORDS if word.lower() in text_lower)
        positive_count = sum(1 for word in POSITIVE_KEYWORDS if word.lower() in text_lower)
        
        matched_negative = [word for word in NEGATIVE_KEYWORDS if word.lower() in text_lower]
        matched_positive = [word for word in POSITIVE_KEYWORDS if word.lower() in text_lower]
        
        net_score = positive_count - negative_count
        return net_score, matched_negative, matched_positive
    
    def analyze_all_stocks(self):
        """Analyze sentiment for all recommended stocks"""
        print("=" * 85)
        print("SENTIMENT ANALYSIS FOR RECOMMENDED STOCKS".center(85))
        print("=" * 85)
        print(f"\nAnalysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"Stocks Analyzed: {len(RECOMMENDED_STOCKS)}")
        print(f"Stocks with News Found: {len(self.stock_news)}")
        print()
        
        results = {}
        
        # Group by strategy
        strategies = defaultdict(list)
        for ticker in sorted(RECOMMENDED_STOCKS.keys()):
            strategy = RECOMMENDED_STOCKS[ticker]["strategy"]
            strategies[strategy].append(ticker)
        
        # Analyze by strategy
        for strategy in sorted(strategies.keys()):
            print(f"\n{'─' * 85}")
            print(f"📊 {strategy.upper()}")
            print(f"{'─' * 85}")
            
            for ticker in strategies[strategy]:
                info = RECOMMENDED_STOCKS[ticker]
                news_articles = self.stock_news.get(ticker, [])
                
                if not news_articles:
                    print(f"\n{ticker:8} │ ✅ NO NEWS FOUND (CLEAN)")
                    results[ticker] = {
                        "ticker": ticker,
                        "strategy": strategy,
                        "sentiment": "CLEAN",
                        "risk_level": "LOW",
                        "news_count": 0,
                        "recommendation": "PROCEED - No negative news detected"
                    }
                else:
                    # Analyze all news for this stock
                    total_sentiment = 0
                    risk_flags = []
                    recent_articles = []
                    
                    for article in news_articles[:10]:  # Last 10 articles
                        title = article.get('title', '')
                        content = article.get('content', '')
                        sentiment, neg_keywords, pos_keywords = self.analyze_sentiment(
                            f"{title} {content}"
                        )
                        total_sentiment += sentiment
                        
                        if neg_keywords:
                            risk_flags.extend(neg_keywords)
                        
                        if sentiment < -2:  # Strongly negative
                            date = article.get('date', 'Unknown')
                            recent_articles.append({
                                "date": date,
                                "title": title[:70],
                                "sentiment": sentiment,
                                "flags": neg_keywords[:3]
                            })
                    
                    avg_sentiment = total_sentiment / len(news_articles)
                    unique_risk_flags = list(set(risk_flags))[:5]
                    
                    # Determine risk level
                    if avg_sentiment < -3 or len([a for a in recent_articles if a["sentiment"] < -2]) >= 2:
                        risk_level = "🔴 HIGH"
                        recommendation = "CAUTION - Multiple negative signals"
                    elif avg_sentiment < -1 or len(unique_risk_flags) >= 3:
                        risk_level = "🟡 MEDIUM"
                        recommendation = "CAREFUL - Monitor latest news"
                    else:
                        risk_level = "🟢 LOW"
                        recommendation = "PROCEED - Sentiment acceptable"
                    
                    print(f"\n{ticker:8} │ Articles: {len(news_articles):2} │ Sentiment: {avg_sentiment:+.1f} │ {risk_level}")
                    
                    if unique_risk_flags:
                        print(f"         │ Red flags: {', '.join(unique_risk_flags)}")
                    
                    if recent_articles:
                        print(f"         │ Recent negatives:")
                        for article in recent_articles[:2]:
                            print(f"         │   • [{article['date']}] {article['title']}...")
                    
                    print(f"         │ ➜ {recommendation}")
                    
                    results[ticker] = {
                        "ticker": ticker,
                        "strategy": strategy,
                        "sentiment": "MIXED" if avg_sentiment > -3 else "NEGATIVE",
                        "sentiment_score": round(avg_sentiment, 2),
                        "risk_level": risk_level.split()[1],
                        "risk_flags": unique_risk_flags,
                        "news_count": len(news_articles),
                        "recommendation": recommendation
                    }
        
        return results
    
    def generate_priority_report(self, results):
        """Generate priority action report"""
        print(f"\n\n{'=' * 85}")
        print("PRIORITY RECOMMENDATIONS".center(85))
        print("=" * 85)
        
        # Priority 1 stocks (from report)
        priority_1 = ["DGIK", "ASII", "BBKP"]
        
        print("\n🚀 PRIORITY 1 STOCKS (Execute if sentiment clear):\n")
        for ticker in priority_1:
            if ticker in results:
                r = results[ticker]
                status = "✅ PROCEED" if r["risk_level"] == "LOW" else f"⚠️  {r['risk_level']} - {r['recommendation']}"
                print(f"{ticker:8} │ {status}")
                if r.get("risk_flags"):
                    print(f"         │ Flags: {', '.join(r['risk_flags'])}")
        
        # Alert on HIGH RISK stocks
        print("\n\n⛔ HIGH RISK ALERTS:\n")
        high_risk = [r for r in results.values() if "HIGH" in r.get("risk_level", "")]
        if high_risk:
            for r in high_risk:
                print(f"{r['ticker']:8} │ AVOID - {r['recommendation']}")
                print(f"         │ Sentiment: {r.get('sentiment_score', 'N/A')}")
        else:
            print("✅ No high-risk stocks detected")
        
        # Summary stats
        print(f"\n\n{'─' * 85}")
        print("SUMMARY STATISTICS")
        print(f"{'─' * 85}")
        low_risk = len([r for r in results.values() if r["risk_level"] == "LOW"])
        medium_risk = len([r for r in results.values() if r["risk_level"] == "MEDIUM"])
        high_risk = len([r for r in results.values() if r["risk_level"] == "HIGH"])
        
        print(f"\n✅ Low Risk (proceed):     {low_risk:3} stocks")
        print(f"🟡 Medium Risk (caution):  {medium_risk:3} stocks")
        print(f"🔴 High Risk (avoid):      {high_risk:3} stocks")
        print(f"📭 No news available:      {len(RECOMMENDED_STOCKS) - len(results):3} stocks")
        
        proceed_rate = (low_risk + (medium_risk * 0.5)) / len(RECOMMENDED_STOCKS) * 100
        print(f"\n📊 Overall Confidence: {proceed_rate:.0f}% of stocks safe to trade")

def main():
    workspace = Path("/Users/arifpras/Library/CloudStorage/Dropbox/perisai/stockscraper")
    news_cache_dir = workspace / "data" / "news_cache"
    
    analyzer = SentimentAnalyzer(news_cache_dir)
    
    # Load news
    print("🔍 Loading news cache...")
    found_news = analyzer.load_news_cache()
    print(f"✓ Found news for {len(analyzer.stock_news)} stocks\n")
    
    # Analyze sentiment
    results = analyzer.analyze_all_stocks()
    
    # Generate priority report
    analyzer.generate_priority_report(results)
    
    # Save results
    output_file = workspace / "results" / "20260123_SENTIMENT_ANALYSIS.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n\n✅ Results saved to: {output_file}")

if __name__ == "__main__":
    main()
