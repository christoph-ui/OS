"""
Multi-Table Delta Loader

Creates and updates multiple standard Delta tables from extracted data.
Handles products, syndication_products, and data_quality_audit tables.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import json

import pandas as pd
import pyarrow as pa
from deltalake import DeltaTable, write_deltalake

from lakehouse.schemas.standard import (
    ProductRecord,
    SyndicationProductRecord,
    DataQualityAuditRecord,
)

logger = logging.getLogger(__name__)


class MultiTableLoader:
    """
    Creates and updates multiple standard Delta tables.

    Manages structured tables (products, syndication_products, data_quality_audit)
    alongside the existing general_documents and general_chunks tables.
    """

    def __init__(self, lakehouse_path: Path):
        """
        Initialize multi-table loader.

        Args:
            lakehouse_path: Path to lakehouse storage (e.g., /data/lakehouse)
        """
        self.lakehouse_path = Path(lakehouse_path)
        self.delta_path = self.lakehouse_path / "delta"
        self.delta_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"MultiTableLoader initialized with lakehouse: {self.lakehouse_path}")

    async def upsert_products(self, records: List[Dict[str, Any]]):
        """
        Create or update products table with structured records.

        Args:
            records: List of product records (dicts from Claude extraction)
        """
        if not records:
            logger.debug("No product records to upsert")
            return

        table_path = self.delta_path / "products"

        try:
            # Validate records using Pydantic
            validated_records = []
            for i, record in enumerate(records):
                try:
                    # Create Pydantic model instance for validation
                    product = ProductRecord(**record)
                    # Convert back to dict for PyArrow
                    validated_records.append(product.model_dump())
                except Exception as e:
                    logger.warning(f"Invalid product record {i}: {e}")
                    logger.debug(f"Record was: {record}")
                    continue

            if not validated_records:
                logger.warning("No valid product records after validation")
                return

            # Convert to DataFrame
            df = pd.DataFrame(validated_records)

            # Convert Decimal columns to float for PyArrow compatibility
            if 'price' in df.columns:
                df['price'] = df['price'].astype(float)

            # Convert datetime columns to strings for Delta Lake
            if 'ingested_at' in df.columns:
                df['ingested_at'] = df['ingested_at'].apply(
                    lambda x: x.isoformat() if hasattr(x, 'isoformat') else str(x)
                )

            # Convert metadata dict to JSON string for Delta Lake
            if 'metadata' in df.columns:
                df['metadata'] = df['metadata'].apply(json.dumps)

            # Create PyArrow table
            table = pa.Table.from_pandas(df)

            # Write to Delta Lake
            write_deltalake(
                str(table_path),
                table,
                mode="append",
                schema_mode="merge"  # Auto-add new columns if schema evolves
            )

            logger.info(f"✅ Upserted {len(validated_records)} records to products table")

        except Exception as e:
            logger.error(f"Failed to upsert products: {e}", exc_info=True)
            raise

    async def upsert_syndication_products(self, records: List[Dict[str, Any]]):
        """
        Create or update syndication_products table.

        Args:
            records: List of syndication product records
        """
        if not records:
            logger.debug("No syndication product records to upsert")
            return

        table_path = self.delta_path / "syndication_products"

        try:
            # Validate records
            validated_records = []
            for i, record in enumerate(records):
                try:
                    product = SyndicationProductRecord(**record)
                    validated_records.append(product.model_dump())
                except Exception as e:
                    logger.warning(f"Invalid syndication product record {i}: {e}")
                    continue

            if not validated_records:
                logger.warning("No valid syndication product records after validation")
                return

            # Convert to DataFrame
            df = pd.DataFrame(validated_records)

            # Convert Decimal to float
            if 'price' in df.columns:
                df['price'] = df['price'].astype(float)

            # Convert datetime columns
            if 'last_updated' in df.columns:
                df['last_updated'] = df['last_updated'].apply(
                    lambda x: x.isoformat() if hasattr(x, 'isoformat') else str(x)
                )

            # Convert nested JSON fields to strings
            json_columns = ['images', 'cad_files', 'technical_specs', 'compliance_data']
            for col in json_columns:
                if col in df.columns:
                    df[col] = df[col].apply(json.dumps)

            # Create PyArrow table
            table = pa.Table.from_pandas(df)

            # Write to Delta Lake
            write_deltalake(
                str(table_path),
                table,
                mode="append",
                schema_mode="merge"
            )

            logger.info(f"✅ Upserted {len(validated_records)} records to syndication_products table")

        except Exception as e:
            logger.error(f"Failed to upsert syndication_products: {e}", exc_info=True)
            raise

    async def upsert_data_quality(self, records: List[Dict[str, Any]]):
        """
        Create or update data_quality_audit table.

        Args:
            records: List of data quality audit records
        """
        if not records:
            logger.debug("No data quality records to upsert")
            return

        table_path = self.delta_path / "data_quality_audit"

        try:
            # Validate records
            validated_records = []
            for i, record in enumerate(records):
                try:
                    quality = DataQualityAuditRecord(**record)
                    validated_records.append(quality.model_dump())
                except Exception as e:
                    logger.warning(f"Invalid data quality record {i}: {e}")
                    continue

            if not validated_records:
                logger.warning("No valid data quality records after validation")
                return

            # Convert to DataFrame
            df = pd.DataFrame(validated_records)

            # Convert datetime columns
            datetime_cols = ['created_at', 'verified_at']
            for col in datetime_cols:
                if col in df.columns:
                    df[col] = df[col].apply(
                        lambda x: x.isoformat() if x and hasattr(x, 'isoformat') else None
                    )

            # Convert nested JSON fields
            json_columns = ['data_sources', 'confidence_levels', 'extraction_notes', 'validation_errors']
            for col in json_columns:
                if col in df.columns:
                    df[col] = df[col].apply(json.dumps)

            # Create PyArrow table
            table = pa.Table.from_pandas(df)

            # Write to Delta Lake
            write_deltalake(
                str(table_path),
                table,
                mode="append",
                schema_mode="merge"
            )

            logger.info(f"✅ Upserted {len(validated_records)} records to data_quality_audit table")

        except Exception as e:
            logger.error(f"Failed to upsert data_quality: {e}", exc_info=True)
            raise

    async def load_all(self, extracted_data: Dict[str, List[Dict[str, Any]]]):
        """
        Load all extracted data to appropriate tables.

        Args:
            extracted_data: Dict with keys: products, syndication_products, data_quality

        Example:
            extracted_data = {
                "products": [{gtin, brand, price, ...}],
                "syndication_products": [{...}],
                "data_quality": [{...}]
            }
        """
        if not extracted_data:
            logger.debug("No extracted data to load")
            return

        # Load products
        if "products" in extracted_data:
            await self.upsert_products(extracted_data["products"])

        # Load syndication products
        if "syndication_products" in extracted_data:
            await self.upsert_syndication_products(extracted_data["syndication_products"])

        # Load data quality
        if "data_quality" in extracted_data:
            await self.upsert_data_quality(extracted_data["data_quality"])

        logger.info("✅ All extracted data loaded to lakehouse")

    def get_table_stats(self) -> Dict[str, Any]:
        """
        Get statistics about created tables.

        Returns:
            Dict with table names and row counts
        """
        stats = {}

        for table_name in ["products", "syndication_products", "data_quality_audit"]:
            table_path = self.delta_path / table_name

            if table_path.exists():
                try:
                    dt = DeltaTable(str(table_path))
                    df = dt.to_pandas()
                    stats[table_name] = {
                        "exists": True,
                        "row_count": len(df),
                        "version": dt.version()
                    }
                except Exception as e:
                    stats[table_name] = {
                        "exists": True,
                        "error": str(e)
                    }
            else:
                stats[table_name] = {
                    "exists": False
                }

        return stats
