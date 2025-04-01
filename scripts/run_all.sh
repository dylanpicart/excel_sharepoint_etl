#!/bin/bash

# --------------------------
# CONFIGURATION
# --------------------------

# Activate the Python virtual environment
source venv/bin/activate
set -e

# Load environment variables from .env
if [ -f ".env" ]; then
    set -o allexport
    source .env
    set +o allexport
fi

mkdir -p logs
rm -f logs/*.log

# Ensure config.json exists
if [ ! -f "config.json" ]; then
    echo "❌ config.json not found. Please create it with your confidential configuration."
    exit 1
fi

# Retrieve sheet names from config.json using jq (requires jq to be installed)
readarray -t SHEETS < <(jq -r '.SHEET_CONFIGS | keys[]' config.json)

# --------------------------
# LOOP THROUGH EACH SHEET
# --------------------------
for SHEET_NAME in "${SHEETS[@]}"
do
    echo ""
    echo "🔄 Processing sheet: $SHEET_NAME"
    echo "📢 SHEET: $SHEET_NAME"

    # Sanitize sheet name for log filenames
    LOG_NAME=$(echo "$SHEET_NAME" | sed 's/[^a-zA-Z0-9._-]/_/g')

    # Get the local PDF output directory from config.json
    PDF_OUTPUT_DIR=$(jq -r --arg sheet "$SHEET_NAME" '.SHEET_CONFIGS[$sheet].local_pdf_dir' config.json)

    if [ -z "$PDF_OUTPUT_DIR" ]; then
        echo "❌ No PDF output directory defined for '$SHEET_NAME'. Skipping."
        continue
    fi

    # Extract CSV file from the Excel sheet
    EXTRACT_OUTPUT=$(python3 python/extract_checked.py "$SHEET_NAME" 2> "logs/${LOG_NAME}.log")
    CSV_FILE=$(echo "$EXTRACT_OUTPUT" | sed -n '1p')

    echo "📄 CSV File: $CSV_FILE"
    echo "📂 Output Folder: $PDF_OUTPUT_DIR"

    if [ ! -d "$PDF_OUTPUT_DIR" ]; then
        echo "❌ Skipping '$SHEET_NAME': output directory does not exist."
        continue
    fi

    sleep 1

    # Download PDFs using the cluster version of the script
    echo "🟡 Downloading PDFs for '$SHEET_NAME'..."
    node js/download_pdfs_cluster.js "$PDF_OUTPUT_DIR" "$CSV_FILE"
    if [ $? -ne 0 ]; then
        echo "❌ Download failed for '$SHEET_NAME'"
        continue
    fi

    sleep 1

    # Add hyperlinks to the Excel file for the current sheet
    echo "🟡 Adding hyperlinks to Excel for '$SHEET_NAME'..."
    python3 python/add_hyperlinks.py "$PDF_OUTPUT_DIR"
    if [ $? -ne 0 ]; then
        echo "❌ Hyperlink update failed for '$SHEET_NAME'"
        continue
    fi

    echo "✅ Finished sheet: $SHEET_NAME"
done

# --------------------------
# GENERATE HYPERLINK SHEETS FOR ALL DIRECTORIES
# --------------------------
echo ""
echo "🔗 Generating hyperlink sheets for all directories..."

python3 python/add_hyperlinks.py
if [ $? -ne 0 ]; then
    echo "❌ Failed to generate hyperlink sheets"
else
    echo "✅ Hyperlink sheets added to: $EXCEL_PATH"
    echo "🧠 You can now copy/paste each hyperlink column into its corresponding 'PDF Name' column."
fi

# --------------------------
# DONE
# --------------------------
echo ""
echo "🎉 All sheets processed!"
echo "📄 Excel updated: $EXCEL_PATH"
echo "🛑 Check 'data/failed_downloads.csv' for any errors."
echo "📜 Check 'logs/' for detailed logs."
