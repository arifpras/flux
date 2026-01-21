"""
Collect daily ringkasan saham data for last N Indonesian business days.
Handles weekends and Indonesian public holidays.
"""
import os
from datetime import datetime, timedelta
from typing import List
import pandas as pd

# Indonesian public holidays 2025-2026
INDONESIAN_HOLIDAYS = [
    datetime(2025, 1, 1),   # New Year
    datetime(2025, 2, 19),  # Isra & Mi'raj
    datetime(2025, 3, 29),  # Nyepi
    datetime(2025, 4, 18),  # Good Friday
    datetime(2025, 5, 1),   # Labour Day
    datetime(2025, 5, 23),  # Vesak Day
    datetime(2025, 6, 1),   # Eid al-Fitr (estimated)
    datetime(2025, 6, 2),   # Eid al-Fitr (estimated)
    datetime(2025, 6, 16),  # Eid al-Adha (estimated)
    datetime(2025, 7, 7),   # Islamic New Year
    datetime(2025, 8, 17),  # Independence Day
    datetime(2025, 8, 28),  # Mawlid
    datetime(2025, 9, 8),   # Ascension of Jesus
    datetime(2025, 12, 25), # Christmas
    datetime(2025, 12, 26), # Joint Leave
    datetime(2026, 1, 1),   # New Year
    datetime(2026, 2, 8),   # Isra & Mi'raj
    datetime(2026, 3, 20),  # Nyepi
]


def is_business_day(date: datetime) -> bool:
    """Check if date is an Indonesian business day (not weekend or holiday)."""
    # Exclude weekends (Saturday=5, Sunday=6)
    if date.weekday() >= 5:
        return False
    # Exclude public holidays
    if date.replace(hour=0, minute=0, second=0, microsecond=0) in INDONESIAN_HOLIDAYS:
        return False
    return True


def get_business_days(end_date: datetime = None, num_days: int = 90) -> List[datetime]:
    """Get last N Indonesian business days (backwards from end_date)."""
    if end_date is None:
        end_date = datetime.now()

    business_days = []
    current = end_date

    while len(business_days) < num_days:
        if is_business_day(current):
            business_days.append(current)
        current -= timedelta(days=1)

    return sorted(business_days)  # Return in chronological order


def format_date(date: datetime, fmt: str = "%Y%m%d") -> str:
    """Format date for filename."""
    return date.strftime(fmt)


def main():
    """Generate list of last 90 business days."""
    dates = get_business_days(num_days=90)

    print("=" * 80)
    print("📅 Last 90 Indonesian Business Days")
    print("=" * 80)
    print(f"\nFrom: {dates[0].strftime('%Y-%m-%d')} ({dates[0].strftime('%A')})")
    print(f"To  : {dates[-1].strftime('%Y-%m-%d')} ({dates[-1].strftime('%A')})")
    print(f"\nTotal business days: {len(dates)}\n")

    # Show first 10 and last 10
    print("First 10 days:")
    for d in dates[:10]:
        print(f"  {d.strftime('%Y-%m-%d %A')}")

    print("\n...")
    print("\nLast 10 days:")
    for d in dates[-10:]:
        print(f"  {d.strftime('%Y-%m-%d %A')}")

    print("\n" + "=" * 80)

    return dates


if __name__ == "__main__":
    dates = main()

    # Save to file for scraper to use
    output_file = "business_days_90.txt"
    with open(output_file, "w") as f:
        for d in dates:
            f.write(f"{d.strftime('%Y%m%d')}\n")
    print(f"\n✅ Saved to: {output_file}")
