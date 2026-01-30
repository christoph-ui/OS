"""
CSV Handler - Extract data from delimited text files (CSV, TSV)
"""

import asyncio
import csv
from pathlib import Path
from typing import Optional
import logging

import chardet

from .base import BaseHandler

logger = logging.getLogger(__name__)


class CSVHandler(BaseHandler):
    """
    Extract data from CSV and TSV files.

    Handles:
    - Various delimiters (comma, tab, semicolon, pipe)
    - Different encodings (UTF-8, Latin-1, Windows-1252)
    - Headers and data rows
    - Quoted fields
    """

    @classmethod
    def supported_extensions(cls) -> set[str]:
        return {'.csv', '.tsv', '.txt'}

    def __init__(self, max_rows: int = 50000):
        """
        Args:
            max_rows: Maximum rows to process (protection against huge files)
        """
        self.max_rows = max_rows

    async def extract(self, path: Path) -> Optional[str]:
        """Extract data from CSV/TSV file"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self._extract_sync, path
        )

    def _extract_sync(self, path: Path) -> Optional[str]:
        """Synchronous extraction"""
        try:
            # Detect encoding
            with open(path, 'rb') as f:
                raw_data = f.read(10000)  # Sample first 10KB
                result = chardet.detect(raw_data)
                encoding = result['encoding'] or 'utf-8'

            # Detect delimiter
            with open(path, 'r', encoding=encoding, errors='replace') as f:
                sample = f.read(4096)
                delimiter = self._detect_delimiter(sample)

            # Read CSV
            rows = []
            with open(path, 'r', encoding=encoding, errors='replace', newline='') as f:
                reader = csv.reader(f, delimiter=delimiter)

                row_count = 0
                for row in reader:
                    if row_count >= self.max_rows:
                        logger.warning(f"Reached max rows ({self.max_rows}) for {path}")
                        break

                    # Skip empty rows
                    if not any(cell.strip() for cell in row):
                        continue

                    # Join cells with delimiter for readability
                    rows.append(delimiter.join(cell.strip() for cell in row))
                    row_count += 1

            if not rows:
                logger.info(f"No data in CSV file: {path}")
                return None

            return "\n".join(rows)

        except Exception as e:
            logger.error(f"CSV extraction failed for {path}: {e}")
            return None

    def _detect_delimiter(self, sample: str) -> str:
        """
        Detect the delimiter used in the CSV file.

        Tries common delimiters and picks the most likely one.
        """
        delimiters = [',', '\t', ';', '|']
        delimiter_counts = {}

        for delimiter in delimiters:
            # Count occurrences in first few lines
            lines = sample.split('\n')[:5]
            counts = [line.count(delimiter) for line in lines]

            # Good delimiter should have consistent count per line
            if counts and max(counts) > 0:
                # Check consistency (standard deviation)
                avg = sum(counts) / len(counts)
                variance = sum((c - avg) ** 2 for c in counts) / len(counts)

                # Lower variance = more consistent = better delimiter
                delimiter_counts[delimiter] = (avg, -variance)

        if not delimiter_counts:
            return ','  # Default to comma

        # Pick delimiter with highest average count and lowest variance
        best_delimiter = max(delimiter_counts.keys(),
                           key=lambda d: delimiter_counts[d])

        logger.debug(f"Detected delimiter: {repr(best_delimiter)}")
        return best_delimiter


class FixedWidthHandler(BaseHandler):
    """
    Handler for fixed-width text files (common in legacy systems).

    Note: Requires column specifications. This is a placeholder for
    Claude-generated handlers with specific column widths.
    """

    @classmethod
    def supported_extensions(cls) -> set[str]:
        return {'.txt', '.dat'}

    async def extract(self, path: Path) -> Optional[str]:
        """Extract from fixed-width file"""
        # This is a generic implementation
        # Claude will generate specific handlers with proper column definitions

        try:
            # Detect encoding
            with open(path, 'rb') as f:
                raw_data = f.read(10000)
                result = chardet.detect(raw_data)
                encoding = result['encoding'] or 'utf-8'

            # Read as plain text
            with open(path, 'r', encoding=encoding, errors='replace') as f:
                content = f.read()

            if not content.strip():
                return None

            return content

        except Exception as e:
            logger.error(f"Fixed-width extraction failed for {path}: {e}")
            return None
