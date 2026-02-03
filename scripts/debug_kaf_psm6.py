from pathlib import Path
from PIL import Image
import pytesseract

img = Path('/Users/arifpras/Library/CloudStorage/Dropbox/perisai/stockscraper/brokers/kaf_sekuritas.png')
text = pytesseract.image_to_string(Image.open(img), config='--psm 6')
lines = [l.strip() for l in text.splitlines() if l.strip()]

for i, l in enumerate(lines):
    print(f"{i:02d}: {l}")

header_idx = None
for i, l in enumerate(lines):
    ll = l.lower()
    if 'buy' in ll and 'b.val' in ll and 'sell' in ll and 's.val' in ll:
        header_idx = i
        break

print('\nHeader idx:', header_idx)
if header_idx is not None:
    print('\nLines after header:')
    for l in lines[header_idx+1:]:
        if 'regular' in l.lower() or 'net' in l.lower():
            print('BREAK ON:', l)
            break
        print(l)
