"""
Image Handler - Extract text from images using OCR (Tesseract)
"""

import asyncio
from pathlib import Path
from typing import Optional, TYPE_CHECKING
import logging

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    # Create a dummy Image for type hints
    class Image:
        class Image:
            pass

from .base import BaseHandler

logger = logging.getLogger(__name__)


class ImageHandler(BaseHandler):
    """
    Extract text from images using Tesseract OCR.

    Supports German and English text recognition.
    Handles common image formats.
    """

    @classmethod
    def supported_extensions(cls) -> set[str]:
        return {'.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.gif'}

    def __init__(self, lang: str = 'deu+eng', dpi: int = 300):
        """
        Args:
            lang: Tesseract language codes (default: German + English)
            dpi: DPI for image processing (higher = better quality, slower)
        """
        self.lang = lang
        self.dpi = dpi

    async def extract(self, path: Path) -> Optional[str]:
        """Extract text from image via OCR"""
        if not TESSERACT_AVAILABLE:
            logger.error("pytesseract/PIL not installed, cannot perform OCR")
            return None

        return await asyncio.get_event_loop().run_in_executor(
            None, self._extract_sync, path
        )

    def _extract_sync(self, path: Path) -> Optional[str]:
        """Synchronous OCR extraction"""
        try:
            # Open image
            image = Image.open(str(path))

            # Preprocessing for better OCR
            image = self._preprocess_image(image)

            # Perform OCR
            text = pytesseract.image_to_string(
                image,
                lang=self.lang,
                config=f'--dpi {self.dpi}'
            )

            # Clean up
            if not text or len(text.strip()) < 5:
                logger.info(f"No text detected in image: {path}")
                return None

            return text.strip()

        except Exception as e:
            logger.error(f"OCR extraction failed for {path}: {e}")
            return None

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR results.

        - Convert to grayscale
        - Enhance contrast
        - Resize if too small
        """
        try:
            from PIL import ImageEnhance

            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Convert to grayscale
            image = image.convert('L')

            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)

            # Upscale small images
            min_dimension = 1000
            if min(image.size) < min_dimension:
                scale = min_dimension / min(image.size)
                new_size = (int(image.width * scale), int(image.height * scale))
                image = image.resize(new_size, Image.Resampling.LANCZOS)

            return image

        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}, using original")
            return image


class ScreenshotHandler(ImageHandler):
    """
    Specialized handler for screenshots (common in support/documentation).

    Uses different OCR parameters optimized for screen content.
    """

    def __init__(self):
        # Screenshots typically have higher resolution and clearer text
        super().__init__(lang='deu+eng', dpi=150)

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Minimal preprocessing for screenshots"""
        # Screenshots usually don't need heavy preprocessing
        if image.mode != 'RGB':
            image = image.convert('RGB')

        return image.convert('L')  # Just convert to grayscale
