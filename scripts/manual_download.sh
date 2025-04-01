#!/bin/bash

OUTPUT_DIR="./manual_test"
CSV_FILE="test_single_row.csv"

mkdir -p "$OUTPUT_DIR"

echo "🔧 Downloading one row from: $CSV_FILE"
node download_pdfs_cluster.js "$OUTPUT_DIR" "$CSV_FILE"

# Exit if the download failed
if ! node download_pdfs_cluster.js "$OUTPUT_DIR" "$CSV_FILE"; then
    echo "❌ Download failed for '$CSV_FILE'"
    exit 1
fi

echo "Manual download complete."