import pandas as pd
import os
import sys
import re
import time
import json
from pathlib import Path
from dotenv import load_dotenv

# ─── Bootstrap env & config ───────────────────────────────────────────────────
# Load .env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

# Load confidential sheet configuration
cfg_path = Path(__file__).resolve().parent.parent / "config.json"
config   = json.loads(cfg_path.read_text())
sheet_configs = config["SHEET_CONFIGS"]

# Parse CLI args
# Usage: python extract_checked.py "<Sheet Key>" [--debug]
raw = sys.argv[1:]
debug = "--debug" in raw
args  = [a for a in raw if a != "--debug"]

if not args:
    print("❌ You must supply one sheet key from config.json:", file=sys.stderr)
    print("   Available keys:", ", ".join(sheet_configs.keys()), file=sys.stderr)
    sys.exit(1)

sheet_name = args[0]
if sheet_name not in sheet_configs:
    print(f"❌ Sheet '{sheet_name}' not found in config.json keys.", file=sys.stderr)
    print("   Available keys:", ", ".join(sheet_configs.keys()), file=sys.stderr)
    sys.exit(1)

print(f"🔍 DEBUG: Using sheet_name = {sheet_name}", file=sys.stderr)
if debug:
    print("🔍 DEBUG: Running in debug mode", file=sys.stderr)

# Paths & timing
start        = time.time()
excel_path   = Path(os.getenv("EXCEL_PATH"))
csv_dir      = Path(os.getenv("CSV_DIR", "data/csv"))
pdf_root_dir = Path(os.getenv("PDF_ROOT_DIR", "data/pdfs"))
safe_name    = re.sub(r'[\\/*?:"<>|]', "_", sheet_name)
output_csv   = csv_dir / f"to_download_{safe_name}.csv"

# ─── Load Excel & filter ───────────────────────────────────────────────────────
required_cols = ["Status", "Hyperlink", "PDF Name"]
xls           = pd.ExcelFile(excel_path)
matched       = next((s for s in xls.sheet_names if s.strip()==sheet_name.strip()), None)
if not matched:
    raise ValueError(f"❌ Sheet '{sheet_name}' not found in workbook")

df = pd.read_excel(excel_path, sheet_name=matched, engine="openpyxl")
df.columns = df.columns.str.strip()

missing = [c for c in required_cols if c not in df.columns]
if missing:
    raise ValueError(f"❌ Missing columns in '{sheet_name}': {missing}")

# Diagnostics
print("🔍 Status values:", df["Status"].unique(), file=sys.stderr)
print("🔍 Sample Hyperlinks:", df["Hyperlink"].dropna().head().tolist(), file=sys.stderr)
print("🔍 Sample PDF Names:", df["PDF Name"].dropna().head().tolist(), file=sys.stderr)

# Optional per-row debug
if debug:
    print(f"── Detailed debug for {sheet_name} ──", file=sys.stderr)
    for idx, row in df.iterrows():
        status = row["Status"]
        link   = str(row["Hyperlink"]).strip()
        name   = str(row["PDF Name"]).strip()
        passes = status is True and link.startswith("http") and bool(name)
        print(
            f"Row {idx+2:3}: Status={status!r}, Link={link[:30]!r:30}, "
            f"Name={name!r:30}, passes_filter={passes}",
            file=sys.stderr
        )

# Apply filters
df["Hyperlink"] = df["Hyperlink"].astype(str).str.strip()
df["PDF Name"]  = df["PDF Name"].astype(str).str.strip()

checked = df[
    df["Status"].eq(True) &
    df["Hyperlink"].str.startswith("http") &
    df["PDF Name"].ne("")
].copy()

# Normalize
checked.loc[:, "PDF Name"]  = checked["PDF Name"].str.replace(r'[\\/*?:"<>|]', "_", regex=True)
checked.loc[:, "Hyperlink"] = checked["Hyperlink"].str.replace("/edit/", "/print/")

# Save CSV
csv_dir.mkdir(exist_ok=True, parents=True)
checked[["Hyperlink","PDF Name"]].to_csv(output_csv, index=False)

# Prepare PDF output folder
folder_name = sheet_name.replace(" - Rows","").strip()
output_path = pdf_root_dir / folder_name
output_path.mkdir(exist_ok=True, parents=True)

# Final logs
print(f"✅ Extracted {len(checked)} rows from sheet: {sheet_name}", file=sys.stderr)
print(f"⏱️  Completed in {round(time.time()-start,2)}s", file=sys.stderr)

# For use by run_all.sh
print(output_csv)
print(output_path)
