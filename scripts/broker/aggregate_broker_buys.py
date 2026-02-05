"""
Aggregate foreign broker buy data from Jan 30, 2026 screenshots
"""

import re
from pathlib import Path
from collections import defaultdict

def parse_buy_data(text):
    """Parse buy data from OCR text"""
    buy_data = []
    
    # Find the Buy section
    lines = text.split('\n')
    in_buy_section = False
    
    for i, line in enumerate(lines):
        # Check if we're in buy section
        if line.strip() == 'Buy':
            in_buy_section = True
            continue
        
        # Stop at Sell section
        if line.strip() == 'Sell':
            in_buy_section = False
            break
        
        if in_buy_section and line.strip():
            # Try to match stock code pattern (4 uppercase letters)
            match = re.match(r'^([A-Z]{4})', line.strip())
            if match:
                stock_code = match.group(1)
                
                # Try to extract value and lot from the corresponding lines
                # Look for B.Val and B.Lot in nearby lines
                value_line = None
                lot_line = None
                avg_line = None
                
                # Search forward in the text for value, lot, and avg
                for j in range(i+1, min(i+10, len(lines))):
                    if 'B.Val' in lines[j] or 'B' in lines[j]:
                        # Extract numbers from the value column
                        value_match = re.search(r'([\d.]+[BMK]?)', lines[j])
                        if value_match:
                            value_line = value_match.group(1)
                    
                buy_data.append({
                    'stock': stock_code,
                    'line': line
                })
    
    return buy_data

def analyze_all_brokers():
    """Analyze all broker screenshots"""
    brokers_path = Path("/Users/arifpras/Library/CloudStorage/Dropbox/perisai/stockscraper/brokers")
    txt_files = sorted(brokers_path.glob("*.txt"))
    
    # Store buy data by stock
    stock_buys = defaultdict(lambda: {'count': 0, 'brokers': [], 'total_mentions': 0})
    
    # Also store raw data per broker
    broker_data = {}
    
    for txt_file in txt_files:
        with open(txt_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Check if it's Jan 30, 2026 data
        if 'Jan 30, 2026' not in text:
            continue
        
        # Extract broker name
        broker_match = re.search(r'([A-Z].+?Sekuritas.*?) v', text)
        broker_name = broker_match.group(1) if broker_match else txt_file.stem
        
        # Parse buy data
        buys = parse_buy_data(text)
        
        if buys:
            broker_data[broker_name] = buys
            print(f"\n{broker_name}:")
            print("Buy list:")
            for buy in buys[:10]:  # Show first 10
                print(f"  - {buy['stock']}")
            
            # Aggregate by stock
            for buy in buys:
                stock = buy['stock']
                stock_buys[stock]['count'] += 1
                stock_buys[stock]['brokers'].append(broker_name)
                stock_buys[stock]['total_mentions'] += 1
    
    # Sort by most bought
    print("\n" + "=" * 80)
    print("MOST BOUGHT STOCKS BY FOREIGN BROKERS - JAN 30, 2026")
    print("=" * 80)
    print()
    
    sorted_stocks = sorted(stock_buys.items(), key=lambda x: x[1]['count'], reverse=True)
    
    print(f"{'Stock':<10} {'# Brokers':<15} {'Brokers'}")
    print("-" * 80)
    
    for stock, data in sorted_stocks[:30]:
        broker_list = ', '.join(data['brokers'][:3])
        if len(data['brokers']) > 3:
            broker_list += f" + {len(data['brokers'])-3} more"
        print(f"{stock:<10} {data['count']:<15} {broker_list}")
    
    # Save results
    output_path = brokers_path.parent / 'results' / '20260130_most_bought_stocks.txt'
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write("FOREIGN BROKER BUY ACTIVITY - JAN 30, 2026\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"{'Stock':<10} {'# Brokers':<15} {'Brokers'}\n")
        f.write("-" * 80 + "\n")
        
        for stock, data in sorted_stocks:
            broker_list = ', '.join(data['brokers'])
            f.write(f"{stock:<10} {data['count']:<15} {broker_list}\n")
    
    print(f"\nFull report saved to: {output_path}")

if __name__ == "__main__":
    analyze_all_brokers()
