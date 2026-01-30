#!/usr/bin/env python3
"""
Parse Lightnet Excel file directly and create structured products
Uses pandas to parse Excel, then saves to lakehouse
"""
import asyncio
import logging
import os
import sys
from pathlib import Path
import pandas as pd
import httpx
from minio import Minio
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def parse_lightnet_excel():
    """Parse Excel and create structured products"""

    customer_id = "a875917d-5d1b-41dd-8c78-61b88d6f8db5"
    bucket_name = f"customer-{customer_id}"
    filename = "20260126_123933_Lightnet_Articledata_Cat25_DE_20251216.xlsx"

    logger.info("📥 Downloading Excel file from MinIO...")

    # Download from MinIO
    minio_client = Minio(
        endpoint="localhost:4050",
        access_key="0711admin",
        secret_key="0711secret",
        secure=False
    )

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        minio_client.fget_object(bucket_name, filename, tmp.name)
        excel_path = tmp.name

    logger.info(f"✅ Downloaded to {excel_path}")

    # Parse Excel with pandas
    logger.info("📊 Parsing Excel file...")
    df = pd.read_excel(excel_path, sheet_name="DE")

    logger.info(f"✅ Parsed {len(df)} rows")
    logger.info(f"Columns: {list(df.columns[:10])}")

    # Create structured products
    products = []
    for idx, row in df.iterrows():
        product = {
            "sku": str(row.get("Code", "")),
            "short_description": str(row.get("Kurztext", "")),
            "long_description": str(row.get("Langtext", "")),
            "product_family": str(row.get("Produktfamilie", "")),
            "product_name": str(row.get("Produktname", "")),
            "price_eur": float(row.get("Preis 0 in EUR (VK0)", 0)) if pd.notna(row.get("Preis 0 in EUR (VK0)")) else None,
            "installation_type": str(row.get("Installationstyp", "")),
            "light_distribution": str(row.get("Lichtverteilung", "")),
            "light_source": str(row.get("Leuchtmittel", "")),
            "control": str(row.get("Steuerung", "")),
            "color_temp": str(row.get("CCT", "")),
            "protection_class": str(row.get("Schutzklasse", "")),
            "status": str(row.get("Status", ""))
        }
        products.append(product)

    logger.info(f"✅ Created {len(products)} structured products")
    logger.info(f"Sample: {products[0]}")

    # Save to lakehouse via API
    logger.info("💾 Saving to lakehouse...")

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Save as syndication_products
        response = await client.post(
            "http://localhost:8502/delta/insert/syndication_products",
            json={"records": products}
        )
        logger.info(f"Response: {response.status_code}")
        if response.status_code == 200:
            logger.info(f"✅ Saved {len(products)} products to syndication_products!")
        else:
            logger.error(f"Error: {response.text}")

    # Cleanup
    os.unlink(excel_path)
    logger.info("✓ Done!")


if __name__ == "__main__":
    asyncio.run(parse_lightnet_excel())
