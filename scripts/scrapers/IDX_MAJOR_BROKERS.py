"""
Major Indonesian Stock Brokers (IDX)
Reference list of top brokers by market activity and AUM
"""

# Top 20 Most Active Brokers on IDX
MAJOR_BROKERS = {
    # Big 5 - Highest Trading Volume
    'YP': {
        'name': 'PT Yulie Sekurindo Tbk',
        'type': 'Retail & Institutional',
        'reputation': 'Very High',
        'known_for': 'High frequency trading, retail dominance'
    },
    'MG': {
        'name': 'PT Mirae Asset Sekuritas Indonesia',
        'type': 'Foreign Institutional',
        'reputation': 'Very High',
        'known_for': 'Korean institutional money, smart money'
    },
    'ZP': {
        'name': 'PT Phillip Sekuritas Indonesia',
        'type': 'Retail & Foreign',
        'reputation': 'High',
        'known_for': 'Singapore-based, retail platform'
    },
    'AK': {
        'name': 'PT Indo Premier Sekuritas',
        'type': 'Institutional',
        'reputation': 'Very High',
        'known_for': 'IPOT platform, aggressive growth'
    },
    'SG': {
        'name': 'PT Samuel Sekuritas Indonesia',
        'type': 'Institutional',
        'reputation': 'High',
        'known_for': 'Large institutional clients'
    },
    
    # Major Local Brokers
    'KK': {
        'name': 'PT Kresna Graha Sekurindo Tbk',
        'type': 'Institutional',
        'reputation': 'High',
        'known_for': 'Smart money, consistent net buy'
    },
    'NH': {
        'name': 'PT Sinarmas Sekuritas',
        'type': 'Bank-affiliated',
        'reputation': 'Very High',
        'known_for': 'Sinarmas Group, big accumulator'
    },
    'OP': {
        'name': 'PT Osman Penjualan Efek',
        'type': 'Retail',
        'reputation': 'Medium',
        'known_for': 'Small-cap specialist'
    },
    'EV': {
        'name': 'PT Erdikha Elit Sekuritas',
        'type': 'Retail',
        'reputation': 'Medium',
        'known_for': 'Active in banking stocks'
    },
    'HS': {
        'name': 'PT Henan Putihrai Sekuritas',
        'type': 'Institutional',
        'reputation': 'High',
        'known_for': 'Blue chip focus'
    },
    
    # Foreign Brokers
    'CS': {
        'name': 'PT Credit Suisse Sekuritas Indonesia',
        'type': 'Foreign Institutional',
        'reputation': 'Very High',
        'known_for': 'Swiss banking, large caps only'
    },
    'MU': {
        'name': 'PT Mandiri Sekuritas',
        'type': 'Bank-affiliated',
        'reputation': 'Very High',
        'known_for': 'Bank Mandiri, state-owned, institutional'
    },
    'BD': {
        'name': 'PT BNI Sekuritas',
        'type': 'Bank-affiliated',
        'reputation': 'Very High',
        'known_for': 'BNI Bank, conservative'
    },
    'BR': {
        'name': 'PT BRI Danareksa Sekuritas',
        'type': 'Bank-affiliated',
        'reputation': 'Very High',
        'known_for': 'BRI Bank, retail strong'
    },
    'DB': {
        'name': 'PT Deutsche Sekuritas Indonesia',
        'type': 'Foreign Institutional',
        'reputation': 'Very High',
        'known_for': 'German bank, big player'
    },
    'MC': {
        'name': 'PT Merrill Lynch Sekuritas Indonesia',
        'type': 'Foreign Institutional',
        'reputation': 'Very High',
        'known_for': 'BofA, institutional only'
    },
    'JP': {
        'name': 'PT JP Morgan Sekuritas Indonesia',
        'type': 'Foreign Institutional',
        'reputation': 'Very High',
        'known_for': 'US institutional, smart money'
    },
    'GS': {
        'name': 'PT Goldman Sachs Sekuritas Indonesia',
        'type': 'Foreign Institutional',
        'reputation': 'Very High',
        'known_for': 'Smart money indicator'
    },
    'MS': {
        'name': 'PT Morgan Stanley Sekuritas Indonesia',
        'type': 'Foreign Institutional',
        'reputation': 'Very High',
        'known_for': 'Institutional powerhouse'
    },
    'UB': {
        'name': 'PT UBS Sekuritas Indonesia',
        'type': 'Foreign Institutional',
        'reputation': 'Very High',
        'known_for': 'Swiss institutional, large caps'
    }
}

# Broker Categories for Analysis
BROKER_CATEGORIES = {
    'smart_money': ['MG', 'KK', 'JP', 'GS', 'MS', 'CS', 'UB', 'NH'],  # Follow these
    'foreign_institutional': ['MG', 'CS', 'DB', 'MC', 'JP', 'GS', 'MS', 'UB'],
    'local_institutional': ['KK', 'NH', 'SG', 'HS', 'AK'],
    'bank_affiliated': ['MU', 'BD', 'BR', 'NH'],  # Conservative, safe
    'retail_dominant': ['YP', 'ZP', 'AK', 'OP', 'EV'],  # Often manipulation targets
    'high_frequency': ['YP', 'AK', 'ZP'],  # Fast movers
}

# Broker Reputation Scoring (1-10)
BROKER_SCORES = {
    # 9-10: Ultra reliable, institutional smart money
    'GS': 10,  # Goldman Sachs - Best smart money indicator
    'JP': 10,  # JP Morgan - Institutional leader
    'MS': 9,   # Morgan Stanley
    'MG': 9,   # Mirae Asset - Korean smart money
    'UB': 9,   # UBS
    
    # 7-8: Reliable institutional
    'CS': 8,
    'DB': 8,
    'MC': 8,
    'KK': 8,   # Kresna - Local smart money
    'NH': 8,   # Sinarmas - Big accumulator
    'MU': 7,   # Mandiri Sekuritas
    'BD': 7,   # BNI Sekuritas
    'BR': 7,   # BRI Danareksa
    
    # 5-6: Mixed retail/institutional
    'AK': 6,   # Indo Premier - Retail platform
    'ZP': 6,   # Phillip Securities
    'SG': 6,   # Samuel
    'HS': 6,   # Henan Putihrai
    
    # 3-4: Retail dominant (watch for manipulation)
    'YP': 4,   # Yulie - High retail volume
    'OP': 3,   # Osman - Small cap
    'EV': 3,   # Erdikha
}


def get_broker_info(broker_code: str) -> dict:
    """Get information about a broker."""
    return MAJOR_BROKERS.get(broker_code, {
        'name': f'Broker {broker_code}',
        'type': 'Unknown',
        'reputation': 'Unknown',
        'known_for': 'No information available'
    })


def is_smart_money(broker_code: str) -> bool:
    """Check if broker is considered smart money."""
    return broker_code in BROKER_CATEGORIES['smart_money']


def is_foreign_broker(broker_code: str) -> bool:
    """Check if broker is foreign institutional."""
    return broker_code in BROKER_CATEGORIES['foreign_institutional']


def get_broker_score(broker_code: str) -> int:
    """Get reputation score (1-10)."""
    return BROKER_SCORES.get(broker_code, 5)  # Default: medium


def print_broker_directory():
    """Print formatted directory of all brokers."""
    print("=" * 100)
    print(" 🏢 IDX MAJOR BROKERS DIRECTORY")
    print("=" * 100)
    
    categories = [
        ('💎 SMART MONEY (Follow These)', 'smart_money'),
        ('🌍 FOREIGN INSTITUTIONAL', 'foreign_institutional'),
        ('🏦 BANK-AFFILIATED', 'bank_affiliated'),
        ('👥 RETAIL DOMINANT', 'retail_dominant'),
    ]
    
    for title, category in categories:
        print(f"\n{title}")
        print("-" * 100)
        
        brokers = BROKER_CATEGORIES[category]
        for code in brokers:
            info = MAJOR_BROKERS.get(code, {})
            score = BROKER_SCORES.get(code, 5)
            stars = '⭐' * (score // 2)
            
            print(f"  {code:4s} | {info.get('name', 'N/A'):50s} | {stars:10s} ({score}/10)")
            print(f"       └─ {info.get('known_for', 'N/A')}")
    
    print("\n" + "=" * 100)


def analyze_broker_mix(broker_list: list) -> dict:
    """Analyze the composition of brokers in a list."""
    analysis = {
        'total': len(broker_list),
        'smart_money_count': 0,
        'foreign_count': 0,
        'retail_count': 0,
        'avg_score': 0,
        'smart_money_brokers': [],
        'foreign_brokers': [],
    }
    
    scores = []
    for broker in broker_list:
        if is_smart_money(broker):
            analysis['smart_money_count'] += 1
            analysis['smart_money_brokers'].append(broker)
        
        if is_foreign_broker(broker):
            analysis['foreign_count'] += 1
            analysis['foreign_brokers'].append(broker)
        
        if broker in BROKER_CATEGORIES['retail_dominant']:
            analysis['retail_count'] += 1
        
        scores.append(get_broker_score(broker))
    
    analysis['avg_score'] = sum(scores) / len(scores) if scores else 0
    
    return analysis


if __name__ == "__main__":
    print_broker_directory()
    
    # Example usage
    print("\n📊 BROKER ANALYSIS EXAMPLES:")
    print("=" * 100)
    
    # Example 1: Check specific broker
    broker = 'GS'
    info = get_broker_info(broker)
    print(f"\n🔍 {broker} - {info['name']}")
    print(f"   Type: {info['type']}")
    print(f"   Score: {get_broker_score(broker)}/10")
    print(f"   Smart Money: {'✅ YES' if is_smart_money(broker) else '❌ NO'}")
    print(f"   Known For: {info['known_for']}")
    
    # Example 2: Analyze broker mix
    print("\n📈 Analyzing broker activity in BBRI:")
    sample_brokers = ['GS', 'JP', 'YP', 'AK', 'NH']
    analysis = analyze_broker_mix(sample_brokers)
    
    print(f"   Total Brokers: {analysis['total']}")
    print(f"   Smart Money: {analysis['smart_money_count']} brokers {analysis['smart_money_brokers']}")
    print(f"   Foreign: {analysis['foreign_count']} brokers")
    print(f"   Retail: {analysis['retail_count']} brokers")
    print(f"   Average Score: {analysis['avg_score']:.1f}/10")
    
    if analysis['smart_money_count'] >= 2:
        print("   🚀 SIGNAL: Strong institutional interest!")
    elif analysis['retail_count'] > analysis['smart_money_count']:
        print("   ⚠️  WARNING: Retail-dominated (potential manipulation)")
    
    print("\n" + "=" * 100)
