import os
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

# PDF Libraries
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import pymupdf as fitz  # PyMuPDF
except (ImportError, Exception):
    # Catch both missing module and DLL load failures
    fitz = None

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

# OCR Libraries
try:
    import pytesseract
    from PIL import Image
    from pdf2image import convert_from_path
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# Word Libraries
try:
    import docx
except ImportError:
    docx = None

from ...utils.document_preprocessor import preprocess_document

logger = logging.getLogger(__name__)

class DocumentExtractor:
    """
    Centralized service for extracting text from various document types.
    Supports PDF, DOCX, TXT, and Images (OCR).
    """

    def __init__(self, ocr_threshold: int = 100):
        self.ocr_threshold = ocr_threshold

    def extract_text(self, file_path: str, extension: Optional[str] = None) -> str:
        """
        Main entry point for text extraction.
        Selects the best engine based on file extension.
        """
        if not os.path.exists(file_path):
            logger.error(f"[EXTRACTOR] File not found: {file_path}")
            return ""

        if not extension:
            extension = Path(file_path).suffix.lower().replace('.', '')
        else:
            extension = extension.lower().replace('.', '')

        logger.info(f"[EXTRACTOR] Extracting text from {file_path} (Type: {extension})")

        text = ""
        if extension == "pdf":
            text = self._extract_from_pdf(file_path)
            # Check if OCR is needed (scanned documents)
            if len(text.strip()) < self.ocr_threshold and OCR_AVAILABLE:
                logger.info(f"[EXTRACTOR] Text too short ({len(text)}), attempting OCR fallback.")
                ocr_text = self._extract_via_ocr(file_path, is_pdf=True)
                if len(ocr_text) > len(text):
                    text = ocr_text
        elif extension in ["png", "jpg", "jpeg", "tiff", "bmp"]:
            if OCR_AVAILABLE:
                text = self._extract_via_ocr(file_path, is_pdf=False)
            else:
                logger.warning("[EXTRACTOR] OCR requested for image but libraries not available.")
        elif extension in ["docx", "doc"]:
            text = self._extract_from_docx(file_path)
        elif extension == "txt":
            text = self._extract_from_txt(file_path)
        else:
            logger.warning(f"[EXTRACTOR] Unsupported extension: {extension}")

        return text.strip()

    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF using multiple fallback engines."""
        text = ""
        
        # 1. Try pdfplumber (best for layout)
        if pdfplumber:
            try:
                with pdfplumber.open(file_path) as pdf:
                    parts = []
                    for page in pdf.pages:
                        t = page.extract_text()
                        if t:
                            parts.append(t)
                    text = "\n".join(parts)
                    if text.strip():
                        logger.info("[EXTRACTOR] Extracted text using pdfplumber")
                        return text
            except Exception as e:
                logger.warning(f"[EXTRACTOR] pdfplumber failed: {e}")

        # 2. Try PyMuPDF (fitz) - very fast and robust
        if fitz:
            try:
                doc = fitz.open(file_path)
                parts = []
                for page in doc:
                    parts.append(page.get_text())
                doc.close()
                text = "\n".join(parts)
                if text.strip():
                    logger.info("[EXTRACTOR] Extracted text using PyMuPDF")
                    return text
            except Exception as e:
                logger.warning(f"[EXTRACTOR] PyMuPDF failed: {e}")

        # 3. Try PyPDF2 (last resort for standard text)
        if PyPDF2:
            try:
                with open(file_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    parts = []
                    for page in reader.pages:
                        t = page.extract_text()
                        if t:
                            parts.append(t)
                    text = "\n".join(parts)
                    if text.strip():
                        logger.info("[EXTRACTOR] Extracted text using PyPDF2")
                        return text
            except Exception as e:
                logger.warning(f"[EXTRACTOR] PyPDF2 failed: {e}")

        return text

    def _extract_via_ocr(self, file_path: str, is_pdf: bool = False) -> str:
        """Extract text using Tesseract OCR."""
        if not OCR_AVAILABLE:
            return ""

        try:
            if is_pdf:
                # Convert PDF pages to images
                # Note: This can be slow for large documents
                # We limit to first 20 pages for safety in this centralized utility
                logger.info(f"[EXTRACTOR] Converting PDF to images for OCR: {file_path}")
                images = convert_from_path(file_path, first_page=1, last_page=20)
                text_parts = []
                for i, image in enumerate(images):
                    logger.debug(f"[EXTRACTOR] OCRing page {i+1}...")
                    page_text = pytesseract.image_to_string(image)
                    if page_text.strip():
                        text_parts.append(page_text)
                return "\n\n".join(text_parts)
            else:
                # Direct image OCR
                text = pytesseract.image_to_string(Image.open(file_path))
                return text
        except Exception as e:
            logger.error(f"[EXTRACTOR] OCR failed: {e}")
            return ""

    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX."""
        if docx:
            try:
                d = docx.Document(file_path)
                return "\n".join([p.text for p in d.paragraphs if p.text.strip()])
            except Exception as e:
                logger.error(f"[EXTRACTOR] DOCX extraction failed: {e}")
        return ""

    def _extract_from_txt(self, file_path: str) -> str:
        """Extract text from plain text file."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            logger.error(f"[EXTRACTOR] TXT extraction failed: {e}")
            return ""

    def extract_and_preprocess(self, file_path: str, max_length: int = 12000) -> str:
        """
        Helper that extracts text and applies the GRC cleaning pipeline.
        """
        raw_text = self.extract_text(file_path)
        if not raw_text:
            return ""
        
        processed_text, _ = preprocess_document(raw_text, max_length=max_length)
        return processed_text
