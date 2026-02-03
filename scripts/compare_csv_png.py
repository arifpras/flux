from pathlib import Path
import re
import pandas as pd
from PIL import Image
import pytesseract

brokers_dir = Path('/Users/arifpras/Library/CloudStorage/Dropbox/perisai/stockscraper/brokers')
csv_dir = brokers_dir / 'csv'
report_path = Path('/Users/arifpras/Library/CloudStorage/Dropbox/perisai/stockscraper/results/broker_csv_png_comparison.csv')


def parse_numbers_with_units(text: str):
    results = []
    for match in re.finditer(r"(\d[\d,]*\.?\d*)(?:\s*([KMB])\b)?", text, flags=re.IGNORECASE):
        num = match.group(1)
        unit = match.group(2)
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


def ocr_structured_counts(image_path: Path):
    text = pytesseract.image_to_string(Image.open(image_path), config='--psm 6')
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    header_idx = None
    for i, l in enumerate(lines):
        ll = l.lower()
        if 'buy' in ll and 'b.val' in ll and 'sell' in ll and 's.val' in ll:
            header_idx = i
            break
    if header_idx is None:
        return 0, 0

    buy_count = 0
    sell_count = 0
    for l in lines[header_idx + 1:]:
        ll = l.lower()
        if re.search(r'\bregular\b', ll) or re.search(r'\bnet\b', ll):
            break
        codes = re.findall(r"\b[A-Z]{4}(?:-W\d?)?\b", l)
        nums = parse_numbers_with_units(l)
        if len(codes) >= 2 and len(nums) >= 6:
            buy_count += 1
            sell_count += 1
        elif len(codes) == 1 and len(nums) >= 3:
            if l.strip().startswith(codes[0]):
                buy_count += 1
            else:
                sell_count += 1
    return buy_count, sell_count


def csv_counts(csv_path: Path):
    df = pd.read_csv(csv_path)
    buy = int((df['side'].str.lower() == 'buy').sum())
    sell = int((df['side'].str.lower() == 'sell').sum())
    return buy, sell


rows = []
for image_path in sorted(brokers_dir.glob('*.png')):
    csv_path = csv_dir / f"{image_path.stem}.csv"
    if not csv_path.exists():
        rows.append({
            'image': image_path.name,
            'csv': csv_path.name,
            'csv_buy': 0,
            'csv_sell': 0,
            'ocr_buy': None,
            'ocr_sell': None,
            'status': 'MISSING_CSV'
        })
        continue

    csv_buy, csv_sell = csv_counts(csv_path)
    ocr_buy, ocr_sell = ocr_structured_counts(image_path)
    status = 'OK' if (csv_buy == ocr_buy and csv_sell == ocr_sell) else 'MISMATCH'
    rows.append({
        'image': image_path.name,
        'csv': csv_path.name,
        'csv_buy': csv_buy,
        'csv_sell': csv_sell,
        'ocr_buy': ocr_buy,
        'ocr_sell': ocr_sell,
        'status': status
    })

report = pd.DataFrame(rows)
report.to_csv(report_path, index=False)

print(f"Saved comparison report: {report_path}")
print("\nMismatches:")
print(report[report['status'] != 'OK'].to_string(index=False))
