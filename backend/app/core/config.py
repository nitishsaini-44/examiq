"""
ExamIQ Configuration Module
Loads environment variables and provides app-wide settings.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads")))
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Tesseract OCR path (Windows)
TESSERACT_CMD = os.getenv(
    "TESSERACT_CMD",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

# HF Space Topic Analyzer
HF_SPACE_URL = os.getenv(
    "HF_SPACE_URL",
    "https://nitishsaini44-exam-topic-analyzer.hf.space"
)

# CORS
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

# Upload settings
MAX_UPLOAD_SIZE_MB = 50

