#!/usr/bin/env python3
"""
Sync EATON Product Categories to Database

Queries EATON lakehouse, categorizes products, and populates
customer_data_categories table for console display.

MULTI-TENANT SAFE: Only updates EATON customer_id.
"""

import asyncio
import httpx
import logging
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# EATON customer ID (UUID from database)
EATON_CUSTOMER_ID = "00000000-0000-0000-0000-000000000002"
EATON_LAKEHOUSE_URL = "http://localhost:9302"

# Product categorization (same as products.py)
CATEGORY_KEYWORDS = {
    "ups": {
        "id": "ups_systems",
        "name": "UPS Systems",
        "icon": "⚡",
        "color": "#f59e0b",
        "keywords": ["ups", "uninterruptible power", "backup power", "5e", "5sc"]
    },
    "circuit_breaker": {
        "id": "circuit_breakers",
        "name": "Circuit Breakers",
        "icon": "🔌",
        "color": "#3b82f6",
        "keywords": ["circuit breaker", "mcb", "miniature", "faz", "breaker"]
    },
    "rcd": {
        "id": "residual_current",
        "name": "Residual Current Devices",
        "icon": "⚠️",
        "color": "#ef4444",
        "keywords": ["rcd", "rccb", "rcbo", "residual", "frcdm"]
    },
    "fuse": {
        "id": "fuses",
        "name": "Fuses",
        "icon": "🔥",
        "color": "#dc2626",
        "keywords": ["fuse", "fusetron", "limiter", "ann", "ktk"]
    },
    "contactor": {
        "id": "contactors",
        "name": "Contactors & Starters",
        "icon": "🔧",
        "color": "#8b5cf6",
        "keywords": ["contactor", "magnetic", "motor starter", "dilm"]
    },
    "drive": {
        "id": "drives",
        "name": "Variable Speed Drives",
        "icon": "⚙️",
        "color": "#06b6d4",
        "keywords": ["drive", "vfd", "frequency", "inverter", "de1"]
    },
    "switch": {
        "id": "switches",
        "name": "Switches & Controls",
        "icon": "🔘",
        "color": "#84cc16",
        "keywords": ["switch", "control", "emergency", "palm", "fak"]
    }
}


def categorize_product(product: dict) -> str:
    """Categorize product based on name and keywords."""
    product_name = (product.get("product_name", "") or "").lower()
    product_desc = (product.get("short_description", "") or "").lower()
    supplier_pid = (product.get("supplier_pid", "") or "").lower()

    search_text = f"{product_name} {product_desc} {supplier_pid}"

    for cat_key, cat_data in CATEGORY_KEYWORDS.items():
        for keyword in cat_data["keywords"]:
            if keyword.lower() in search_text:
                return cat_data["id"]

    return "other"


async def fetch_eaton_products() -> list:
    """Fetch products from EATON lakehouse."""
    logger.info(f"Fetching products from {EATON_LAKEHOUSE_URL}/products")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{EATON_LAKEHOUSE_URL}/products",
            params={"limit": 500}
        )
        response.raise_for_status()
        result = response.json()

    products = result.get("products", [])
    logger.info(f"Fetched {len(products)} products from EATON lakehouse")

    return products


def categorize_products(products: list) -> dict:
    """Categorize products and count per category."""
    categories = {}

    # Initialize categories
    for cat_key, cat_data in CATEGORY_KEYWORDS.items():
        categories[cat_data["id"]] = {
            **cat_data,
            "count": 0
        }

    # Add "other" category
    categories["other"] = {
        "id": "other",
        "name": "Other Products",
        "icon": "📦",
        "color": "#9ca3af",
        "count": 0
    }

    # Categorize each product
    for product in products:
        category_id = categorize_product(product)
        if category_id in categories:
            categories[category_id]["count"] += 1

    # Remove empty categories
    categories = {
        cat_id: cat_data
        for cat_id, cat_data in categories.items()
        if cat_data["count"] > 0
    }

    return categories


def sync_to_database(categories: dict, db_url: str):
    """Sync categories to customer_data_categories table."""
    logger.info(f"Syncing {len(categories)} categories to database")

    engine = create_engine(db_url)

    with Session(engine) as session:
        # Clear existing EATON categories
        delete_query = text("""
            DELETE FROM customer_data_categories
            WHERE customer_id = CAST(:customer_id AS uuid)
        """)

        session.execute(delete_query, {"customer_id": EATON_CUSTOMER_ID})
        logger.info("Cleared existing EATON categories")

        # Insert new categories
        insert_query = text("""
            INSERT INTO customer_data_categories (
                customer_id,
                category_key,
                category_name,
                description,
                icon,
                color,
                document_count,
                total_size_bytes,
                discovered_by,
                sort_order,
                is_active
            ) VALUES (
                CAST(:customer_id AS uuid),
                :category_key,
                :category_name,
                :description,
                :icon,
                :color,
                :document_count,
                0,
                'lakehouse-sync',
                :sort_order,
                true
            )
        """)

        # Sort categories by count descending
        sorted_cats = sorted(categories.items(), key=lambda x: x[1]["count"], reverse=True)

        for idx, (cat_id, cat_data) in enumerate(sorted_cats):
            session.execute(insert_query, {
                "customer_id": EATON_CUSTOMER_ID,
                "category_key": cat_id,
                "category_name": cat_data["name"],
                "description": f"{cat_data['count']} products in this category",
                "icon": cat_data["icon"],
                "color": cat_data["color"],
                "document_count": cat_data["count"],
                "sort_order": idx
            })

            logger.info(f"  Inserted: {cat_data['name']} ({cat_data['count']} products)")

        session.commit()
        logger.info("✓ Categories synced to database")


async def main():
    """Main execution."""
    import os
    from pathlib import Path

    logger.info("=" * 60)
    logger.info("EATON Product Categories Sync")
    logger.info("=" * 60)

    # Get database URL from environment
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        # Try loading from .env
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            from dotenv import load_dotenv
            load_dotenv(env_path)
            db_url = os.getenv("DATABASE_URL")

    if not db_url:
        logger.error("DATABASE_URL not found in environment")
        logger.error("Set it in .env or export DATABASE_URL=...")
        return

    try:
        # Step 1: Fetch products from lakehouse
        products = await fetch_eaton_products()

        if not products:
            logger.warning("No products found in EATON lakehouse")
            return

        # Step 2: Categorize products
        categories = categorize_products(products)

        logger.info("\nCategorization Results:")
        for cat_id, cat_data in sorted(categories.items(), key=lambda x: x[1]["count"], reverse=True):
            logger.info(f"  {cat_data['icon']} {cat_data['name']}: {cat_data['count']} products")

        # Step 3: Sync to database
        sync_to_database(categories, db_url)

        logger.info("\n" + "=" * 60)
        logger.info("✓ Sync Complete!")
        logger.info("=" * 60)
        logger.info("\nRefresh your console to see updated categories.")

    except Exception as e:
        logger.error(f"Sync failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
