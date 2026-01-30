#!/usr/bin/env python3
"""
Test BMEcat Generation

Tests the SYNDICATE MCP's BMEcat generator by:
1. Querying syndication_products table for sample products
2. Calling SYNDICATE MCP to generate BMEcat XML
3. Validating XML structure and content
4. Saving output to file for manual inspection

Expected result: Valid BMEcat 2005.1 XML with ECLASS/ETIM classifications

Created: 2026-01-12
Author: Claude Code
"""

import sys
import logging
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BMEcatTester:
    """
    Tests BMEcat generation from P360 syndication data.
    """

    def __init__(self):
        self.customer_id = "eaton"
        self.lakehouse_url = "http://localhost:9302"
        self.console_api_url = "http://localhost:4010"
        self.output_file = Path("/tmp/eaton_bmecat_test.xml")

    async def get_sample_products(self, limit: int = 5) -> list:
        """
        Query syndication_products table for sample products.

        Args:
            limit: Number of products to retrieve

        Returns:
            List of product dictionaries
        """
        logger.info(f"Querying syndication_products table for {limit} UPS products...")

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Query for UPS products (good test case with ETIM classifications)
            response = await client.get(
                f"{self.lakehouse_url}/delta/query/syndication_products",
                params={"limit": limit}
            )
            response.raise_for_status()
            data = response.json()

        products = data.get("rows", [])
        logger.info(f"✓ Retrieved {len(products)} products")

        # Log product IDs
        for p in products:
            logger.info(f"  - {p['product_id']}: {p['product_name']} (ETIM: {p['etim_class']})")

        return products

    async def generate_bmecat(self, product_ids: list, language: str = "en") -> dict:
        """
        Call SYNDICATE MCP to generate BMEcat XML.

        Args:
            product_ids: List of product SKUs
            language: Output language (en, de)

        Returns:
            Response from SYNDICATE MCP with XML content
        """
        logger.info(f"Generating BMEcat XML for {len(product_ids)} products (language: {language})...")

        # Build request payload
        payload = {
            "format": "bmecat",
            "product_ids": product_ids,
            "language": language
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{self.console_api_url}/api/syndicate/generate",
                    json=payload,
                    params={"customer_id": self.customer_id}
                )
                response.raise_for_status()
                result = response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error: {e.response.status_code}")
                logger.error(f"Response: {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Request failed: {e}")
                raise

        logger.info(f"✓ BMEcat generation complete")
        return result

    def validate_bmecat_xml(self, xml_content: str) -> dict:
        """
        Validate BMEcat XML structure.

        Checks:
        - Well-formed XML
        - BMEcat 2005.1 root element
        - Header present
        - ARTICLE elements present
        - ECLASS/ETIM feature systems
        - Required fields populated

        Returns:
            Validation report dictionary
        """
        logger.info("Validating BMEcat XML structure...")

        report = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "stats": {}
        }

        try:
            # Parse XML
            root = ET.fromstring(xml_content)
            report["stats"]["root_tag"] = root.tag

            # Check root element
            if "BMECAT" not in root.tag:
                report["errors"].append("Root element is not BMECAT")
                report["valid"] = False
            else:
                logger.info("✓ Valid BMECAT root element")

            # Check version
            version = root.get("version")
            if version:
                report["stats"]["version"] = version
                if "2005" in version:
                    logger.info(f"✓ BMEcat version: {version}")
                else:
                    report["warnings"].append(f"Unexpected version: {version}")
            else:
                report["warnings"].append("No version attribute found")

            # Find HEADER
            header = root.find(".//{http://www.bmecat.org/bmecat/2005}HEADER") or root.find(".//HEADER")
            if header is not None:
                logger.info("✓ HEADER element present")

                # Check catalog info
                catalog = header.find(".//{http://www.bmecat.org/bmecat/2005}CATALOG") or header.find(".//CATALOG")
                if catalog is not None:
                    catalog_id = catalog.find(".//{http://www.bmecat.org/bmecat/2005}CATALOG_ID") or catalog.find(".//CATALOG_ID")
                    if catalog_id is not None and catalog_id.text:
                        logger.info(f"  Catalog ID: {catalog_id.text}")
                        report["stats"]["catalog_id"] = catalog_id.text
            else:
                report["errors"].append("Missing HEADER element")
                report["valid"] = False

            # Find T_NEW_CATALOG
            catalog_section = root.find(".//{http://www.bmecat.org/bmecat/2005}T_NEW_CATALOG") or root.find(".//T_NEW_CATALOG")
            if catalog_section is not None:
                logger.info("✓ T_NEW_CATALOG section present")

                # Check FEATURE_SYSTEM declarations
                feature_systems = catalog_section.findall(".//{http://www.bmecat.org/bmecat/2005}FEATURE_SYSTEM") or catalog_section.findall(".//FEATURE_SYSTEM")
                if feature_systems:
                    systems = []
                    for fs in feature_systems:
                        fs_name = fs.find(".//{http://www.bmecat.org/bmecat/2005}FEATURE_SYSTEM_NAME") or fs.find(".//FEATURE_SYSTEM_NAME")
                        if fs_name is not None and fs_name.text:
                            systems.append(fs_name.text)

                    report["stats"]["feature_systems"] = systems
                    logger.info(f"✓ Feature systems declared: {', '.join(systems)}")

                    if "ECLASS" not in str(systems) and "ETIM" not in str(systems):
                        report["warnings"].append("No ECLASS or ETIM feature system found")
                else:
                    report["warnings"].append("No FEATURE_SYSTEM elements found")

                # Count ARTICLE elements
                articles = catalog_section.findall(".//{http://www.bmecat.org/bmecat/2005}ARTICLE") or catalog_section.findall(".//ARTICLE")
                article_count = len(articles)
                report["stats"]["article_count"] = article_count

                if article_count > 0:
                    logger.info(f"✓ Found {article_count} ARTICLE elements")

                    # Validate first article structure
                    first_article = articles[0]

                    # Check SUPPLIER_AID (SKU)
                    supplier_aid = first_article.find(".//{http://www.bmecat.org/bmecat/2005}SUPPLIER_AID") or first_article.find(".//SUPPLIER_AID")
                    if supplier_aid is not None and supplier_aid.text:
                        logger.info(f"  First product SKU: {supplier_aid.text}")
                        report["stats"]["sample_sku"] = supplier_aid.text
                    else:
                        report["warnings"].append("First ARTICLE missing SUPPLIER_AID")

                    # Check ARTICLE_DETAILS
                    details = first_article.find(".//{http://www.bmecat.org/bmecat/2005}ARTICLE_DETAILS") or first_article.find(".//ARTICLE_DETAILS")
                    if details is not None:
                        desc_short = details.find(".//{http://www.bmecat.org/bmecat/2005}DESCRIPTION_SHORT") or details.find(".//DESCRIPTION_SHORT")
                        if desc_short is not None and desc_short.text:
                            logger.info(f"  Description: {desc_short.text[:60]}...")

                        ean = details.find(".//{http://www.bmecat.org/bmecat/2005}EAN") or details.find(".//EAN")
                        if ean is not None and ean.text:
                            logger.info(f"  EAN: {ean.text}")
                    else:
                        report["warnings"].append("First ARTICLE missing ARTICLE_DETAILS")

                    # Check ARTICLE_FEATURES
                    features_sections = first_article.findall(".//{http://www.bmecat.org/bmecat/2005}ARTICLE_FEATURES") or first_article.findall(".//ARTICLE_FEATURES")
                    if features_sections:
                        logger.info(f"  Feature groups: {len(features_sections)}")
                        for feat_section in features_sections:
                            ref_sys = feat_section.find(".//{http://www.bmecat.org/bmecat/2005}REFERENCE_FEATURE_SYSTEM_NAME") or feat_section.find(".//REFERENCE_FEATURE_SYSTEM_NAME")
                            if ref_sys is not None and ref_sys.text:
                                logger.info(f"    - {ref_sys.text}")
                    else:
                        report["warnings"].append("First ARTICLE has no ARTICLE_FEATURES")

                    # Check MIME_INFO (images/documents)
                    mime_info = first_article.find(".//{http://www.bmecat.org/bmecat/2005}MIME_INFO") or first_article.find(".//MIME_INFO")
                    if mime_info is not None:
                        mime_elements = mime_info.findall(".//{http://www.bmecat.org/bmecat/2005}MIME") or mime_info.findall(".//MIME")
                        if mime_elements:
                            logger.info(f"  Media files: {len(mime_elements)}")
                        else:
                            report["warnings"].append("MIME_INFO present but empty")
                    else:
                        report["warnings"].append("First ARTICLE missing MIME_INFO")

                else:
                    report["errors"].append("No ARTICLE elements found")
                    report["valid"] = False
            else:
                report["errors"].append("Missing T_NEW_CATALOG section")
                report["valid"] = False

        except ET.ParseError as e:
            report["errors"].append(f"XML parsing error: {e}")
            report["valid"] = False
            logger.error(f"✗ XML parsing failed: {e}")
        except Exception as e:
            report["errors"].append(f"Validation error: {e}")
            report["valid"] = False
            logger.error(f"✗ Validation failed: {e}")

        # Summary
        if report["valid"]:
            logger.info("✓ BMEcat XML validation passed")
        else:
            logger.error(f"✗ BMEcat XML validation failed: {len(report['errors'])} errors")

        if report["warnings"]:
            logger.warning(f"⚠ {len(report['warnings'])} warnings")

        return report

    def save_xml(self, xml_content: str):
        """Save XML to file for inspection"""
        self.output_file.write_text(xml_content)
        logger.info(f"✓ Saved BMEcat XML to: {self.output_file}")

        # Print excerpt
        lines = xml_content.split('\n')
        logger.info(f"\nFirst 50 lines of generated XML:")
        logger.info("-" * 70)
        for i, line in enumerate(lines[:50], 1):
            print(f"{i:3d} | {line}")
        logger.info("-" * 70)
        logger.info(f"Total lines: {len(lines)}")
        logger.info(f"Total size: {len(xml_content)/1024:.1f} KB")

    async def run(self):
        """Execute complete test"""
        start_time = datetime.now()

        logger.info("")
        logger.info("=" * 70)
        logger.info("BMECAT GENERATION TEST")
        logger.info("=" * 70)
        logger.info(f"  Customer:     {self.customer_id}")
        logger.info(f"  Lakehouse:    {self.lakehouse_url}")
        logger.info(f"  Console API:  {self.console_api_url}")
        logger.info(f"  Output file:  {self.output_file}")
        logger.info("=" * 70)
        logger.info("")

        try:
            # Step 1: Get sample products
            products = await self.get_sample_products(limit=5)
            if not products:
                logger.error("No products found!")
                return

            product_ids = [p["product_id"] for p in products]

            # Step 2: Generate BMEcat
            logger.info("")
            result = await self.generate_bmecat(product_ids, language="en")

            # Check if generation succeeded
            if not result.get("success"):
                logger.error(f"BMEcat generation failed: {result}")
                return

            xml_content = result.get("output", "")
            if not xml_content:
                logger.error("No XML content returned")
                logger.error(f"Result: {json.dumps(result, indent=2)}")
                return

            # Step 3: Save XML
            logger.info("")
            self.save_xml(xml_content)

            # Step 4: Validate
            logger.info("")
            validation = self.validate_bmecat_xml(xml_content)

            # Print report
            logger.info("")
            logger.info("=" * 70)
            logger.info("VALIDATION REPORT")
            logger.info("=" * 70)
            logger.info(f"  Valid: {validation['valid']}")
            logger.info(f"  Errors: {len(validation['errors'])}")
            logger.info(f"  Warnings: {len(validation['warnings'])}")
            logger.info("")
            logger.info("Statistics:")
            for key, value in validation["stats"].items():
                logger.info(f"  {key}: {value}")
            logger.info("")

            if validation["errors"]:
                logger.info("Errors:")
                for err in validation["errors"]:
                    logger.info(f"  - {err}")
                logger.info("")

            if validation["warnings"]:
                logger.info("Warnings:")
                for warn in validation["warnings"]:
                    logger.info(f"  - {warn}")
                logger.info("")

            logger.info("=" * 70)

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"✓ Test complete in {elapsed:.1f} seconds")

            if validation["valid"]:
                logger.info("✅ BMEcat generation test PASSED")
            else:
                logger.info("❌ BMEcat generation test FAILED")

        except Exception as e:
            logger.error(f"Test failed: {e}", exc_info=True)
            raise


async def main():
    """Main entry point"""
    tester = BMEcatTester()
    await tester.run()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
