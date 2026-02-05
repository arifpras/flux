import re
from pathlib import Path
from typing import List, Tuple, Optional

import pandas as pd
from PIL import Image
import pytesseract

BROKERS_DIR = Path("/Users/arifpras/Library/CloudStorage/Dropbox/perisai/stockscraper/brokers")
OUTPUT_DIR = BROKERS_DIR / "csv"
COMBINED_PATH = Path("/Users/arifpras/Library/CloudStorage/Dropbox/perisai/stockscraper/results/broker_tables_combined.csv")

SECTION_MARKERS = {
    "buy",
    "sell",
    "b.val",
    "b.lot",
    "b.avg",
    "s.val",
    "s.lot",
    "s.avg",
    "allinvestor",
    "regular",
    "net",
}


def extract_text(image_path: Path) -> str:
    img = Image.open(image_path)
    return pytesseract.image_to_string(img, config="--psm 6")


def find_broker_name(lines: List[str], fallback: str) -> str:
    for l in lines[:25]:
        if "Sekuritas" in l or "Securities" in l:
            return l.strip()
    for i, l in enumerate(lines):
        if l.lower().strip() == "broker activity":
            for j in range(i + 1, min(i + 12, len(lines))):
                if lines[j].strip():
                    return lines[j].strip()
    return fallback


def extract_stocks_between(lines: List[str], start_token: str, end_tokens: Tuple[str, ...]) -> List[str]:
    collecting = False
    stocks: List[str] = []
    for l in lines:
        ll = l.lower().strip()
        if ll == start_token:
            collecting = True
            continue
        if collecting:
            if any(ll.startswith(t) or t in ll for t in end_tokens):
                break
            for code in re.findall(r"\b[A-Z]{4}\b", l):
                stocks.append(code)
    return stocks


def extract_stocks_in_window(lines: List[str], start_token: str, end_tokens: Tuple[str, ...]) -> List[str]:
    start_idx = None
    end_idx = None
    lowered = [l.lower().strip() for l in lines]
    def is_end_token(line: str) -> bool:
        for token in end_tokens:
            if token in {"net", "regular"}:
                if re.search(rf"\b{re.escape(token)}\b", line):
                    return True
            else:
                if line.startswith(token) or token in line:
                    return True
        return False
    for i, ll in enumerate(lowered):
        if start_token in ll:
            start_idx = i + 1
            break
    if start_idx is None:
        return []

    for j in range(start_idx, len(lowered)):
        ll = lowered[j]
        if is_end_token(ll):
            end_idx = j
            break
    if end_idx is None:
        end_idx = len(lines)

    stocks: List[str] = []
    for l in lines[start_idx:end_idx]:
        for code in re.findall(r"\b[A-Z]{4}\b", l):
            stocks.append(code)
    return stocks


def parse_numbers_with_units(text: str) -> List[float]:
    results: List[float] = []
    for match in re.finditer(r"(\d[\d,]*\.?\d*)(?:\s*([KMB])\b)?", text, flags=re.IGNORECASE):
        num = match.group(1)
        unit = match.group(2)
        if not num:
            continue
        try:
            val = float(num.replace(",", ""))
        except ValueError:
            continue
        if unit:
            unit = unit.upper()
            if unit == "K":
                val *= 1e3
            elif unit == "M":
                val *= 1e6
            elif unit == "B":
                val *= 1e9
        results.append(val)
    return results


def extract_metric_numbers(lines: List[str], label: str) -> List[float]:
    values: List[float] = []
    collecting = False
    for l in lines:
        ll = l.lower().strip()
        if label in ll:
            collecting = True
            values.extend(parse_numbers_with_units(l))
            continue
        if collecting:
            if any(marker in ll for marker in SECTION_MARKERS) and not ll.startswith(label):
                break
            values.extend(parse_numbers_with_units(l))
    return values


def align_lengths(stocks: List[str], *arrays: List[float]) -> Tuple[List[str], List[List[float]]]:
    if not stocks:
        return stocks, [list(a) for a in arrays]
    min_len = min([len(stocks)] + [len(a) for a in arrays if a is not None])
    stocks = stocks[:min_len]
    aligned = [list(a[:min_len]) for a in arrays]
    return stocks, aligned


def build_table(broker: str, side: str, stocks: List[str], vals: List[float], lots: List[float], avgs: List[float]):
    rows = []
    for i, stock in enumerate(stocks):
        rows.append({
            "broker": broker,
            "side": side,
            "stock": stock,
            "val": vals[i] if i < len(vals) else None,
            "lot": lots[i] if i < len(lots) else None,
            "avg": avgs[i] if i < len(avgs) else None,
        })
    return rows


def parse_structured_table(lines: List[str], broker: str, source_image: str) -> Optional[pd.DataFrame]:
    header_idx = None
    for i, l in enumerate(lines):
        ll = l.lower()
        if "buy" in ll and "b.val" in ll and "sell" in ll and "s.val" in ll:
            header_idx = i
            break
    if header_idx is None:
        return None

    rows = []
    for l in lines[header_idx + 1 :]:
        ll = l.lower()
        if re.search(r"\bregular\b", ll) or re.search(r"\bnet\b", ll):
            break
        codes = re.findall(r"\b[A-Z]{4}(?:-W\d?)?\b", l)
        nums = parse_numbers_with_units(l)
        if len(codes) >= 2 and len(nums) >= 6:
            buy_code = codes[0]
            sell_code = codes[1]
            buy_vals = nums[:3]
            sell_vals = nums[-3:]
            rows.append({
                "broker": broker,
                "side": "Buy",
                "stock": buy_code,
                "val": buy_vals[0],
                "lot": buy_vals[1],
                "avg": buy_vals[2],
                "source_image": source_image,
            })
            rows.append({
                "broker": broker,
                "side": "Sell",
                "stock": sell_code,
                "val": sell_vals[0],
                "lot": sell_vals[1],
                "avg": sell_vals[2],
                "source_image": source_image,
            })
        elif len(codes) == 1 and len(nums) >= 3:
            is_buy = l.strip().startswith(codes[0])
            vals = nums[:3] if is_buy else nums[-3:]
            rows.append({
                "broker": broker,
                "side": "Buy" if is_buy else "Sell",
                "stock": codes[0],
                "val": vals[0],
                "lot": vals[1],
                "avg": vals[2],
                "source_image": source_image,
            })

    if not rows:
        return None
    return pd.DataFrame(rows)


def process_image(image_path: Path) -> Optional[pd.DataFrame]:
    text = extract_text(image_path)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return None

    broker = find_broker_name(lines, image_path.stem)

    structured_df = parse_structured_table(lines, broker, image_path.name)
    if structured_df is not None:
        return structured_df

    buy_stocks = extract_stocks_in_window(lines, "buy", ("sell",))
    sell_stocks = extract_stocks_in_window(lines, "sell", ("regular", "net"))

    b_val = extract_metric_numbers(lines, "b.val")
    b_lot = extract_metric_numbers(lines, "b.lot")
    b_avg = extract_metric_numbers(lines, "b.avg")

    s_val = extract_metric_numbers(lines, "s.val")
    s_lot = extract_metric_numbers(lines, "s.lot")
    s_avg = extract_metric_numbers(lines, "s.avg")

    # Remove tiny OCR artifacts from value columns (values should be in large units)
    b_val = [v for v in b_val if v >= 100_000]
    s_val = [v for v in s_val if v >= 100_000]

    buy_stocks, (b_val, b_lot, b_avg) = align_lengths(buy_stocks, b_val, b_lot, b_avg)
    sell_stocks, (s_val, s_lot, s_avg) = align_lengths(sell_stocks, s_val, s_lot, s_avg)

    rows = []
    rows += build_table(broker, "Buy", buy_stocks, b_val, b_lot, b_avg)
    rows += build_table(broker, "Sell", sell_stocks, s_val, s_lot, s_avg)

    if not rows:
        return None

    df = pd.DataFrame(rows)
    df["source_image"] = image_path.name
    return df


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_frames = []
    images = sorted(BROKERS_DIR.glob("*.png"))

    for image_path in images:
        df = process_image(image_path)
        if df is None or df.empty:
            continue
        out_path = OUTPUT_DIR / f"{image_path.stem}.csv"
        df.to_csv(out_path, index=False)
        all_frames.append(df)

    if not all_frames:
        print("No data extracted from images.")
        return

    combined = pd.concat(all_frames, ignore_index=True)
    COMBINED_PATH.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(COMBINED_PATH, index=False)

    print(f"Saved per-image CSVs to: {OUTPUT_DIR}")
    print(f"Saved combined CSV to: {COMBINED_PATH}")
    print(f"Rows extracted: {len(combined)}")


if __name__ == "__main__":
    main()
