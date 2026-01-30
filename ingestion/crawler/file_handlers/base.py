"""
Base Handler - Abstract interface for file content extraction
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class BaseHandler(ABC):
    """
    Abstract base class for file handlers.

    Each handler is responsible for extracting text content from a specific
    file type (PDF, DOCX, XLSX, etc.).
    """

    @abstractmethod
    async def extract(self, path: Path) -> Optional[str]:
        """
        Extract text content from a file.

        Args:
            path: Path to the file to extract

        Returns:
            Extracted text content, or None if extraction fails or file is empty

        Note:
            Implementations should handle errors gracefully and return None
            rather than raising exceptions. Log errors for debugging.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement extract()")

    def can_handle(self, path: Path) -> bool:
        """
        Check if this handler can process the given file.

        Default implementation checks file extension. Override for more
        sophisticated detection.

        Args:
            path: Path to file

        Returns:
            True if this handler can process the file
        """
        return path.suffix.lower() in self.supported_extensions()

    @classmethod
    def supported_extensions(cls) -> set[str]:
        """
        Return set of file extensions this handler supports.

        Returns:
            Set of extensions (e.g., {'.pdf', '.docx'})
        """
        return set()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(extensions={self.supported_extensions()})"
