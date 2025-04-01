import os
from dotenv import load_dotenv
from pathlib import Path

# Load the .env file from the project root
dotenv_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path)

# Centralized config values
EXCEL_PATH = os.getenv("EXCEL_PATH")
CSV_DIR = os.getenv("CSV_DIR", "data/csv")
PDF_ROOT_DIR = os.getenv("PDF_ROOT_DIR", "data/pdfs")
COOKIES_FILE = os.getenv("COOKIES_FILE", "cookies.json")