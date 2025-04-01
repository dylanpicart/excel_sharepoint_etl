#!/bin/bash

echo "🧨 Removing generated CSVs and output PDFs..."

rm to_download_*.csv 2>/dev/null
find . -type f -name '*.pdf' -delete

echo "✅ Clean slate."
