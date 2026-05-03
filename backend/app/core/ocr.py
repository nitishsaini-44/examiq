"""
ExamIQ OCR Engine
Hybrid PDF/Image text extraction using PyMuPDF + Pytesseract fallback.
"""
import fitz  # PyMuPDF
from pathlib import Path
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> list[dict]:
    """
    Extract text from a PDF file using PyMuPDF.
    Falls back to OCR for scanned pages.
    
    Returns list of {page: int, text: str} dicts.
    """
    doc = fitz.open(file_path)
    pages = []

    for page_num, page in enumerate(doc, 1):
        # Try native text extraction first (works for digital PDFs without Tesseract)
        text = page.get_text("text", sort=True)

        # If very little text, the PDF may be scanned — try OCR fallbacks
        if len(text.strip()) < 50:
            # Attempt 1: PyMuPDF built-in OCR (requires Tesseract)
            try:
                tp = page.get_textpage_ocr(language="eng", dpi=300)
                ocr_text = page.get_text("text", textpage=tp)
                if len(ocr_text.strip()) > len(text.strip()):
                    text = ocr_text
                logger.info(f"Page {page_num}: Used PyMuPDF OCR fallback")
            except Exception as e:
                logger.warning(f"Page {page_num}: PyMuPDF OCR failed - {e}")
                # Attempt 2: pytesseract as last resort
                try:
                    fallback_text = _pytesseract_fallback(page)
                    if len(fallback_text.strip()) > len(text.strip()):
                        text = fallback_text
                except Exception as e2:
                    logger.warning(f"Page {page_num}: All OCR methods failed - {e2}")

        if text.strip():
            pages.append({
                "page": page_num,
                "text": text.strip()
            })

    doc.close()
    return pages


def extract_text_from_image(file_path: str) -> str:
    """Extract text from an image file using pytesseract."""
    try:
        import pytesseract
        from app.core.config import TESSERACT_CMD
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

        img = Image.open(file_path)
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception as e:
        logger.error(f"Image OCR failed: {e}")
        return ""


def _pytesseract_fallback(page) -> str:
    """Use pytesseract on a rendered PDF page."""
    try:
        import pytesseract
        from app.core.config import TESSERACT_CMD
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception as e:
        logger.warning(f"Pytesseract fallback failed: {e}")
        return ""


def process_file(file_path: str) -> str:
    """
    Process any supported file and return extracted text.
    Supports: PDF, PNG, JPG, JPEG
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        pages = extract_text_from_pdf(file_path)
        return "\n\n--- PAGE BREAK ---\n\n".join(
            p["text"] for p in pages
        )
    elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]:
        return extract_text_from_image(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def extract_year_from_filename(filename: str) -> int | None:
    """Try to extract exam year from filename."""
    import re
    # Match patterns like 2023, 2024, etc.
    match = re.search(r'(20\d{2})', filename)
    if match:
        return int(match.group(1))
    return None
