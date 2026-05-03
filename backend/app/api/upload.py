"""
ExamIQ Upload API
File upload endpoints for papers and syllabus.
"""
import os
import json
import uuid
import logging
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.core.config import UPLOAD_DIR, DATA_DIR
from app.core.ocr import process_file, extract_year_from_filename
from app.models.schemas import UploadResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/upload", tags=["upload"])

# In-memory storage for current session
uploaded_data = {
    "papers": [],  # [{filename, year, text}]
    "syllabus_text": "",
    "syllabus_file": "",
}


@router.post("/papers", response_model=UploadResponse)
async def upload_papers(files: list[UploadFile] = File(...)):
    """Upload past exam papers (PDF/images). Extracts text via OCR."""
    papers_dir = UPLOAD_DIR / "papers"
    papers_dir.mkdir(parents=True, exist_ok=True)

    processed = 0
    total_text = 0
    years = []

    for file in files:
        try:
            ext = Path(file.filename).suffix.lower()
            if ext not in [".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".tiff"]:
                logger.warning(f"Skipping unsupported file: {file.filename}")
                continue

            file_id = str(uuid.uuid4())[:8]
            save_path = papers_dir / f"{file_id}_{file.filename}"

            content = await file.read()
            with open(save_path, "wb") as f:
                f.write(content)

            text = ""
            try:
                text = process_file(str(save_path))
            except Exception as ocr_err:
                logger.error(f"OCR processing failed for {file.filename}: {ocr_err}")

            year = extract_year_from_filename(file.filename)

            if not text:
                logger.warning(
                    f"No text extracted from {file.filename}. "
                    "Check if Tesseract OCR is installed (needed for scanned PDFs)."
                )

            # Always record the paper — even with empty text — so the
            # JSON reflects every uploaded file.
            uploaded_data["papers"].append({
                "filename": file.filename,
                "year": year or 0,
                "text": text,
                "path": str(save_path),
            })
            processed += 1
            total_text += len(text)
            if year:
                years.append(year)

            logger.info(f"Processed: {file.filename} (year={year}, chars={len(text)})")

        except Exception as e:
            logger.error(f"Failed to process {file.filename}: {e}")

    # Save to disk
    data_file = DATA_DIR / "uploaded_papers.json"
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(uploaded_data["papers"], f, indent=2, ensure_ascii=False)

    return UploadResponse(
        message=f"Successfully processed {processed}/{len(files)} files",
        files_processed=processed,
        total_text_length=total_text,
        years_detected=sorted(set(years))
    )


@router.post("/syllabus", response_model=UploadResponse)
async def upload_syllabus(file: UploadFile = File(...)):
    """Upload syllabus file (PDF/image/text)."""
    syllabus_dir = UPLOAD_DIR / "syllabus"
    syllabus_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix.lower()
    save_path = syllabus_dir / f"syllabus{ext}"

    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    if ext == ".txt":
        text = content.decode("utf-8", errors="ignore")
    else:
        text = process_file(str(save_path))

    uploaded_data["syllabus_text"] = text
    uploaded_data["syllabus_file"] = str(save_path)

    data_file = DATA_DIR / "syllabus.json"
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump({"text": text, "file": str(save_path)}, f, indent=2, ensure_ascii=False)

    return UploadResponse(
        message="Syllabus uploaded and processed",
        files_processed=1,
        total_text_length=len(text)
    )


@router.get("/status")
async def upload_status():
    """Get current upload status."""
    return {
        "papers_count": len(uploaded_data["papers"]),
        "has_syllabus": bool(uploaded_data["syllabus_text"]),
        "years": sorted(set(p["year"] for p in uploaded_data["papers"] if p["year"])),
        "total_text_chars": sum(len(p["text"]) for p in uploaded_data["papers"]),
    }


def get_uploaded_data():
    """Get uploaded data for analysis. Tries memory first, then disk."""
    if uploaded_data["papers"]:
        return uploaded_data

    # Try loading from disk
    papers_file = DATA_DIR / "uploaded_papers.json"
    syllabus_file = DATA_DIR / "syllabus.json"

    if papers_file.exists():
        with open(papers_file, "r", encoding="utf-8") as f:
            uploaded_data["papers"] = json.load(f)

    if syllabus_file.exists():
        with open(syllabus_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            uploaded_data["syllabus_text"] = data.get("text", "")

    return uploaded_data
