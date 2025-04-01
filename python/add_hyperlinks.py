import os
import json
import urllib.parse
from dotenv import load_dotenv
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.styles import Font

# Load environment variables from .env (plain text values)
dotenv_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path)

# Get Excel file path from environment
excel_path = Path(os.getenv("EXCEL_PATH"))

# Base domain URL for building the final link to SharePoint
sharepoint_base_url = os.getenv("SHAREPOINT_BASE_URL")

# The library URL (plain text)
library_url = os.getenv("SHAREPOINT_LIBRARY_URL")
# The base PDF folder path (plain text, starting with a slash)
pdf_folder_base = os.getenv("SHAREPOINT_PDF_FOLDER")

# Load confidential sheet configuration from config.json
config_file = Path(__file__).resolve().parent.parent / "config.json"
with open(config_file, "r") as f:
    config_data = json.load(f)

sheet_configs = config_data["SHEET_CONFIGS"]

# Load the workbook using openpyxl (preserves formatting)
wb = load_workbook(excel_path)

for sheet_name, config in sheet_configs.items():
    if sheet_name not in wb.sheetnames:
        print(f"⚠️ Sheet not found: {sheet_name}")
        continue

    ws_original = wb[sheet_name]
    # Create a new sheet name by replacing " - Rows" with " - Hyperlink"
    new_sheet_name = sheet_name.replace(" - Rows", " - Hyperlink")
    
    # Remove old hyperlink sheet if it exists
    if new_sheet_name in wb.sheetnames:
        print(f"🔄 Overwriting existing sheet: {new_sheet_name}")
        wb.remove(wb[new_sheet_name])
    
    # Create the new sheet for hyperlinks
    ws_new = wb.create_sheet(title=new_sheet_name)
    
    # Find the "PDF Name" column in the header row of the original sheet
    header_row = next(ws_original.iter_rows(min_row=1, max_row=1, values_only=True))
    try:
        pdf_col_index = header_row.index("PDF Name") + 1  # openpyxl uses 1-based indexing
    except ValueError:
        print(f"⚠️ 'PDF Name' column missing in {sheet_name}")
        continue

    # Write header in the new sheet
    ws_new.cell(row=1, column=1, value="PDF Name")
    
    # Define a hyperlink font style (blue and underlined)
    hyperlink_font = Font(color="0000FF", underline="single")
    
    # Pre-compute constants for this sheet (encoded library URL and parent folder)
    encoded_listurl = urllib.parse.quote(library_url, safe='')
    parent_folder = f"{pdf_folder_base}/{config['sp_subfolder']}"
    encoded_parent = urllib.parse.quote(parent_folder, safe='')

    # Process each data row using enumerate (starting at row 2)
    for row_num, row in enumerate(ws_original.iter_rows(min_row=2, values_only=False), start=2):
        cell = row[pdf_col_index - 1]
        pdf_name = cell.value
        # Guard clause: if pdf_name is not a non-empty string, write it and continue
        if not (isinstance(pdf_name, str) and pdf_name.strip()):
            ws_new.cell(row=row_num, column=1, value=pdf_name)
            continue

        pdf_name = pdf_name.strip()
        local_pdf_path = Path(config["local_pdf_dir"]).resolve() / f"{pdf_name}.pdf"
        new_cell = ws_new.cell(row=row_num, column=1, value=pdf_name)
        if local_pdf_path.exists():
            file_path = f"{pdf_folder_base}/{config['sp_subfolder']}/{pdf_name}.pdf"
            encoded_id = urllib.parse.quote(file_path, safe='')
            url = f"{sharepoint_base_url.rstrip('/')}/shared?listurl={encoded_listurl}&id={encoded_id}&parent={encoded_parent}"
            new_cell.hyperlink = url
            new_cell.font = hyperlink_font

# Save the workbook (this updates the file while leaving the original sheets intact)
wb.save(excel_path)
print(f"✅ Hyperlink sheets created for all configured sheets in: {excel_path}")
