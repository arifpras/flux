#!/bin/bash
# 
# Daily Economist Brief Generator
# Runs every trading day at 8:00 AM WIB
#

# Set paths
PROJECT_DIR="/Users/arifpras/Library/CloudStorage/Dropbox/perisai/stockscraper"
PYTHON_BIN="$PROJECT_DIR/.venv/bin/python3"
SCRIPT="$PROJECT_DIR/scripts/analysis/generate_economist_brief.py"
LOG_DIR="$PROJECT_DIR/REPORTS/logs"
LOG_FILE="$LOG_DIR/economist_brief_$(date +\%Y\%m\%d).log"

# Create log directory if needed
mkdir -p "$LOG_DIR"

# Log start
echo "========================================" >> "$LOG_FILE"
echo "Economist Brief Generation Started" >> "$LOG_FILE"
echo "Date: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# Run the generator
"$PYTHON_BIN" "$SCRIPT" >> "$LOG_FILE" 2>&1

# Check exit status
if [ $? -eq 0 ]; then
    echo "✓ Success" >> "$LOG_FILE"
else
    echo "✗ Failed with exit code $?" >> "$LOG_FILE"
fi

# Log end
echo "Completed: $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
