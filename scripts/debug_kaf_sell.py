from pathlib import Path
import re
from PIL import Image
import pytesseract

image_path = Path('/Users/arifpras/Library/CloudStorage/Dropbox/perisai/stockscraper/brokers/kaf_sekuritas.png')
text = pytesseract.image_to_string(Image.open(image_path))
lines = [l.strip() for l in text.splitlines() if l.strip()]

SECTION_MARKERS = {
    'buy','sell','b.val','b.lot','b.avg','s.val','s.lot','s.avg','allinvestor','regular','net'
}

def extract_stocks_in_window(start_token, end_tokens):
    lowered = [l.lower().strip() for l in lines]
    start_idx = None
    end_idx = None
    for i, ll in enumerate(lowered):
        if start_token in ll:
            start_idx = i + 1
            break
    if start_idx is None:
        return []
    for j in range(start_idx, len(lowered)):
        ll = lowered[j]
        if any(ll.startswith(t) or t in ll for t in end_tokens):
            end_idx = j
            break
    if end_idx is None:
        end_idx = len(lines)
    stocks = []
    for l in lines[start_idx:end_idx]:
        stocks += re.findall(r'\b[A-Z]{4}\b', l)
    return stocks

def parse_numbers_with_units(text):
    results = []
    for match in re.finditer(r'(\d[\d,]*\.?\d*)\s*([KMB])?', text, flags=re.IGNORECASE):
        num = match.group(1)
        unit = match.group(2)
        if not num:
            continue
        val = float(num.replace(',', ''))
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
        if label in ll:
            collecting = True
            values.extend(parse_numbers_with_units(l))
            continue
        if collecting:
            if any(marker in ll for marker in SECTION_MARKERS) and label not in ll:
                break
            values.extend(parse_numbers_with_units(l))
    return values

sell_stocks = extract_stocks_in_window('sell', ('regular','net'))
print('Sell stocks:', sell_stocks)

print('\nLines between Sell and Regular/Net:')
lowered = [l.lower().strip() for l in lines]
start_idx = None
end_idx = None
for i, ll in enumerate(lowered):
    if 'sell' in ll:
        start_idx = i + 1
        break
if start_idx is not None:
    for j in range(start_idx, len(lowered)):
        ll = lowered[j]
        if 'regular' in ll or 'net' in ll:
            end_idx = j
            break
    if end_idx is None:
        end_idx = len(lines)
    for l in lines[start_idx:end_idx]:
        print(l)

s_val = [v for v in extract_metric_numbers('s.val') if v >= 100_000]
s_lot = extract_metric_numbers('s.lot')
s_avg = extract_metric_numbers('s.avg')
print('s_val count', len(s_val), s_val[:10])
print('s_lot count', len(s_lot), s_lot[:10])
print('s_avg count', len(s_avg), s_avg[:10])
