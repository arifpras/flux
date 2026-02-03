import re
from pathlib import Path
from collections import defaultdict

brokers_path = Path('/Users/arifpras/Library/CloudStorage/Dropbox/perisai/stockscraper/brokers')

def extract_sections(text):
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
    bvals = grab_after('B.Val')
    blots = grab_after('B.Lot')
    bavgs = grab_after('B.Avg')
    return stocks, bvals, blots, bavgs


price_by_stock = defaultdict(list)
count_by_stock = defaultdict(set)

for txt_file in brokers_path.glob('*.txt'):
    text = txt_file.read_text(encoding='utf-8', errors='ignore')
    if 'Jan 30, 2026' not in text:
        continue
    sec_match = re.search(r'([A-Z].+?Sekuritas.*?) v', text)
    broker = sec_match.group(1) if sec_match else txt_file.stem

    if 'DU KAF' in text:
        for m in re.finditer(r'\b([A-Z]{4})\b\s+([0-9.]+[MBK]?)\s+([0-9,]+)\s+([0-9,]+)', text):
            stock = m.group(1)
            avg = m.group(4).replace(',', '')
            try:
                price = float(avg)
            except ValueError:
                continue
            price_by_stock[stock].append(price)
            count_by_stock[stock].add(broker)
        continue

    res = extract_sections(text)
    if not res:
        continue
    stocks, bvals, blots, bavgs = res

    for i, stock in enumerate(stocks):
        if i >= len(bavgs):
            continue
        avg = bavgs[i]
        avg = avg.replace(',', '')
        avg = re.sub(r'[^0-9.]', '', avg)
        if not avg:
            continue
        try:
            price = float(avg)
        except ValueError:
            continue
        price_by_stock[stock].append(price)
        count_by_stock[stock].add(broker)

rows = []
for stock, brokers in count_by_stock.items():
    if len(brokers) >= 5:
        prices = price_by_stock.get(stock, [])
        if prices:
            pmin = min(prices)
            pmax = max(prices)
            pavg = sum(prices) / len(prices)
        else:
            pmin = pmax = pavg = None
        rows.append((stock, len(brokers), pmin, pmax, pavg))

rows.sort(key=lambda r: (-r[1], r[0]))

print('STOCK\tBROKERS\tPRICE_MIN\tPRICE_MAX\tPRICE_AVG')
for r in rows:
    print(f"{r[0]}\t{r[1]}\t{'' if r[2] is None else int(r[2])}\t{'' if r[3] is None else int(r[3])}\t{'' if r[4] is None else int(r[4])}")
