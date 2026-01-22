#!/bin/bash
# Quick script to scrape today's data and validate recommendations

echo "🚀 IDX Real-Time Validation Pipeline"
echo "======================================"
echo ""

# Step 1: Scrape today's data
echo "📊 Step 1: Scraping today's data from IDX..."
echo ""
python scripts/scrapers/20260116_ringkasan_saham_batch_scraper.py

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  Scraping failed. Possible reasons:"
    echo "   - Market not yet open (< 09:00 WIB)"
    echo "   - Internet connection issue"
    echo "   - Chrome/chromedriver not installed"
    echo ""
    echo "💡 Manual scraping option:"
    echo "   1. Visit: https://www.idx.co.id/id/data-pasar/ringkasan-perdagangan/ringkasan-saham/"
    echo "   2. Download today's CSV"
    echo "   3. Place in: data/IHSGstockdata/ringkasan_saham/"
    echo ""
    exit 1
fi

# Step 2: Combine with existing data
echo ""
echo "🔄 Step 2: Combining with historical data..."
python 20260120_combine_ringkasan_data.py

# Step 3: Validate
echo ""
echo "✅ Step 3: Validating recommendations..."
python 20260122_validate_today_opening.py

echo ""
echo "======================================"
echo "✨ Validation complete!"
