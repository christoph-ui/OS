"""
BMEcat XML Parser

Parses BMEcat 2005 format product catalogs into structured product entities.
Extracts ETIM classifications, specifications, and product details.

Standard: BMEcat 2005 (German e-business standard)
Used by: Eaton, many European electrical/industrial suppliers
"""

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class BMEcatProduct:
    """Structured product from BMEcat catalog"""
    supplier_pid: str  # Catalog number (primary key)
    manufacturer_pid: str  # Manufacturer part number
    manufacturer_name: str
    product_name: str
    short_description: str
    long_description: str

    # ETIM/ECLASS Classification
    etim_class: Optional[str] = None
    eclass_code: Optional[str] = None
    reference_feature_group_id: Optional[str] = None

    # Technical Specifications
    specifications: Dict = None

    # Product Details
    ean_upc: Optional[str] = None
    manufacturer_type_descr: Optional[str] = None
    keyword: Optional[str] = None

    # Pricing (if available)
    price: Optional[float] = None
    currency: Optional[str] = None

    # Logistics
    delivery_time: Optional[int] = None
    min_order: Optional[int] = None
    country_of_origin: Optional[str] = None

    # Media references
    mime_sources: List[str] = None

    def __post_init__(self):
        if self.specifications is None:
            self.specifications = {}
        if self.mime_sources is None:
            self.mime_sources = []


class BMEcatParser:
    """
    Parse BMEcat 2005 XML catalogs.

    Handles:
    - Product extraction
    - ETIM/ECLASS classification
    - Technical features
    - Media references
    """

    def __init__(self):
        self.namespace = {
            'bme': 'https://www.etim-international.com/bmecat/50'
        }
        self.ns_prefix = '{https://www.etim-international.com/bmecat/50}'

    def parse_file(self, xml_path: Path) -> List[BMEcatProduct]:
        """
        Parse BMEcat XML file.

        Args:
            xml_path: Path to BMEcat XML file

        Returns:
            List of BMEcatProduct objects
        """
        logger.info(f"Parsing BMEcat file: {xml_path}")

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            products = []

            # Find all PRODUCT elements in T_NEW_CATALOG section
            # Handle namespace properly
            for product_elem in root.iter():
                tag = product_elem.tag
                # Remove namespace prefix for comparison
                local_tag = tag.split('}')[-1] if '}' in tag else tag

                if local_tag == 'PRODUCT':
                    product = self._parse_product(product_elem)
                    if product:
                        products.append(product)

            logger.info(f"Extracted {len(products)} products from {xml_path.name}")
            return products

        except Exception as e:
            logger.error(f"Failed to parse BMEcat: {e}")
            return []

    def _parse_product(self, product_elem: ET.Element) -> Optional[BMEcatProduct]:
        """Parse single PRODUCT element"""
        try:
            # Extract basic IDs
            supplier_pid = self._get_text(product_elem, 'SUPPLIER_PID')
            if not supplier_pid:
                return None

            # Product details (with namespace)
            details = product_elem.find(self.ns_prefix + 'PRODUCT_DETAILS')

            # Extract fields from PRODUCT_DETAILS
            manufacturer_pid = self._get_text(details, 'MANUFACTURER_PID') if details is not None else None
            manufacturer_name = self._get_text(details, 'MANUFACTURER_NAME') if details is not None else None
            manufacturer_type_descr = self._get_text(details, 'MANUFACTURER_TYPE_DESCR') if details is not None else None
            ean = self._get_text(details, 'INTERNATIONAL_PID') if details is not None else None
            keyword = self._get_text(details, 'KEYWORD') if details is not None else None
            short_desc = self._get_text(details, 'DESCRIPTION_SHORT') if details is not None else None
            long_desc = self._get_text(details, 'DESCRIPTION_LONG') if details is not None else None

            # ETIM/ECLASS classification from PRODUCT_FEATURES
            etim_class = None
            eclass_code = None

            # Find all PRODUCT_FEATURES elements
            for features_elem in product_elem.findall('.//' + self.ns_prefix + 'PRODUCT_FEATURES'):
                feature_system = self._get_text(features_elem, 'REFERENCE_FEATURE_SYSTEM_NAME')
                ref_group = self._get_text(features_elem, 'REFERENCE_FEATURE_GROUP_ID')

                if feature_system and ref_group:
                    if 'ETIM' in feature_system:
                        etim_class = ref_group
                    elif 'ECLASS' in feature_system:
                        eclass_code = ref_group

            # Fallback: try at product level
            if not etim_class and not eclass_code:
                ref_feature_group = self._get_text(product_elem, 'REFERENCE_FEATURE_GROUP_ID')
                feature_system = self._get_text(product_elem, 'REFERENCE_FEATURE_SYSTEM_NAME')
                if feature_system and 'ECLASS' in feature_system:
                    eclass_code = ref_feature_group
                elif feature_system and 'ETIM' in feature_system:
                    etim_class = ref_feature_group
            else:
                ref_feature_group = etim_class or eclass_code

            # Extract technical specifications (FEATURE elements)
            specifications = self._parse_features(product_elem)

            # Media sources
            mime_sources = self._parse_mime_sources(product_elem)

            # Pricing
            price_elem = product_elem.find('.//PRODUCT_PRICE')
            price = None
            currency = None
            if price_elem is not None:
                price_text = price_elem.get('price_amount') or price_elem.text
                if price_text:
                    try:
                        price = float(price_text)
                    except:
                        pass
                currency = price_elem.get('price_currency')

            # Logistics
            order_details = product_elem.find('.//PRODUCT_ORDER_DETAILS')
            delivery_time = self._get_int(order_details, 'DELIVERY_TIME')
            min_order = self._get_int(order_details, 'ORDER_UNIT')

            logistics = product_elem.find('.//PRODUCT_LOGISTIC_DETAILS')
            country = self._get_text(logistics, 'COUNTRY_OF_ORIGIN')

            # Build product name (fallback logic)
            product_name = (
                short_desc or
                manufacturer_type_descr or
                f"Product {supplier_pid}"
            )

            return BMEcatProduct(
                supplier_pid=supplier_pid,
                manufacturer_pid=manufacturer_pid or supplier_pid,
                manufacturer_name=manufacturer_name or "Eaton",
                product_name=product_name,
                short_description=short_desc or "",
                long_description=long_desc or "",
                etim_class=etim_class,
                eclass_code=eclass_code or ref_feature_group,
                reference_feature_group_id=ref_feature_group,
                specifications=specifications,
                ean_upc=ean,
                manufacturer_type_descr=manufacturer_type_descr,
                keyword=keyword,
                price=price,
                currency=currency,
                delivery_time=delivery_time,
                min_order=min_order,
                country_of_origin=country,
                mime_sources=mime_sources
            )

        except Exception as e:
            logger.error(f"Failed to parse product: {e}")
            return None

    def _parse_features(self, product_elem: ET.Element) -> Dict[str, str]:
        """Parse FEATURE elements into specifications dict"""
        specs = {}

        for feature in product_elem.iter():
            if not feature.tag.endswith('FEATURE'):
                continue

            fname = self._get_text(feature, 'FNAME')
            fvalue = self._get_text(feature, 'FVALUE')

            if fname and fvalue:
                specs[fname] = fvalue

        return specs

    def _parse_mime_sources(self, product_elem: ET.Element) -> List[str]:
        """Extract MIME_SOURCE (image filenames)"""
        sources = []

        for mime in product_elem.iter():
            if mime.tag.endswith('MIME_SOURCE'):
                source = mime.text
                if source:
                    sources.append(source.strip())

        return sources

    def _get_text(self, element: Optional[ET.Element], tag: str) -> Optional[str]:
        """Safely get text from XML element (handles namespace)"""
        if element is None:
            return None

        # Try with namespace
        ns_tag = f"{self.ns_prefix}{tag}"
        child = element.find(f".//{ns_tag}") or element.find(ns_tag)

        # Try without namespace as fallback
        if child is None:
            child = element.find(f".//{tag}") or element.find(tag)

        if child is not None and child.text:
            return child.text.strip()

        return None

    def _get_int(self, element: Optional[ET.Element], tag: str) -> Optional[int]:
        """Safely get integer from XML element"""
        text = self._get_text(element, tag)
        if text:
            try:
                return int(text)
            except:
                pass
        return None

    def export_to_delta(self, products: List[BMEcatProduct], output_path: Path):
        """
        Export products to Delta Lake table.

        Args:
            products: List of products
            output_path: Path to Delta table
        """
        import pyarrow as pa
        from deltalake import write_deltalake

        # Convert to records
        records = []
        for product in products:
            record = asdict(product)
            # Convert specs dict to JSON string
            import json
            record['specifications'] = json.dumps(record['specifications'])
            record['mime_sources'] = json.dumps(record['mime_sources'])
            records.append(record)

        # Create schema
        schema = pa.schema([
            ('supplier_pid', pa.string()),
            ('manufacturer_pid', pa.string()),
            ('manufacturer_name', pa.string()),
            ('product_name', pa.string()),
            ('short_description', pa.string()),
            ('long_description', pa.string()),
            ('etim_class', pa.string()),
            ('eclass_code', pa.string()),
            ('reference_feature_group_id', pa.string()),
            ('specifications', pa.string()),  # JSON
            ('ean_upc', pa.string()),
            ('manufacturer_type_descr', pa.string()),
            ('keyword', pa.string()),
            ('price', pa.float64()),
            ('currency', pa.string()),
            ('delivery_time', pa.int32()),
            ('min_order', pa.int32()),
            ('country_of_origin', pa.string()),
            ('mime_sources', pa.string()),  # JSON
        ])

        # Create table
        table = pa.Table.from_pylist(records, schema=schema)

        # Write to Delta
        write_deltalake(
            str(output_path),
            table,
            mode="overwrite",
            schema_mode="overwrite"
        )

        logger.info(f"Exported {len(products)} products to {output_path}")


# CLI entry point
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python bmecat_parser.py <path_to_bmecat.xml> [output_delta_path]")
        sys.exit(1)

    xml_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("products_delta")

    parser = BMEcatParser()
    products = parser.parse_file(xml_path)

    print(f"\nExtracted {len(products)} products")
    print("\nFirst 5 products:")
    for p in products[:5]:
        print(f"  - {p.supplier_pid}: {p.product_name}")
        if p.etim_class:
            print(f"    ETIM: {p.etim_class}")
        if p.eclass_code:
            print(f"    ECLASS: {p.eclass_code}")

    if output_path:
        parser.export_to_delta(products, output_path)
        print(f"\n✓ Exported to {output_path}")
