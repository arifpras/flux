import re
from pathlib import Path

brokers_path = Path('/Users/arifpras/Library/CloudStorage/Dropbox/perisai/stockscraper/brokers')

def extract_buy_lists(text):
    lines = [l.strip() for l in text.split('\n')]
    try:
        buy_idx = lines.index('Buy')
    except ValueError:
        return None
    end_idx = None
    for i in range(buy_idx + 1, len(lines)):
        if lines[i] == 'Sell':
            end_idx = i
            break
    if end_idx is None:
        end_idx = len(lines)
    buy_block = lines[buy_idx + 1 : end_idx]

    def grab_after(label):
        try:
            idx = buy_block.index(label)
        except ValueError:
            return []
        vals = []
        for l in buy_block[idx + 1 :]:
            if not l:
                continue
            if l in ('Jan 30, 2026', 'B.Lot', 'B.Avg', '='):
                break
            if not re.search(r'[0-9]', l):
                break
            vals.append(l)
        return vals

    try:
        bval_idx = buy_block.index('B.Val')
    except ValueError:
        return None

    stocks = [l for l in buy_block[:bval_idx] if l and re.fullmatch(r'[A-Z]{4}', l)]
    bavgs = grab_after('B.Avg')
    return stocks, bavgs


def collect_prices(target_stock):
    prices = []
    for txt_file in brokers_path.glob('*.txt'):
        text = txt_file.read_text(encoding='utf-8', errors='ignore')
        if 'Jan 30, 2026' not in text:
            continue
        sec_match = re.search(r'([A-Z].+?Sekuritas.*?) v', text)
        broker = sec_match.group(1) if sec_match else txt_file.stem

        if 'DU KAF' in text:
            for m in re.finditer(rf'\b({target_stock})\b\s+([0-9.]+[MBK]?)\s+([0-9,]+)\s+([0-9,]+)', text):
                avg = m.group(4).replace(',', '')
                if avg.isdigit():
                    prices.append((broker, int(avg)))
            continue

        res = extract_buy_lists(text)
        if not res:
            continue
        stocks, bavgs = res
        if target_stock in stocks:
            idx = stocks.index(target_stock)
            if idx < len(bavgs):
                avg = re.sub(r'[^0-9]', '', bavgs[idx])
                if avg:
                    prices.append((broker, int(avg)))
    return prices

for stock in ['ICBP', 'UNTR']:
    prices = collect_prices(stock)
    print(f"{stock} prices by broker (OCR-aligned):")
    for broker, price in sorted(prices, key=lambda x: x[1]):
        print(f"{price}\t{broker}")
    print()
