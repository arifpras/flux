from pathlib import Path
from glob import glob
import pandas as pd
import re

files = sorted(glob('data/reference/Ringkasan Broker-*.xlsx'))
frames = []
for f in files:
    df = pd.read_excel(f)
    # Normalize column names to snake_case
    df.columns = [re.sub(r'[^0-9a-zA-Z]+', '_', c.strip()).strip('_').lower() for c in df.columns]
    # Parse date: prefer existing 'date' column, otherwise derive from filename
    if 'date' in df.columns:
        parsed = pd.to_datetime(df['date'], errors='coerce')
    else:
        m = re.search(r'(20\d{6})', Path(f).name)
        parsed = pd.to_datetime(m.group(1)) if m else pd.NaT
    df['date'] = parsed
    df['sourcefile'] = Path(f).name
    frames.append(df)

combined = pd.concat(frames, ignore_index=True)
out_path = Path('data/reference/ringkasan_broker_combined_20251201_20260121.csv')
out_path.parent.mkdir(parents=True, exist_ok=True)
combined.to_csv(out_path, index=False)
print(f'files {len(files)}, rows {len(combined)}, wrote {out_path}')
