#!/usr/bin/env python3
"""
Ingest P360 Syndication XML to Lakehouse

Parses EATON's P360/Informatica syndication XML and loads product data
into a dedicated `syndication_products` Delta table optimized for
multi-channel content syndication (BMEcat, Amazon, CNET, etc.).

Data structure: 109 products × 79 fields per product
- 7 identifiers (SKU, UPC, GTIN, EAN, ETIM, UNSPSC, IGCC)
- Classifications & branding
- Descriptions (long, marketing, invoice)
- Features & applications (pipe-delimited)
- Dimensions (product + package)
- 40-80 technical attributes per product
- 37 images (multiple resolutions)
- 15 documents per product
- 21 product associations

Output: Delta Lake table at /data/lakehouse/delta/syndication_products

Created: 2026-01-12
Author: Claude Code
"""

import sys
import logging
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pyarrow as pa
from deltalake import write_deltalake

from core.paths import CustomerPaths

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class P360SyndicationIngester:
    """
    Ingests P360 syndication XML into Delta Lake.

    Creates a specialized table for syndication with full product metadata.
    """

    def __init__(self, customer_id: str = "eaton"):
        self.customer_id = customer_id

        # Get persistent lakehouse path
        self.lakehouse_path = CustomerPaths.get_lakehouse_path(customer_id)
        logger.info(f"Lakehouse path: {self.lakehouse_path}")

        # Validate not /tmp
        if not CustomerPaths.validate_path_safety(self.lakehouse_path):
            raise ValueError("UNSAFE: Lakehouse path is in /tmp!")

        self.delta_path = self.lakehouse_path / "delta"
        self.table_path = self.delta_path / "syndication_products"

        # P360 XML source
        self.p360_xml_path = Path("/tmp/eaton_syndication/EATON 2/P360_Future_Syndication_Sample_20251010/Temp_Samples_Future_Syndication_10_10_2025.xml")

        if not self.p360_xml_path.exists():
            raise FileNotFoundError(f"P360 XML not found: {self.p360_xml_path}")

    def parse_p360_xml(self) -> List[Dict[str, Any]]:
        """
        Parse P360 XML and extract all product fields.

        Returns:
            List of product dictionaries with full metadata
        """
        logger.info(f"Parsing P360 XML: {self.p360_xml_path}")

        tree = ET.parse(self.p360_xml_path)
        root = tree.getroot()

        if root.tag != "envelope":
            raise ValueError("Not a P360 envelope XML")

        items = root.findall("item")
        logger.info(f"Found {len(items)} products in P360 XML")

        products = []
        for idx, item in enumerate(items, 1):
            try:
                product = self._parse_product_item(item, idx)
                products.append(product)
            except Exception as e:
                logger.error(f"Error parsing product {idx}: {e}")
                continue

        logger.info(f"✓ Parsed {len(products)} products")
        return products

    def _parse_product_item(self, item: ET.Element, index: int) -> Dict[str, Any]:
        """Extract all fields from a single <item> element"""

        def get_text(tag: str, default: str = "") -> str:
            """Get text content of XML tag safely"""
            elem = item.find(tag)
            return elem.text.strip() if elem is not None and elem.text else default

        def get_list(tag: str, delimiter: str = "|") -> List[str]:
            """Parse pipe-delimited text into list"""
            text = get_text(tag)
            if not text:
                return []
            return [x.strip() for x in text.split(delimiter) if x.strip()]

        # Count media elements
        images = item.findall("image")
        docs = item.findall("doc")
        associations = item.findall("ItemAssociation")
        attributes = item.findall("attribute")

        # Extract primary image URL (priority 1, 1000x1000)
        primary_image_url = ""
        for img in images:
            priority = img.find("image_priority")
            if priority is not None and priority.text == "1":
                url_elem = img.find("imageURL")
                if url_elem is not None and url_elem.text:
                    if "1000x1000" in url_elem.text:
                        primary_image_url = url_elem.text
                        break

        # Extract datasheet URL (first document with type=Specification)
        datasheet_url = ""
        for doc in docs:
            doctype = doc.find("doctype")
            if doctype is not None and "Specification" in doctype.text:
                url_elem = doc.find("docURL")
                if url_elem is not None and url_elem.text:
                    datasheet_url = url_elem.text
                    break

        # Parse attributes into JSON
        attributes_dict = {}
        for attr in attributes:
            name_elem = attr.find("name")
            value_elem = attr.find("value")
            if name_elem is not None and value_elem is not None:
                if name_elem.text and value_elem.text:
                    attributes_dict[name_elem.text] = value_elem.text

        # Build product record
        product = {
            # Core identifiers
            "product_id": get_text("catalog"),
            "supplier_pid": get_text("catalog"),
            "upc": get_text("upc"),
            "gtin": get_text("gtin"),
            "ean": get_text("ean"),

            # Classifications
            "etim_class": get_text("etim"),
            "unspsc": get_text("unspsc"),
            "igcc": get_text("igcc"),
            "commodity_code": get_text("commodityCode"),

            # Branding
            "manufacturer_name": get_text("brandLabel", "Eaton"),
            "brand_label": get_text("brandLabel"),
            "sub_brand": get_text("subBrand"),
            "trade_name": get_text("TradeName"),
            "product_type": get_text("prodType"),
            "product_subtype": get_text("prodSubType"),
            "product_name": get_text("prodName"),

            # Descriptions
            "short_description": get_text("longDesc"),  # 1-liner
            "long_description": get_text("markDesc"),  # Marketing text
            "invoice_description": get_text("InvDesc"),
            "keywords": get_text("Keywords"),
            "catalog_notes": get_text("catNotes"),

            # Features (store as JSON array)
            "features": json.dumps(get_list("prodFeature")),
            "segments": json.dumps(get_list("Segment")),
            "applications": json.dumps(get_list("Application")),

            # Dimensions - Product
            "product_height": get_text("prodHgt"),
            "product_width": get_text("prodWid"),
            "product_length": get_text("prodLen"),
            "product_weight": get_text("prodWt"),
            "product_height_uom": get_text("prodHgtUOM"),
            "product_weight_uom": get_text("prodWtUOM"),

            # Dimensions - Package
            "package_height": get_text("unitHgt"),
            "package_width": get_text("unitWid"),
            "package_length": get_text("unitLen"),
            "package_gross_weight": get_text("unitGrossWt"),
            "package_height_uom": get_text("unitHgtUOM"),
            "package_weight_uom": get_text("unitGrossWtUOM"),

            # Compliance
            "warranty": get_text("Warranty"),
            "warranty_country": get_text("WarrantyCountry"),
            "certifications": get_text("Certifications"),
            "compliances": get_text("Compliances"),
            "country_of_origin": get_text("cntryOfOrg"),

            # Commercial (if available)
            "list_price": get_text("ListPrice"),
            "currency": get_text("Currency"),
            "lead_time": get_text("leadTime"),
            "lead_time_uom": get_text("leadTimeUOM"),
            "min_order_qty": get_text("ordMin"),
            "stock_indicator": get_text("stkInd"),

            # Media URLs
            "primary_image_url": primary_image_url,
            "datasheet_url": datasheet_url,

            # Media counts
            "image_count": len(images),
            "document_count": len(docs),
            "association_count": len(associations),
            "attribute_count": len(attributes),

            # Technical attributes (as JSON)
            "technical_attributes": json.dumps(attributes_dict),

            # Metadata
            "source": "P360_Syndication_XML",
            "ingested_at": datetime.utcnow().isoformat(),
            "index": index
        }

        return product

    def create_delta_table(self, products: List[Dict[str, Any]]):
        """
        Write products to Delta Lake table.

        Creates `syndication_products` table with optimized schema.
        """
        logger.info(f"Creating Delta table: {self.table_path}")

        # Define PyArrow schema
        schema = pa.schema([
            # Core identifiers
            ("product_id", pa.string()),
            ("supplier_pid", pa.string()),
            ("upc", pa.string()),
            ("gtin", pa.string()),
            ("ean", pa.string()),

            # Classifications
            ("etim_class", pa.string()),
            ("unspsc", pa.string()),
            ("igcc", pa.string()),
            ("commodity_code", pa.string()),

            # Branding
            ("manufacturer_name", pa.string()),
            ("brand_label", pa.string()),
            ("sub_brand", pa.string()),
            ("trade_name", pa.string()),
            ("product_type", pa.string()),
            ("product_subtype", pa.string()),
            ("product_name", pa.string()),

            # Descriptions
            ("short_description", pa.string()),
            ("long_description", pa.large_string()),
            ("invoice_description", pa.string()),
            ("keywords", pa.string()),
            ("catalog_notes", pa.string()),

            # Features (JSON arrays)
            ("features", pa.string()),
            ("segments", pa.string()),
            ("applications", pa.string()),

            # Dimensions - Product
            ("product_height", pa.string()),
            ("product_width", pa.string()),
            ("product_length", pa.string()),
            ("product_weight", pa.string()),
            ("product_height_uom", pa.string()),
            ("product_weight_uom", pa.string()),

            # Dimensions - Package
            ("package_height", pa.string()),
            ("package_width", pa.string()),
            ("package_length", pa.string()),
            ("package_gross_weight", pa.string()),
            ("package_height_uom", pa.string()),
            ("package_weight_uom", pa.string()),

            # Compliance
            ("warranty", pa.string()),
            ("warranty_country", pa.string()),
            ("certifications", pa.string()),
            ("compliances", pa.string()),
            ("country_of_origin", pa.string()),

            # Commercial
            ("list_price", pa.string()),
            ("currency", pa.string()),
            ("lead_time", pa.string()),
            ("lead_time_uom", pa.string()),
            ("min_order_qty", pa.string()),
            ("stock_indicator", pa.string()),

            # Media URLs
            ("primary_image_url", pa.string()),
            ("datasheet_url", pa.string()),

            # Media counts
            ("image_count", pa.int32()),
            ("document_count", pa.int32()),
            ("association_count", pa.int32()),
            ("attribute_count", pa.int32()),

            # Technical attributes (JSON)
            ("technical_attributes", pa.large_string()),

            # Metadata
            ("source", pa.string()),
            ("ingested_at", pa.string()),
            ("index", pa.int32()),
        ])

        # Create PyArrow table
        table = pa.Table.from_pylist(products, schema=schema)

        # Write to Delta Lake
        write_deltalake(
            str(self.table_path),
            table,
            mode="overwrite",  # Replace existing data
            schema_mode="overwrite"
        )

        logger.info(f"✓ Wrote {len(products)} products to Delta Lake")

    def print_statistics(self, products: List[Dict[str, Any]]):
        """Print ingestion statistics"""
        total_products = len(products)
        total_images = sum(p["image_count"] for p in products)
        total_docs = sum(p["document_count"] for p in products)
        total_attrs = sum(p["attribute_count"] for p in products)
        total_assocs = sum(p["association_count"] for p in products)

        # Count by product type
        by_type = {}
        for p in products:
            ptype = p.get("product_type", "Unknown")
            by_type[ptype] = by_type.get(ptype, 0) + 1

        logger.info("")
        logger.info("=" * 70)
        logger.info("INGESTION STATISTICS")
        logger.info("=" * 70)
        logger.info(f"  Total products:    {total_products}")
        logger.info(f"  Total images:      {total_images}")
        logger.info(f"  Total documents:   {total_docs}")
        logger.info(f"  Total attributes:  {total_attrs}")
        logger.info(f"  Total associations: {total_assocs}")
        logger.info("")
        logger.info("Products by type:")
        for ptype, count in sorted(by_type.items(), key=lambda x: -x[1]):
            logger.info(f"  {ptype}: {count}")
        logger.info("=" * 70)

    def run(self):
        """Execute complete ingestion pipeline"""
        start_time = datetime.now()

        logger.info("")
        logger.info("=" * 70)
        logger.info("P360 SYNDICATION INGESTION")
        logger.info("=" * 70)
        logger.info(f"  Customer:    {self.customer_id}")
        logger.info(f"  Source XML:  {self.p360_xml_path.name}")
        logger.info(f"  Lakehouse:   {self.lakehouse_path}")
        logger.info(f"  Table:       syndication_products")
        logger.info("=" * 70)
        logger.info("")

        # Step 1: Parse XML
        products = self.parse_p360_xml()

        if not products:
            logger.error("No products parsed!")
            return

        # Step 2: Create Delta table
        self.create_delta_table(products)

        # Step 3: Print stats
        self.print_statistics(products)

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"✓ Ingestion complete in {elapsed:.1f} seconds")
        logger.info(f"✓ Table path: {self.table_path}")
        logger.info("")


def main():
    """Main entry point"""
    try:
        ingester = P360SyndicationIngester(customer_id="eaton")
        ingester.run()
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
