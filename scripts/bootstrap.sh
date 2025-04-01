#!/bin/bash

set -e  # Exit on error

echo "🚀 Bootstrapping project: excel_sharepoint_etl"

# Step 1: Create virtual environment
if [ ! -d "venv" ]; then
  echo "📦 Creating Python virtual environment..."
  python3 -m venv venv
else
  echo "✅ venv already exists."
fi

# Step 2: Activate environment
echo "📂 Activating virtual environment..."
source venv/bin/activate

# Step 3: Install Python dependencies
echo "📦 Installing Python packages from requirements.txt..."
pip install -r requirements.txt

# Step 4: Install Node dependencies (if package.json exists)
if [ -f "package.json" ]; then
  echo "📦 Installing Node packages..."
  npm install
else
  echo "⚠️ No package.json found — skipping Node setup."
fi

# Step 5: Create expected directories
echo "📁 Creating data directories..."
mkdir -p data/csv
mkdir -p data/pdfs
mkdir -p logs

# Step 6: Ensure .env file exists with confidential configuration placeholders
if [ ! -f ".env" ]; then
  echo "📄 Creating placeholder .env file..."
  cat <<EOF > .env
# Path to your Excel file
EXCEL_PATH="/path/to/your/excel_file.xlsx"

# Directory for CSV output
CSV_DIR=data/csv

# Directory for downloaded PDFs
PDF_ROOT_DIR=data/pdfs

# File containing cookies for Puppeteer authentication (if applicable)
COOKIES_FILE=cookies.json

# Local directories for PDFs (each corresponding to a specific sheet)
# Update these with your actual local PDF folder paths
PDF_SY1920="/path/to/local/pdf_folder_1"
PDF_PWC="/path/to/local/pdf_folder_2"
PDF_ROI="/path/to/local/pdf_folder_3"
PDF_SY2122="/path/to/local/pdf_folder_4"
PDF_TELE="/path/to/local/pdf_folder_5"

# SharePoint configuration for PDF access
# Update these with your actual SharePoint settings.
SHAREPOINT_BASE_URL="https://yoursharepointdomain.sharepoint.com"
SHAREPOINT_LIBRARY_URL="https://yoursharepointdomain.sharepoint.com/link/to/SharePoint/Library"
SHAREPOINT_PDF_FOLDER="/link/to/SharePoint/PDF/Folder"
EOF

  echo "⚠️ Please update .env with your actual file paths and SharePoint settings."
else
  echo "✅ .env already exists."
fi

echo "✅ Bootstrap complete!"
