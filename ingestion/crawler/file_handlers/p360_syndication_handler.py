"""
P360 Syndication XML Handler

Parses EATON's P360/Informatica syndication XML format.

Format characteristics:
- <envelope><item> structure
- 79 elements per product
- Multi-value fields (pipe-delimited)
- Nested images, documents, attributes, associations
- 109 products per file (sample)

Output: Structured product data ready for syndication
"""

import xml.etree.ElementTree as ET
import logging
import json
from pathlib import Path
from typing import Optional, Dict, List

from .base import BaseHandler

logger = logging.getLogger(__name__)


class P360SyndicationHandler(BaseHandler):
    """
    Handler for P360/Informatica syndication XML files.

    Parses EATON's product syndication format with full metadata:
    - Product identifiers (SKU, UPC, GTIN, EAN)
    - Classifications (ETIM, UNSPSC, IGCC)
    - Descriptions (marketing, technical, invoice)
    - Features & applications (pipe-delimited)
    - Dimensions (product + package)
    - Attributes (name-value pairs)
    - Images (multiple resolutions, priorities)
    - Documents (72 types)
    - Product associations (accessories, replacements)
    - Compliance (warranty, certifications)
    """

    @property
    def supported_extensions(self) -> List[str]:
        return [".xml"]

    def can_handle(self, file_path: Path) -> bool:
        """Check if XML file is P360 syndication format."""
        if file_path.suffix.lower() != ".xml":
            return False

        # Check for P360 envelope structure
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # P360 format has <envelope><item> structure
            if root.tag == "envelope" and root.find("item") is not None:
                logger.info(f"Detected P360 syndication format: {file_path.name}")
                return True

        except Exception:
            pass

        return False

    async def extract(self, file_path: Path) -> Optional[str]:
        """
        Extract P360 syndication XML to structured text.

        Converts XML to human-readable product catalog format
        suitable for RAG and syndication processing.
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            if root.tag != "envelope":
                logger.warning(f"Not a P360 envelope: {file_path.name}")
                return None

            products = []
            items = root.findall("item")

            logger.info(f"Parsing {len(items)} products from P360 XML")

            for idx, item in enumerate(items, 1):
                try:
                    product_text = self._extract_product(item, idx)
                    products.append(product_text)
                except Exception as e:
                    logger.error(f"Error parsing product {idx}: {e}")
                    continue

            # Join all products
            output = f"P360 SYNDICATION CATALOG - {len(products)} PRODUCTS\n"
            output += "=" * 80 + "\n\n"
            output += "\n\n".join(products)

            logger.info(f"✓ Extracted {len(products)} products from {file_path.name}")

            return output

        except Exception as e:
            logger.error(f"Failed to parse P360 XML: {e}")
            return None

    def _extract_product(self, item: ET.Element, index: int) -> str:
        """Extract single product from XML item element."""

        # Helper to get text safely
        def get_text(tag: str, default: str = "") -> str:
            elem = item.find(tag)
            return elem.text.strip() if elem is not None and elem.text else default

        # IDENTIFIERS
        catalog = get_text("catalog")
        upc = get_text("upc")
        gtin = get_text("gtin")
        ean = get_text("ean")

        # CLASSIFICATIONS
        etim = get_text("etim")
        unspsc = get_text("unspsc")
        igcc = get_text("igcc")

        # BRANDING
        brand = get_text("brandLabel")
        trade_name = get_text("TradeName")
        prod_type = get_text("prodType")
        prod_name = get_text("prodName")

        # DESCRIPTIONS
        long_desc = get_text("longDesc")
        mark_desc = get_text("markDesc")
        keywords = get_text("Keywords")

        # FEATURES (pipe-delimited)
        features = get_text("prodFeature")
        features_list = [f.strip() for f in features.split("|") if f.strip()]

        # SEGMENTS & APPLICATIONS
        segment = get_text("Segment")
        application = get_text("Application")

        # DIMENSIONS
        prod_hgt = get_text("prodHgt")
        prod_wid = get_text("prodWid")
        prod_len = get_text("prodLen")
        prod_wt = get_text("prodWt")
        prod_hgt_uom = get_text("prodHgtUOM")
        prod_wt_uom = get_text("prodWtUOM")

        # COMPLIANCE
        warranty = get_text("Warranty")
        certifications = get_text("Certifications")
        compliances = get_text("Compliances")

        # COUNT MEDIA
        images = item.findall("image")
        docs = item.findall("doc")
        associations = item.findall("ItemAssociation")
        attributes = item.findall("attribute")

        # Build structured text
        output = []
        output.append(f"PRODUCT #{index}: {catalog}")
        output.append("-" * 80)

        # Basic Info
        output.append(f"\n**PRODUCT NAME:** {prod_name}")
        output.append(f"**BRAND:** {brand} {trade_name}")
        output.append(f"**TYPE:** {prod_type}")
        output.append(f"\n**IDENTIFIERS:**")
        output.append(f"  SKU: {catalog}")
        output.append(f"  UPC: {upc}")
        output.append(f"  GTIN: {gtin}")
        if ean:
            output.append(f"  EAN: {ean}")

        # Classifications
        output.append(f"\n**CLASSIFICATIONS:**")
        output.append(f"  ETIM: {etim}")
        output.append(f"  UNSPSC: {unspsc}")
        output.append(f"  IGCC: {igcc}")

        # Description
        if long_desc:
            output.append(f"\n**DESCRIPTION:** {long_desc}")

        if mark_desc:
            output.append(f"\n**MARKETING:**")
            output.append(mark_desc[:500])  # Limit for RAG chunking

        # Features
        if features_list:
            output.append(f"\n**KEY FEATURES:**")
            for feat in features_list[:10]:  # Top 10
                output.append(f"  • {feat}")

        # Dimensions
        if prod_hgt and prod_wid and prod_len:
            output.append(f"\n**DIMENSIONS:** {prod_hgt} × {prod_wid} × {prod_len} {prod_hgt_uom}")
        if prod_wt:
            output.append(f"**WEIGHT:** {prod_wt} {prod_wt_uom}")

        # Segments
        if segment:
            segments = [s.strip() for s in segment.split("|") if s.strip()]
            output.append(f"\n**TARGET SEGMENTS:** {', '.join(segments[:5])}")

        # Applications
        if application:
            apps = [a.strip() for a in application.split("|") if a.strip()]
            output.append(f"**APPLICATIONS:** {', '.join(apps[:5])}")

        # Compliance
        if certifications:
            output.append(f"\n**CERTIFICATIONS:** {certifications}")
        if warranty:
            output.append(f"**WARRANTY:** {warranty[:200]}")  # Truncate long warranties

        # Media counts
        output.append(f"\n**MEDIA:**")
        output.append(f"  Images: {len(images)} (multiple resolutions)")
        output.append(f"  Documents: {len(docs)} technical/marketing files")
        if associations:
            output.append(f"  Related Products: {len(associations)} associations")
        if attributes:
            output.append(f"  Technical Attributes: {len(attributes)} specifications")

        # Keywords
        if keywords:
            output.append(f"\n**KEYWORDS:** {keywords}")

        return "\n".join(output)

    def metadata(self, file_path: Path) -> Dict:
        """Extract metadata from P360 XML."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            items = root.findall("item")

            # Count media elements
            total_images = sum(len(item.findall("image")) for item in items)
            total_docs = sum(len(item.findall("doc")) for item in items)
            total_attrs = sum(len(item.findall("attribute")) for item in items)

            return {
                "format": "P360_Syndication_XML",
                "products": len(items),
                "total_images": total_images,
                "total_documents": total_docs,
                "total_attributes": total_attrs,
                "source": "Informatica_P360"
            }
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {}
