# Lightweight ETL Pipeline: PDF, Excel, and SharePoint Integration

This multilanguage project leverages Python, Bash, and JavaScript to build a lightweight Extract, Transform, and Load (ETL) pipeline that automates the process of:

- Extracting data from Excel sheets (with special handling for checked rows)
- Generating hyperlinks for PDF files in the Excel workbook
- Downloading PDF files via browser automation using Puppeteer
- Uploading and linking PDFs stored in SharePoint

The pipeline has been designed for efficient processing of multiple sheets and files while preserving advanced Excel formatting and ensuring secure, authenticated access via SharePoint. This version allows the user to choose between downloading and hyperlinking one sheet at a time, or to loop through the entire Excel file and loop through all the sheets.

---

## Table of Contents

- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)
- [Future Improvements](#future-improvements)
- [License](#license)

---

## Project Structure

```
excel_sharepoint_etl/
├── .env                                  # Environment configuration (e.g., SharePoint URLs, local paths)
├── .gitignore                            # Files and folders to ignore in version control
├── config.json                           # Confidential configuration file (ignored by Git)
├── cookies.json                          # Cookies required for authentication
├── add_trusted_location.reg              # Optional: Windows Registry file to trust the project folder
├── scripts/                              # Bash and orchestration scripts
│   ├── run_all.sh                       # Main pipeline script that executes the entire process
│   ├── check_env.sh                     # (Optional) Script to verify environment setup
│   └── bootstrap.sh                     # Sets up the virtual environment and installs dependencies
├── python/                               # Python scripts for data processing and hyperlink generation
│   ├── add_hyperlinks.py                # Creates hyperlink sheets for individual Excel sheets 
│   ├── load_config.py                   # Alternative or updated version for hyperlink generation across all sheets
│   └── extract_checked.py               # Extracts checked rows from Excel and generates CSV files
├── js/                                   # JavaScript code for browser automation (Puppeteer)
│   └── download_pdfs.js                 # Downloads PDFs from URLs listed in CSV files
├── data/                                 # Data generated and used during the pipeline
│   ├── csv/                             # CSV files (e.g., to_download_*.csv) generated from Excel data
│   ├── pdfs/                            # Downloaded PDF files stored in respective subfolders
│   └── failed_downloads.csv             # Log file for any PDF download errors
├── logs/                                 # Detailed logs of pipeline executions
└── requirements.txt                     # Python dependency list
```

---

## Prerequisites

- **Python 3.8+**: Required for running the Python scripts.
- **Node.js (v12+)**: For running the Puppeteer-based PDF download script.
- **SharePoint Account**: Ensure your account has the necessary permissions to access the configured document libraries and folders.
- **OneDrive/SharePoint Sync Client** (optional): For ensuring local files are synced with SharePoint.
- **Git**: To clone the repository (optional).
- **jq**: A lightweight command-line JSON processor (used by run_all.sh to read config.json).

---

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://your-repo-url.git
   cd download_link_pdf
   ```

2. **Set Up the Python Environment:**

   Run the bootstrap script to set up a virtual environment and install dependencies:
   
   ```bash
   ./scripts/bootstrap.sh
   ```

3. **Install Node Dependencies:**

   Navigate to the `js/` directory and install Puppeteer (if not already installed):

   ```bash
   cd js
   npm install
   cd ..
   ```

---

## Configuration

1. **Environment Variables (.env file):**

   Create a `.env` file in the project root (or update the existing one) with your configuration. Key variables include:

   ```dotenv
   # Excel file to update
   EXCEL_PATH=/path/to/your/excel_file.xlsx

   # Local directories for PDFs (each corresponding to a specific sheet)
   PDF_FOLDER_1=/path/to/local/pdf_folder_1
   PDF_FOLDER_2=/path/to/local/pdf_folder_2
   PDF_FOLDER_3=/path/to/local/pdf_folder_3
   PDF_FOLDER_4=/path/to/local/pdf_folder_4
   PDF_FOLDER_5=/path/to/local/pdf_folder_5

   # SharePoint configuration for PDF access
   SHAREPOINT_BASE_URL=https://sharepointbaseurl.sharepoint.com
   SHAREPOINT_LIBRARY_URL=https://sharepointbaseurl.sharepoint.com/link/to/SharePoint/Library
   SHAREPOINT_PDF_FOLDER=/link/to/SharePoint/PDF/Folder

   # (Optional) Other configurations such as cookies file for Puppeteer
   COOKIES_FILE=cookies.json
   ```

   **Note:**  
   - The `SHAREPOINT_LIBRARY_URL` should be in plain text with spaces URL‑encoded (i.e., `%20` for spaces).  
   - `SHAREPOINT_PDF_FOLDER` is the common relative path where all PDF subfolders reside. The individual subfolder names are defined in the confidential configuration.

2. **Confidential Configuration (config.json):**

   To protect sensitive information, move confidential mappings out of your source code. Create a file named **config.json** in the project root with contents similar to:

   ```json
   {
     "SHEET_CONFIGS": {
       "Sheet 1 - Rows": {
         "local_pdf_dir": "/path/to/local/pdf_folder_1",
         "sp_subfolder": "Sheet 1 Folder"
       },
       "Sheet 2 - Rows": {
         "local_pdf_dir": "/path/to/local/pdf_folder_2",
         "sp_subfolder": "Sheet 2 Folder"
       },
       "Sheet 3 - Rows": {
         "local_pdf_dir": "/path/to/local/pdf_folder_3",
         "sp_subfolder": "Sheet 3 Folder"
       },
       "Sheet 4 - Rows": {
         "local_pdf_dir": "/path/to/local/pdf_folder_4",
         "sp_subfolder": "Sheet 4 Folder"
       },
       "Sheet 5 - Rows": {
         "local_pdf_dir": "/path/to/local/pdf_folder_5",
         "sp_subfolder": "Sheet 5 Folder"
       }
     }
   }
   ```

   **Important:**  
   - Add **config.json** to your `.gitignore` so that confidential data isn’t pushed to GitHub.  
   - Optionally, include a **config.example.json** in the repository for reference with dummy values.

3. **SharePoint Folder Structure:**

   Ensure that the PDFs are organized into subfolders under the common PDF folder specified in `SHAREPOINT_PDF_FOLDER`. Your sheets will map to these subfolders.

4. **Node Dependencies:**

    We now use dotenv in our JS scripts. Make sure your js/package.json has:

    ```json
    "dependencies": {
      "dotenv": "^10.0.0",
      "puppeteer": "...",
      "puppeteer-cluster": "...",
      "csv-parser": "..."
    }
    ```
    And install with:

    ```bash
    cd js
    npm install
    ```

---

## Usage

### Running the Pipeline

The main pipeline is orchestrated by the `run_all.sh` script in the `scripts/` folder. It performs the following steps for each configured sheet:

1. **Extract Data:**  
   Runs the Python script `extract_checked.py` to extract rows with a "checked" status into a CSV file.

2. **Download PDFs:**  
   Uses the Node.js script `download_pdfs.js` to download PDFs from the URLs listed in the CSV file.

3. **Generate Hyperlink Sheets:**  
   Calls the Python script `add_hyperlinks.py` to create new sheets in the Excel workbook that contain hyperlinks pointing to the PDFs stored on SharePoint.

To run the full pipeline:

```bash
./scripts/run_all.sh
```

Download PDFs (clustered)
We’ve refactored download_pdfs_cluster.js (and download_pdfs_cluster_debug.js) so that:

If you call it with two args, it treats them as:

```bash
node js/download_pdfs_cluster.js <OUTPUT_DIR> <CSV_FILE>
```
If you call it with just the CSV path, it defaults `<OUTPUT_DIR>` to the SharePoint folder you set in `PDF_TELE`:

```bash
node js/download_pdfs_cluster.js data/csv/to_download_Sheet_With-Rows.csv
```
You can still pass `--debug` as a third flag to get verbose logs:

```bash
node js/download_pdfs_cluster_debug.js \
  data/csv/to_download_Sheet_With-Rows.csv \
  --debug
```

**Add Hyperlinks (single sheet)**

You can now rebuild just one hyperlink sheet by passing its “– Rows” name:

```bash
python3 python/add_hyperlinks.py "Sheet 1 - Rows"
```
This:

Loads your existing workbook (`EXCEL_PATH`).

Removes & recreates only the matching “-- Hyperlink” sheet.

Injects hyperlinks for every PDF in the corresponding `PDF_TELE` folder.

To regenerate all hyperlink sheets, simply run without arguments:

```bash
python3 python/add_hyperlinks.py
```

### Individual Script Usage

- **Extract Checked Rows:**

  ```bash
  python3 python/extract_checked.py "Sheet Name"
  ```

- **Download PDFs:**

  ```bash
  node js/download_pdfs.js "/path/to/output/folder" "/path/to/csv_file.csv"
  ```

- **Add Hyperlinks to Excel:**

  ```bash
  python3 python/add_hyperlinks.py
  ```

---

### Launching the GUI Application

A Tkinter-based GUI is available for users who prefer a clickable interface. The GUI application is located in the `gui/` folder.

To launch the GUI:

1. Ensure you’ve set up the project as described above.
2. Navigate to the **gui/** directory and run the application:

   ```bash
   cd gui
   python3 app.py
   ```

The GUI provides a button to run the pipeline and a log display area to show the output in real-time.

---

## Security Considerations

- **Access Control:**  
  Ensure that your SharePoint document libraries and folders have restricted access to only your team. Regularly audit permissions.

- **Confidential Data:**  
  Sensitive configuration data (such as sheet mappings) is stored in a separate `config.json` file that is excluded from version control.

- **Environment Variables:**  
  Keep your `.env` file out of version control and consider using a secrets manager if needed.

- **HTTPS:**  
  All communications use HTTPS to protect data in transit.

---

## Troubleshooting

- **Hyperlink Issues in Excel:**  
  If hyperlinks do not open the correct PDF, verify that your SharePoint environment variables (`SHAREPOINT_BASE_URL`, `SHAREPOINT_LIBRARY_URL`, and `SHAREPOINT_PDF_FOLDER`) are set correctly and that the folder structure in SharePoint matches your configuration.

- **Expired Cookies / CSRF Errors:**  
  Ensure your SharePoint session is active or update your cookies file (`COOKIES_FILE`) to include valid session cookies if encountering authentication issues.

- **File Not Found:**  
  If a hyperlink cell does not generate a URL, check that the local PDF exists in the designated folder and that the naming convention in Excel matches the file name exactly.

- **Config Issues:**  
  If the sheet names do not match or the configuration isn’t read properly, verify that your `config.json` is correctly formatted and that you’re using `jq` to parse it.

---

## Future Improvements

- **Enhanced Error Reporting:**  
  Improve logging and error reporting to provide more detailed diagnostics for failed downloads or file access issues.

- **User Interface Enhancements:**  
  Expand the GUI to include additional controls, progress indicators, and error displays for a richer user experience.

- **Automated Sync Checks:**  
  Add a mechanism to verify that PDFs have successfully synced to SharePoint before generating hyperlinks.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Author

Developed by Dylan Picart at Partnership With Children.

For questions or contributions, contact [dpicart@partnershipwithchildren.org](mailto:dpicart@partnershipwithchildren.org).
