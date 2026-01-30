"""
PDF Handler - Extract text from PDF files using PyMuPDF
"""

import asyncio
from pathlib import Path
from typing import Optional
import logging

try:
    import pymupdf  # PyMuPDF
except ImportError:
    import fitz as pymupdf  # Fallback import name

from .base import BaseHandler

logger = logging.getLogger(__name__)


class PDFHandler(BaseHandler):
    """
    Extract text from PDF files using PyMuPDF (fast and reliable).

    Handles:
    - Text-based PDFs
    - Multi-page documents
    - Various encodings
    - Corrupted/partial PDFs (graceful degradation)
    """

    @classmethod
    def supported_extensions(cls) -> set[str]:
        return {'.pdf'}

    async def extract(self, path: Path) -> Optional[str]:
        """Extract text from PDF file"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self._extract_sync, path
        )

    def _extract_sync(self, path: Path) -> Optional[str]:
        """Synchronous extraction (runs in thread pool)"""
        try:
            # Open PDF
            doc = pymupdf.open(str(path))

            if doc.page_count == 0:
                logger.warning(f"PDF has no pages: {path}")
                doc.close()
                return None

            text_parts = []

            # Extract text from each page
            for page_num in range(doc.page_count):
                try:
                    page = doc[page_num]
                    text = page.get_text()

                    if text and text.strip():
                        # Add page marker for context
                        text_parts.append(f"--- Page {page_num + 1} ---\n{text.strip()}")

                except Exception as e:
                    logger.warning(f"Failed to extract page {page_num + 1} from {path}: {e}")
                    continue

            doc.close()

            # Combine all pages
            full_text = "\n\n".join(text_parts)

            if not full_text.strip():
                logger.info(f"No text content in PDF: {path}")
                return None

            return full_text

        except Exception as e:
            logger.error(f"PDF extraction failed for {path}: {e}")
            return None


class PDFWithOCRHandler(PDFHandler):
    """
    Extended PDF handler that performs OCR on image-based PDFs.

    Falls back to OCR if text extraction yields too little content.
    """

    def __init__(self, min_text_threshold: int = 100):
        """
        Args:
            min_text_threshold: Minimum characters to consider text-based
        """
        self.min_text_threshold = min_text_threshold

    def _extract_sync(self, path: Path) -> Optional[str]:
        """Try text extraction first, fall back to OCR if needed"""

        # Try normal text extraction
        text = super()._extract_sync(path)

        # If we got enough text, return it
        if text and len(text) >= self.min_text_threshold:
            return text

        # Fall back to OCR
        logger.info(f"PDF appears to be image-based, attempting OCR: {path}")
        return self._extract_with_ocr(path)

    def _extract_with_ocr(self, path: Path) -> Optional[str]:
        """Extract text using OCR (Tesseract)"""
        try:
            import pytesseract
            from PIL import Image

            doc = pymupdf.open(str(path))
            text_parts = []

            for page_num in range(doc.page_count):
                try:
                    page = doc[page_num]

                    # Render page to image
                    pix = page.get_pixmap(dpi=300)  # High DPI for better OCR

                    # Convert to PIL Image
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                    # Perform OCR (German + English)
                    text = pytesseract.image_to_string(img, lang='deu+eng')

                    if text.strip():
                        text_parts.append(f"--- Page {page_num + 1} ---\n{text.strip()}")

                except Exception as e:
                    logger.warning(f"OCR failed for page {page_num + 1} in {path}: {e}")
                    continue

            doc.close()

            full_text = "\n\n".join(text_parts)
            return full_text if full_text.strip() else None

        except ImportError:
            logger.error("pytesseract not available for OCR")
            return None
        except Exception as e:
            logger.error(f"OCR extraction failed for {path}: {e}")
            return None
