import pandas as pd
import os
import sys
import re
import time
from pathlib import Path
from dotenv import load_dotenv

# Load .env
dotenv_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path)

# Timing start
start = time.time()

# --- CLI args ---
# Usage: python extract_checked.py "Sheet Name" [--debug]
debug = "--debug" in sys.argv
# strip out --debug so sheet_name logic isn’t confused
args = [a for a in sys.argv[1:] if a != "--debug"]
sheet_name = args[0] if args else "SY1920 Remote Consent - Rows"

print(f"🔍 DEBUG: Using sheet_name = {sheet_name}", file=sys.stderr)
if debug:
    print("🔍 DEBUG: Running in debug mode", file=sys.stderr)

safe_sheet = re.sub(r'[\\/*?:"<>|]', "_", sheet_name)
excel_path = Path(os.getenv("EXCEL_PATH"))
csv_dir     = Path(os.getenv("CSV_DIR", "data/csv"))
pdf_root_dir= Path(os.getenv("PDF_ROOT_DIR", "data/pdfs"))
output_csv  = csv_dir / f"to_download_{safe_sheet}.csv"

# Define required columns
required_cols = ['Status', 'Hyperlink', 'PDF Name']

# Load sheet
xls = pd.ExcelFile(excel_path)
matched = next((s for s in xls.sheet_names if s.strip()==sheet_name.strip()), None)
if not matched:
    raise ValueError(f"❌ Sheet '{sheet_name}' not found")

df = pd.read_excel(excel_path, sheet_name=matched, engine="openpyxl")
df.columns = df.columns.str.strip()

missing = [c for c in required_cols if c not in df.columns]
if missing:
    raise ValueError(f"❌ Missing columns in '{sheet_name}': {missing}")

# Diagnostics before filtering
print("🔍 Status values:", df['Status'].unique(), file=sys.stderr)
print("🔍 Sample Hyperlinks:", df['Hyperlink'].dropna().head().tolist(), file=sys.stderr)
print("🔍 Sample PDF Names:", df['PDF Name'].dropna().head().tolist(), file=sys.stderr)

# Detailed per-row debug for Remote Telemental Health
if debug and sheet_name == "Remote Telemental Health - Rows":
    print("── Detailed debug for Remote Telemental Health ──", file=sys.stderr)
    for idx, row in df.iterrows():
        status = row['Status']
        link   = str(row['Hyperlink']).strip()
        name   = str(row['PDF Name']).strip()
        passes = (
            status is True and
            link.startswith("http") and
            name != ""
        )
        print(
            f"Row {idx+2:3}: Status={status!r}, "
            f"Link={repr(link)[:30]:30}, "
            f"Name={repr(name):30}, "
            f"passes_filter={passes}",
            file=sys.stderr
        )

# Clean up and filter
df['Hyperlink'] = df['Hyperlink'].astype(str).str.strip()
df['PDF Name'] = df['PDF Name'].astype(str).str.strip()

checked_df = df[
    df['Status'].eq(True) &
    df['Hyperlink'].str.startswith("http") &
    df['PDF Name'].notna() &
    (df['PDF Name'] != "")
].copy()

# Normalize filenames and convert URLs
checked_df.loc[:, 'PDF Name'] = (
    checked_df['PDF Name']
      .str.replace(r'[\\/*?:"<>|]', '_', regex=True)
)
checked_df.loc[:, 'Hyperlink'] = (
    checked_df['Hyperlink']
      .str.replace('/edit/', '/print/')
)

# Save result
csv_dir.mkdir(parents=True, exist_ok=True)
checked_df[['Hyperlink', 'PDF Name']].to_csv(output_csv, index=False)

# Create PDF output folder
folder_name = sheet_name.replace(" - Rows", "").strip()
output_path = pdf_root_dir / folder_name
output_path.mkdir(parents=True, exist_ok=True)

# Final logs
print(f"✅ Extracted {len(checked_df)} rows from sheet: {sheet_name}", file=sys.stderr)
print(f"⏱️ Extract completed in {round(time.time() - start, 2)}s", file=sys.stderr)

# Output for run_all.sh
print(str(output_csv))
print(str(output_path))
