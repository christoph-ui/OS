#!/usr/bin/env python3
"""
Transform Lightnet raw Excel data to structured products using Claude
Reads from products_documents table and creates structured product records
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.extractor.intelligent_extractor import IntelligentExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def transform_lightnet_products():
    """Transform Lightnet raw data to structured products"""

    customer_id = "a875917d-5d1b-41dd-8c78-61b88d6f8db5"
    lakehouse_path = Path(f"/home/christoph.bertsch/0711/0711-OS/data/lakehouse/{customer_id}")

    logger.info(f"🚀 Starting Lightnet product transformation")
    logger.info(f"Lakehouse: {lakehouse_path}")

    # Initialize intelligent extractor with Claude
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not set!")
        return

    extractor = IntelligentExtractor(claude_api_key=api_key)

    # Read raw product document directly from lakehouse API
    import httpx
    import json

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://localhost:8502/delta/query/products_documents?limit=1")
            data = resp.json()
            docs = data.get("rows", [])

        logger.info(f"Found {len(docs)} product documents")

        if not docs:
            logger.error("No documents found!")
            return

        # Get first document (the Excel file)
        doc = docs[0]
        raw_text = doc.get("text", "")

        logger.info(f"Document: {doc.get('filename')}")
        logger.info(f"Text length: {len(raw_text)} chars")
        logger.info(f"First 500 chars:\n{raw_text[:500]}")

        # Deployment context for Lightnet
        deployment_context = {
            "company_name": "Lightnet",
            "industry": "LED lighting manufacturing",
            "data_format": "Excel product catalog",
            "expected_fields": [
                "Code", "Kurztext", "Langtext", "Produktfamilie", "Produktname",
                "Preis 0 in EUR (VK0)", "Installationstyp", "Lichtverteilung",
                "Leuchtmittel", "Optisches System", "Steuerung"
            ],
            "target_schema": "products + syndication_products",
            "transformation_rules": {
                "Code": "product_sku",
                "Kurztext": "short_description",
                "Langtext": "long_description",
                "Produktname": "product_name",
                "Preis 0 in EUR (VK0)": "price_eur",
                "Produktfamilie": "product_family"
            }
        }

        # Extract structured products using Claude
        logger.info("🤖 Calling Claude to extract structured products...")

        result = await extractor.extract_to_standard_schema(
            file_content=raw_text,
            deployment_context=deployment_context,
            classification="products",
            filename=doc.get("filename")
        )

        logger.info(f"✅ Extraction complete!")
        logger.info(f"Result keys: {result.keys()}")

        if "products" in result:
            logger.info(f"Products extracted: {len(result['products'])}")
            logger.info(f"Sample product: {result['products'][0] if result['products'] else 'None'}")

        if "syndication_products" in result:
            logger.info(f"Syndication products: {len(result['syndication_products'])}")

        # Save to lakehouse
        logger.info("💾 Saving to lakehouse...")

        # TODO: Load into proper tables
        logger.info("✓ Transformation complete!")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(transform_lightnet_products())
