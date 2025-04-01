#!/bin/bash

echo "🔍 Checking environment..."

# Required files
[[ -f cookies.json ]] || echo "❌ cookies.json not found"
[[ -f extract_checked.py ]] || echo "❌ extract_checked.py missing"
[[ -f download_pdfs_cluster.js ]] || echo "❌ download_pdfs_cluster.js missing"

# Node + Python versions
echo "🧠 Python version: $(python3 --version)"
echo "🧠 Node version: $(node --version)"
echo "🧠 npm version: $(npm --version)"

# Excel file path check
EXCEL_PATH="/path/to/Excel/File.xlsx" # Update this path to your actual Excel file location
[[ -f "$EXCEL_PATH" ]] && echo "✅ Excel file found" || echo "❌ Excel file not found at: $EXCEL_PATH"
