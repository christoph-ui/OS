"""
XML Handler - Extract data from XML files
"""

import asyncio
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional
import logging

from .base import BaseHandler

logger = logging.getLogger(__name__)


class XMLHandler(BaseHandler):
    """
    Extract text content from XML files.

    Generic XML handler that extracts all text content.
    For specific XML schemas (DATEV, BMEcat, etc.), Claude will generate
    specialized handlers.
    """

    @classmethod
    def supported_extensions(cls) -> set[str]:
        return {'.xml'}

    async def extract(self, path: Path) -> Optional[str]:
        """Extract text from XML file"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self._extract_sync, path
        )

    def _extract_sync(self, path: Path) -> Optional[str]:
        """Synchronous extraction"""
        try:
            # Parse XML
            tree = ET.parse(str(path))
            root = tree.getroot()

            # Extract all text content
            text_parts = []
            self._extract_element_text(root, text_parts)

            if not text_parts:
                logger.info(f"No text content in XML: {path}")
                return None

            return "\n".join(text_parts)

        except ET.ParseError as e:
            logger.error(f"XML parsing failed for {path}: {e}")
            return None
        except Exception as e:
            logger.error(f"XML extraction failed for {path}: {e}")
            return None

    def _extract_element_text(self, element: ET.Element, text_parts: list, depth: int = 0):
        """
        Recursively extract text from XML elements.

        Args:
            element: XML element
            text_parts: List to accumulate text
            depth: Current depth (for indentation)
        """
        # Get element tag (remove namespace if present)
        tag = element.tag.split('}')[-1] if '}' in element.tag else element.tag

        # Add element text if present
        if element.text and element.text.strip():
            indent = "  " * depth
            text_parts.append(f"{indent}{tag}: {element.text.strip()}")

        # Process attributes (if meaningful)
        for attr_name, attr_value in element.attrib.items():
            if attr_value and len(attr_value) > 3:  # Skip short/meaningless attrs
                indent = "  " * depth
                text_parts.append(f"{indent}@{attr_name}: {attr_value}")

        # Recurse into children
        for child in element:
            self._extract_element_text(child, text_parts, depth + 1)

        # Add tail text if present
        if element.tail and element.tail.strip():
            text_parts.append(element.tail.strip())


class HTMLHandler(BaseHandler):
    """
    Extract text from HTML files.

    Uses BeautifulSoup for robust HTML parsing.
    """

    @classmethod
    def supported_extensions(cls) -> set[str]:
        return {'.html', '.htm'}

    async def extract(self, path: Path) -> Optional[str]:
        """Extract text from HTML file"""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            logger.error("beautifulsoup4 not installed, cannot parse HTML")
            return None

        return await asyncio.get_event_loop().run_in_executor(
            None, self._extract_sync, path
        )

    def _extract_sync(self, path: Path) -> Optional[str]:
        """Synchronous extraction"""
        try:
            from bs4 import BeautifulSoup

            # Read HTML
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                html = f.read()

            # Parse with BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Extract text
            text = soup.get_text(separator='\n', strip=True)

            # Clean up whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            text = '\n'.join(lines)

            if not text:
                logger.info(f"No text content in HTML: {path}")
                return None

            return text

        except Exception as e:
            logger.error(f"HTML extraction failed for {path}: {e}")
            return None


class JSONHandler(BaseHandler):
    """
    Extract text from JSON files.

    Converts JSON to readable text format.
    """

    @classmethod
    def supported_extensions(cls) -> set[str]:
        return {'.json'}

    async def extract(self, path: Path) -> Optional[str]:
        """Extract text from JSON file"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self._extract_sync, path
        )

    def _extract_sync(self, path: Path) -> Optional[str]:
        """Synchronous extraction"""
        try:
            import json

            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                data = json.load(f)

            # Convert JSON to readable text
            text_parts = []
            self._json_to_text(data, text_parts)

            if not text_parts:
                logger.info(f"No meaningful content in JSON: {path}")
                return None

            return "\n".join(text_parts)

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed for {path}: {e}")
            return None
        except Exception as e:
            logger.error(f"JSON extraction failed for {path}: {e}")
            return None

    def _json_to_text(self, obj, text_parts: list, prefix: str = ""):
        """Convert JSON object to text recursively"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    text_parts.append(f"{prefix}{key}:")
                    self._json_to_text(value, text_parts, prefix + "  ")
                else:
                    text_parts.append(f"{prefix}{key}: {value}")

        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, (dict, list)):
                    text_parts.append(f"{prefix}[{i}]:")
                    self._json_to_text(item, text_parts, prefix + "  ")
                else:
                    text_parts.append(f"{prefix}- {item}")

        else:
            text_parts.append(f"{prefix}{obj}")
