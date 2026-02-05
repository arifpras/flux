from pathlib import Path
import re
import pandas as pd
from PIL import Image
import pytesseract

image_path = Path('/Users/arifpras/Library/CloudStorage/Dropbox/perisai/stockscraper/brokers/kaf_sekuritas.png')
output_path = Path('/Users/arifpras/Library/CloudStorage/Dropbox/perisai/stockscraper/brokers/csv/kaf_sekuritas.csv')

text = pytesseract.image_to_string(Image.open(image_path))
lines = [l.strip() for l in text.splitlines() if l.strip()]

broker = None
for l in lines[:25]:
    if 'Sekuritas' in l or 'Securities' in l:
        broker = l.strip()
        break
broker = broker or image_path.stem

SECTION_MARKERS = {
    'buy','sell','b.val','b.lot','b.avg','s.val','s.lot','s.avg','allinvestor','regular','net'
}

def extract_stocks_between(start_token, end_tokens):
    collecting = False
    stocks = []
    for l in lines:
        ll = l.lower().strip()
        if ll == start_token:
            collecting = True
            continue
        if collecting:
            if any(ll.startswith(t) or t in ll for t in end_tokens):
                break
            for code in re.findall(r'\b[A-Z]{4}\b', l):
                stocks.append(code)
    return stocks

def parse_numbers_with_units(text):
    results = []
    for match in re.finditer(r'(\d[\d,]*\.?\d*)\s*([KMB])?', text, flags=re.IGNORECASE):
        num = match.group(1)
        unit = match.group(2)
        if not num:
            continue
        try:
            val = float(num.replace(',', ''))
        except ValueError:
            continue
        if unit:
            unit = unit.upper()
            if unit == 'K':
                val *= 1e3
            elif unit == 'M':
                val *= 1e6
            elif unit == 'B':
                val *= 1e9
        results.append(val)
    return results

def extract_metric_numbers(label):
    values = []
    collecting = False
    for l in lines:
        ll = l.lower().strip()
        if ll.startswith(label):
            collecting = True
            values.extend(parse_numbers_with_units(l))
            continue
        if collecting:
            if any(marker in ll for marker in SECTION_MARKERS) and not ll.startswith(label):
                break
            values.extend(parse_numbers_with_units(l))
    return values

def align_lengths(stocks, *arrays):
    if not stocks:
        return stocks, [list(a) for a in arrays]
    min_len = min([len(stocks)] + [len(a) for a in arrays if a is not None])
    stocks = stocks[:min_len]
    aligned = [list(a[:min_len]) for a in arrays]
    return stocks, aligned

def build_table(side, stocks, vals, lots, avgs):
    rows = []
    for i, stock in enumerate(stocks):
        rows.append({
            'broker': broker,
            'side': side,
            'stock': stock,
            'val': vals[i] if i < len(vals) else None,
            'lot': lots[i] if i < len(lots) else None,
            'avg': avgs[i] if i < len(avgs) else None,
            'source_image': image_path.name,
        })
    return rows

buy_stocks = extract_stocks_between('buy', ('b.val','sell'))
sell_stocks = extract_stocks_between('sell', ('s.val','allinvestor','regular'))

b_val = extract_metric_numbers('b.val')
b_lot = extract_metric_numbers('b.lot')
b_avg = extract_metric_numbers('b.avg')

s_val = extract_metric_numbers('s.val')
s_lot = extract_metric_numbers('s.lot')
s_avg = extract_metric_numbers('s.avg')

buy_stocks, (b_val, b_lot, b_avg) = align_lengths(buy_stocks, b_val, b_lot, b_avg)
sell_stocks, (s_val, s_lot, s_avg) = align_lengths(sell_stocks, s_val, s_lot, s_avg)

rows = []
rows += build_table('Buy', buy_stocks, b_val, b_lot, b_avg)
rows += build_table('Sell', sell_stocks, s_val, s_lot, s_avg)

df = pd.DataFrame(rows)
if df.empty:
    raise SystemExit('No rows extracted')

df.to_csv(output_path, index=False)
print(f'Overwrote: {output_path}')
print(f'Rows: {len(df)}')
