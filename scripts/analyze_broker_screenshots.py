"""
Analyze foreign broker activity screenshots from Jan 30, 2026
Extract stock codes, volumes, and prices to identify most bought stocks
"""

import os
import re
from pathlib import Path
from PIL import Image
import pytesseract
import pandas as pd
from collections import defaultdict

def extract_text_from_image(image_path):
    """Extract text from screenshot using OCR"""
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return ""

def parse_broker_data(text):
    """
    Parse broker activity data from OCR text
    Looking for patterns like:
    - Stock codes (4 letters)
    - Buy/Sell volumes
    - Prices
    """
    data = []
    
    # Split into lines
    lines = text.split('\n')
    
    for line in lines:
        # Skip empty lines
        if not line.strip():
            continue
            
        # Look for stock code pattern (4 capital letters)
        stock_match = re.search(r'\b([A-Z]{4})\b', line)
        
        # Look for numbers that could be volumes or prices
        numbers = re.findall(r'[\d,]+\.?\d*', line)
        
        if stock_match and numbers:
            stock_code = stock_match.group(1)
            # Try to extract volume and price
            # This will need refinement based on actual screenshot format
            data.append({
                'stock': stock_code,
                'line': line,
                'numbers': numbers
            })
    
    return data

def analyze_brokers_folder(folder_path):
    """Analyze all screenshots in the brokers folder"""
    
    print("=" * 80)
    print("FOREIGN BROKER ACTIVITY ANALYSIS - JAN 30, 2026")
    print("=" * 80)
    print()
    
    folder = Path(folder_path)
    screenshots = sorted(folder.glob("*.png"))
    
    print(f"Found {len(screenshots)} screenshots to analyze")
    print()
    
    all_data = []
    stock_buy_volumes = defaultdict(list)
    stock_prices = defaultdict(list)
    
    for i, screenshot in enumerate(screenshots, 1):
        print(f"Processing {i}/{len(screenshots)}: {screenshot.name}")
        
        text = extract_text_from_image(screenshot)
        
        # Save extracted text for debugging
        text_file = screenshot.with_suffix('.txt')
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(text)
        
        # Parse the extracted text
        parsed_data = parse_broker_data(text)
        all_data.extend(parsed_data)
        
        # Look for foreign buy indicators
        if 'foreign' in text.lower() or 'asing' in text.lower():
            print(f"  ✓ Contains foreign broker data")
        
        print(f"  Found {len(parsed_data)} potential stock entries")
        print()
    
    # Create DataFrame for analysis
    if all_data:
        df = pd.DataFrame(all_data)
        
        print("\n" + "=" * 80)
        print("SUMMARY OF DETECTED STOCKS")
        print("=" * 80)
        
        stock_counts = df['stock'].value_counts()
        print(f"\nTop 20 most mentioned stocks:")
        print(stock_counts.head(20))
        
        # Save results
        output_path = Path(folder_path).parent / 'results' / '20260130_broker_ocr_analysis.csv'
        output_path.parent.mkdir(exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"\nDetailed results saved to: {output_path}")
        
        # Save summary
        summary_path = Path(folder_path).parent / 'results' / '20260130_broker_summary.txt'
        with open(summary_path, 'w') as f:
            f.write("FOREIGN BROKER ACTIVITY - JAN 30, 2026\n")
            f.write("=" * 80 + "\n\n")
            f.write("TOP MENTIONED STOCKS:\n\n")
            f.write(stock_counts.head(20).to_string())
            f.write("\n\nNote: This is OCR-extracted data. Manual verification recommended.\n")
        
        print(f"Summary saved to: {summary_path}")
        
    else:
        print("\nNo stock data could be extracted. OCR may need adjustment.")
        print("Please check the generated .txt files next to each screenshot.")
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Review the .txt files generated for each screenshot")
    print("2. Check the CSV output for detected patterns")
    print("3. Manually verify the most bought stocks and prices")

if __name__ == "__main__":
    brokers_folder = "/Users/arifpras/Library/CloudStorage/Dropbox/perisai/stockscraper/brokers"
    analyze_brokers_folder(brokers_folder)
