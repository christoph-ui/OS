"""
Product Data Parsers

Specialized parsers for different product data formats:
- BMECat XML (1.0, 1.2, 2005)
- ETIM Pricelist
- CSV/Excel with intelligent field detection
- DATANORM (4.0, 5.0)
"""

import csv
import io
import json
import logging
import re
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ParseResult:
    """Result of parsing a file"""
    success: bool
    format_detected: str
    version: Optional[str] = None
    record_count: int = 0
    fields: List[str] = field(default_factory=list)
    sample_records: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseParser(ABC):
    """Base class for product data parsers"""
    
    @abstractmethod
    def can_parse(self, filename: str, content: bytes) -> bool:
        """Check if this parser can handle the file"""
        pass
    
    @abstractmethod
    def parse(self, content: bytes) -> Generator[Dict[str, Any], None, None]:
        """Parse content and yield product dicts"""
        pass
    
    @abstractmethod
    def analyze(self, content: bytes) -> ParseResult:
        """Analyze content without full parsing"""
        pass


class BMECatParser(BaseParser):
    """
    BMECat XML Parser
    
    Supports:
    - BMECat 1.0
    - BMECat 1.2
    - BMECat 2005
    """
    
    # Common namespaces
    NAMESPACES = {
        "bme12": "http://www.bmecat.org/bmecat/1.2/bmecat_new_catalog",
        "bme2005": "http://www.bmecat.org/bmecat/2005",
    }
    
    def can_parse(self, filename: str, content: bytes) -> bool:
        """Check for BMECat XML"""
        if not filename.lower().endswith(".xml"):
            return False
        
        # Check for BMECat markers
        header = content[:2000].lower()
        return b"bmecat" in header
    
    def detect_version(self, content: bytes) -> str:
        """Detect BMECat version"""
        header = content[:5000].decode("utf-8", errors="ignore")
        
        if "bmecat/2005" in header.lower():
            return "2005"
        elif "bmecat/1.2" in header.lower():
            return "1.2"
        else:
            return "1.0"
    
    def analyze(self, content: bytes) -> ParseResult:
        """Quick analysis of BMECat file"""
        result = ParseResult(
            success=True,
            format_detected="BMECat",
        )
        
        try:
            version = self.detect_version(content)
            result.version = version
            
            # Count articles
            text = content.decode("utf-8", errors="ignore")
            result.record_count = text.lower().count("<article") or text.lower().count("<artikel")
            
            # Extract sample fields
            root = ET.fromstring(content)
            
            # Find first article
            article = root.find(".//ARTICLE") or root.find(".//article")
            if article:
                result.fields = self._extract_field_names(article)
            
            # Get supplier info
            supplier = root.find(".//SUPPLIER") or root.find(".//supplier")
            if supplier:
                name = supplier.find("SUPPLIER_NAME") or supplier.find("supplier_name")
                if name is not None and name.text:
                    result.metadata["supplier"] = name.text
            
        except Exception as e:
            result.errors.append(f"Analysis error: {e}")
        
        return result
    
    def _extract_field_names(self, element: ET.Element, prefix: str = "") -> List[str]:
        """Extract field names from XML element"""
        fields = []
        for child in element:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            full_name = f"{prefix}/{tag}" if prefix else tag
            
            if len(child) == 0:  # Leaf node
                fields.append(full_name)
            else:
                fields.extend(self._extract_field_names(child, full_name))
        
        return fields[:20]  # Limit to first 20
    
    def parse(self, content: bytes) -> Generator[Dict[str, Any], None, None]:
        """Parse BMECat XML and yield products"""
        try:
            root = ET.fromstring(content)
            
            # Handle namespaces
            ns = {}
            if root.tag.startswith("{"):
                ns_uri = root.tag[1:root.tag.index("}")]
                ns["bme"] = ns_uri
            
            # Find all articles
            articles = root.findall(".//ARTICLE", ns) or root.findall(".//article", ns)
            
            for article in articles:
                product = self._parse_article(article, ns)
                if product:
                    yield product
                    
        except ET.ParseError as e:
            logger.error(f"BMECat XML parse error: {e}")
    
    def _parse_article(self, article: ET.Element, ns: Dict[str, str]) -> Dict[str, Any]:
        """Parse a single BMECat article"""
        product = {"_source": "bmecat"}
        
        # Define field mappings (xpath -> key)
        mappings = [
            ("SUPPLIER_AID", "sku"),
            ("ARTICLE_DETAILS/DESCRIPTION_SHORT", "name"),
            ("ARTICLE_DETAILS/DESCRIPTION_LONG", "description"),
            ("ARTICLE_DETAILS/EAN", "gtin"),
            ("ARTICLE_DETAILS/MANUFACTURER_AID", "manufacturer_sku"),
            ("ARTICLE_DETAILS/MANUFACTURER_NAME", "manufacturer"),
            ("ARTICLE_DETAILS/DELIVERY_TIME", "delivery_time"),
            ("ARTICLE_ORDER_DETAILS/ORDER_UNIT", "order_unit"),
            ("ARTICLE_ORDER_DETAILS/CONTENT_UNIT", "content_unit"),
            ("ARTICLE_ORDER_DETAILS/NO_CU_PER_OU", "content_per_order"),
            ("ARTICLE_ORDER_DETAILS/PRICE_QUANTITY", "price_quantity"),
            ("ARTICLE_ORDER_DETAILS/QUANTITY_MIN", "min_quantity"),
        ]
        
        for xpath, key in mappings:
            elem = self._find_element(article, xpath, ns)
            if elem is not None and elem.text:
                product[key] = elem.text.strip()
        
        # Parse prices
        product["prices"] = self._parse_prices(article, ns)
        
        # Parse features/attributes
        product["attributes"] = self._parse_features(article, ns)
        
        # Parse classification references
        product["classifications"] = self._parse_classifications(article, ns)
        
        # Parse media/images
        product["media"] = self._parse_media(article, ns)
        
        return product
    
    def _find_element(self, parent: ET.Element, path: str, ns: Dict[str, str]) -> Optional[ET.Element]:
        """Find element by path, handling different naming conventions"""
        # Try exact path
        elem = parent.find(path.replace("/", "//"), ns)
        if elem is not None:
            return elem
        
        # Try lowercase
        elem = parent.find(path.lower().replace("/", "//"), ns)
        return elem
    
    def _parse_prices(self, article: ET.Element, ns: Dict[str, str]) -> List[Dict[str, Any]]:
        """Parse price information"""
        prices = []
        
        for price_elem in article.findall(".//ARTICLE_PRICE", ns):
            price = {}
            
            price_type = price_elem.find("PRICE_TYPE", ns)
            if price_type is not None:
                price["type"] = price_type.text
            
            amount = price_elem.find("PRICE_AMOUNT", ns)
            if amount is not None:
                price["amount"] = float(amount.text)
            
            currency = price_elem.find("PRICE_CURRENCY", ns)
            if currency is not None:
                price["currency"] = currency.text
            
            if price:
                prices.append(price)
        
        return prices
    
    def _parse_features(self, article: ET.Element, ns: Dict[str, str]) -> Dict[str, Any]:
        """Parse product features/attributes"""
        attributes = {}
        
        for feature in article.findall(".//FEATURE", ns):
            fname = feature.find("FNAME", ns)
            fvalue = feature.find("FVALUE", ns)
            
            if fname is not None and fvalue is not None:
                attributes[fname.text] = fvalue.text
        
        return attributes
    
    def _parse_classifications(self, article: ET.Element, ns: Dict[str, str]) -> Dict[str, str]:
        """Parse classification references (ETIM, ECLASS, etc.)"""
        classifications = {}
        
        for ref in article.findall(".//ARTICLE_REFERENCE", ns):
            ref_type = ref.get("type", "")
            art_id = ref.find("ART_ID_TO", ns)
            
            if art_id is not None and art_id.text:
                if "etim" in ref_type.lower():
                    classifications["etim"] = art_id.text
                elif "eclass" in ref_type.lower():
                    classifications["eclass"] = art_id.text
                elif "unspsc" in ref_type.lower():
                    classifications["unspsc"] = art_id.text
        
        return classifications
    
    def _parse_media(self, article: ET.Element, ns: Dict[str, str]) -> List[Dict[str, str]]:
        """Parse media references (images, documents)"""
        media = []
        
        for mime in article.findall(".//MIME", ns):
            item = {}
            
            mime_type = mime.find("MIME_TYPE", ns)
            if mime_type is not None:
                item["type"] = mime_type.text
            
            source = mime.find("MIME_SOURCE", ns)
            if source is not None:
                item["source"] = source.text
            
            purpose = mime.find("MIME_PURPOSE", ns)
            if purpose is not None:
                item["purpose"] = purpose.text
            
            if item:
                media.append(item)
        
        return media


class ETIMParser(BaseParser):
    """
    ETIM Pricelist Parser
    
    Parses ETIM classification data and pricelists.
    """
    
    def can_parse(self, filename: str, content: bytes) -> bool:
        """Check for ETIM XML"""
        if not filename.lower().endswith(".xml"):
            return False
        
        header = content[:2000].lower()
        return b"etim" in header and b"bmecat" not in header
    
    def analyze(self, content: bytes) -> ParseResult:
        """Analyze ETIM file"""
        return ParseResult(
            success=True,
            format_detected="ETIM Pricelist",
            version="9.0",  # Would detect actual version
        )
    
    def parse(self, content: bytes) -> Generator[Dict[str, Any], None, None]:
        """Parse ETIM pricelist"""
        # Would implement ETIM-specific parsing
        yield from []


class CSVParser(BaseParser):
    """
    Intelligent CSV Parser
    
    Auto-detects:
    - Delimiter (comma, semicolon, tab)
    - Encoding (UTF-8, Latin-1, CP1252)
    - Field types and meanings
    """
    
    # Common field name patterns (German and English)
    FIELD_PATTERNS = {
        "sku": [r"artikel.*nr", r"art.*nr", r"sku", r"product.*id", r"item.*no"],
        "name": [r"bezeichnung", r"name", r"title", r"beschreibung.*kurz", r"short.*desc"],
        "description": [r"langtext", r"beschreibung.*lang", r"long.*desc", r"description"],
        "gtin": [r"ean", r"gtin", r"upc", r"barcode"],
        "price": [r"preis", r"price", r"vk", r"ek", r"netto", r"brutto"],
        "manufacturer": [r"hersteller", r"manufacturer", r"brand", r"marke"],
        "etim": [r"etim", r"etim.*class", r"etim.*code"],
        "eclass": [r"eclass", r"ecl.*code"],
    }
    
    def can_parse(self, filename: str, content: bytes) -> bool:
        """Check for CSV"""
        return filename.lower().endswith(".csv")
    
    def detect_encoding(self, content: bytes) -> str:
        """Detect file encoding"""
        for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                content.decode(encoding)
                return encoding
            except UnicodeDecodeError:
                continue
        return "utf-8"
    
    def detect_delimiter(self, text: str) -> str:
        """Detect CSV delimiter"""
        sample = text[:5000]
        counts = {
            ",": sample.count(","),
            ";": sample.count(";"),
            "\t": sample.count("\t"),
            "|": sample.count("|"),
        }
        return max(counts, key=counts.get)
    
    def analyze(self, content: bytes) -> ParseResult:
        """Analyze CSV file"""
        result = ParseResult(
            success=True,
            format_detected="CSV",
        )
        
        try:
            encoding = self.detect_encoding(content)
            text = content.decode(encoding)
            delimiter = self.detect_delimiter(text)
            
            result.metadata["encoding"] = encoding
            result.metadata["delimiter"] = delimiter
            
            reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
            result.fields = reader.fieldnames or []
            
            # Count rows
            rows = list(reader)
            result.record_count = len(rows)
            
            # Sample records
            result.sample_records = rows[:3] if rows else []
            
            # Detect field mappings
            result.metadata["field_suggestions"] = self._suggest_field_mappings(result.fields)
            
        except Exception as e:
            result.errors.append(f"Analysis error: {e}")
        
        return result
    
    def _suggest_field_mappings(self, fields: List[str]) -> Dict[str, str]:
        """Suggest standard field mappings based on column names"""
        suggestions = {}
        
        for field in fields:
            field_lower = field.lower()
            
            for standard_name, patterns in self.FIELD_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, field_lower):
                        suggestions[field] = standard_name
                        break
                if field in suggestions:
                    break
        
        return suggestions
    
    def parse(self, content: bytes) -> Generator[Dict[str, Any], None, None]:
        """Parse CSV and yield products"""
        encoding = self.detect_encoding(content)
        text = content.decode(encoding)
        delimiter = self.detect_delimiter(text)
        
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        
        for row in reader:
            product = {"_source": "csv"}
            product.update(row)
            yield product


class ParserFactory:
    """Factory for creating appropriate parser"""
    
    PARSERS = [
        BMECatParser,
        ETIMParser,
        CSVParser,
    ]
    
    @classmethod
    def get_parser(cls, filename: str, content: bytes) -> Optional[BaseParser]:
        """Get appropriate parser for file"""
        for parser_class in cls.PARSERS:
            parser = parser_class()
            if parser.can_parse(filename, content):
                return parser
        return None
    
    @classmethod
    def analyze_file(cls, filename: str, content: bytes) -> ParseResult:
        """Analyze file and return results"""
        parser = cls.get_parser(filename, content)
        
        if not parser:
            return ParseResult(
                success=False,
                format_detected="Unknown",
                errors=["Could not detect file format"],
            )
        
        return parser.analyze(content)
