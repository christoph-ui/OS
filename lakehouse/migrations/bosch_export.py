"""
Bosch Data Export Script

Exports data from original Bosch PostgreSQL database to intermediate formats:
- Products → Parquet files
- Embeddings → Numpy arrays
- Graph relationships → JSON
- ECLASS/ETIM classifications → Parquet

Source: Bosch PostgreSQL (localhost:5434, database: bosch_products)
Target: /home/christoph.bertsch/0711/0711-OS/lakehouse/clients/bosch/export/
"""

import os
import sys
import logging
import psycopg2
import numpy as np
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from psycopg2.extras import RealDictCursor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BoschDataExporter:
    """Exports Bosch data from PostgreSQL to portable formats"""

    def __init__(
        self,
        db_host: str = "localhost",
        db_port: int = 5434,
        db_name: str = "bosch_products",
        db_user: str = "bosch_user",
        db_password: str = "bosch_secure_2024",
        export_dir: str = None
    ):
        self.db_config = {
            'host': db_host,
            'port': db_port,
            'database': db_name,
            'user': db_user,
            'password': db_password
        }

        self.export_dir = Path(export_dir or "/home/christoph.bertsch/0711/0711-OS/lakehouse/clients/bosch/export")
        self.export_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Export directory: {self.export_dir}")

    def connect(self):
        """Create database connection"""
        try:
            conn = psycopg2.connect(**self.db_config)
            logger.info(f"✓ Connected to {self.db_config['database']}")
            return conn
        except Exception as e:
            logger.error(f"✗ Failed to connect: {e}")
            raise

    def export_products(self):
        """Export products table to Parquet"""
        logger.info("=" * 70)
        logger.info("EXPORTING PRODUCTS")
        logger.info("=" * 70)

        conn = self.connect()

        try:
            # Get total count
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM products")
                total_count = cur.fetchone()[0]
                logger.info(f"Total products: {total_count:,}")

            # Export in chunks to handle large dataset
            chunk_size = 5000
            chunks_exported = 0

            query = """
                SELECT
                    id,
                    supplier_pid,
                    gtin,
                    ean,
                    manufacturer_pid,
                    manufacturer_name,
                    manufacturer_type_descr,
                    description_short,
                    description_long,
                    product_status,
                    product_type,
                    delivery_time,
                    keyword,
                    waregroup,
                    product_group,
                    article_type,
                    price,
                    discontinued,
                    description_marketing,
                    created_at,
                    updated_at
                FROM products
                ORDER BY id
            """

            for chunk_df in pd.read_sql_query(query, conn, chunksize=chunk_size):
                chunk_file = self.export_dir / f"products_chunk_{chunks_exported:04d}.parquet"
                # Convert timestamps to compatible format for Spark
                for col in chunk_df.columns:
                    if pd.api.types.is_datetime64_any_dtype(chunk_df[col]):
                        chunk_df[col] = chunk_df[col].astype('datetime64[us]')  # Microsecond precision
                chunk_df.to_parquet(chunk_file, index=False, compression='snappy', engine='pyarrow')
                chunks_exported += 1
                logger.info(f"  Exported chunk {chunks_exported}: {len(chunk_df)} products → {chunk_file.name}")

            logger.info(f"✓ Products exported: {total_count:,} products in {chunks_exported} chunks")

            # Export metadata
            metadata = {
                'total_products': total_count,
                'chunks': chunks_exported,
                'chunk_size': chunk_size,
                'exported_at': datetime.now().isoformat(),
                'source_db': self.db_config['database']
            }

            with open(self.export_dir / "products_metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)

            return total_count

        finally:
            conn.close()

    def export_product_features(self):
        """Export product features to Parquet"""
        logger.info("=" * 70)
        logger.info("EXPORTING PRODUCT FEATURES")
        logger.info("=" * 70)

        conn = self.connect()

        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM product_features")
                total_count = cur.fetchone()[0]
                logger.info(f"Total features: {total_count:,}")

            query = """
                SELECT
                    id,
                    product_id,
                    fname,
                    fvalue,
                    fvalue_details,
                    funit
                FROM product_features
                ORDER BY product_id, id
            """

            chunk_size = 10000
            chunks_exported = 0

            for chunk_df in pd.read_sql_query(query, conn, chunksize=chunk_size):
                chunk_file = self.export_dir / f"features_chunk_{chunks_exported:04d}.parquet"
                chunk_df.to_parquet(chunk_file, index=False, compression='snappy')
                chunks_exported += 1
                logger.info(f"  Exported chunk {chunks_exported}: {len(chunk_df)} features")

            logger.info(f"✓ Features exported: {total_count:,} features in {chunks_exported} chunks")
            return total_count

        finally:
            conn.close()

    def export_embeddings(self):
        """Export product embeddings to numpy arrays"""
        logger.info("=" * 70)
        logger.info("EXPORTING EMBEDDINGS")
        logger.info("=" * 70)

        conn = self.connect()

        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM product_embeddings")
                total_count = cur.fetchone()[0]
                logger.info(f"Total embeddings: {total_count:,}")

            query = """
                SELECT
                    product_id,
                    embedding,
                    embedding_model
                FROM product_embeddings
                ORDER BY product_id
            """

            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)

                product_ids = []
                embeddings = []
                models = []

                for row in cur:
                    product_ids.append(row['product_id'])
                    # Embedding is stored as vector type, convert to list
                    emb = row['embedding']
                    if isinstance(emb, str):
                        # Parse string representation: "[0.1, 0.2, ...]"
                        emb = json.loads(emb.replace('[', '[').replace(']', ']'))
                    embeddings.append(emb)
                    models.append(row['embedding_model'])

                # Save as compressed numpy arrays
                embeddings_array = np.array(embeddings, dtype=np.float32)
                product_ids_array = np.array(product_ids, dtype=np.int32)

                np.savez_compressed(
                    self.export_dir / "embeddings.npz",
                    product_ids=product_ids_array,
                    embeddings=embeddings_array,
                    models=np.array(models)
                )

                logger.info(f"  Embedding shape: {embeddings_array.shape}")
                logger.info(f"  Dimension: {embeddings_array.shape[1]}D")
                logger.info(f"  Model: {models[0] if models else 'unknown'}")
                logger.info(f"✓ Embeddings exported: {total_count:,} vectors → embeddings.npz")

                # Save metadata
                metadata = {
                    'count': total_count,
                    'dimension': int(embeddings_array.shape[1]),
                    'model': models[0] if models else 'unknown',
                    'dtype': 'float32',
                    'format': 'numpy_compressed',
                    'exported_at': datetime.now().isoformat()
                }

                with open(self.export_dir / "embeddings_metadata.json", 'w') as f:
                    json.dump(metadata, f, indent=2)

                return total_count

        finally:
            conn.close()

    def export_graph_relationships(self):
        """Export product relationships (graph edges) to JSON"""
        logger.info("=" * 70)
        logger.info("EXPORTING GRAPH RELATIONSHIPS")
        logger.info("=" * 70)

        conn = self.connect()

        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM product_relationships")
                total_count = cur.fetchone()[0]
                logger.info(f"Total relationships: {total_count:,}")

            query = """
                SELECT
                    id,
                    source_product_id,
                    target_product_id,
                    relationship_type,
                    strength,
                    metadata
                FROM product_relationships
                ORDER BY source_product_id, target_product_id
            """

            df = pd.read_sql_query(query, conn)

            # Export as Parquet (more efficient than JSON for large data)
            relationships_file = self.export_dir / "relationships.parquet"
            df.to_parquet(relationships_file, index=False, compression='snappy')

            logger.info(f"✓ Relationships exported: {total_count:,} edges → relationships.parquet")

            # Also export relationship type summary
            if len(df) > 0:
                type_summary = df['relationship_type'].value_counts().to_dict()
                logger.info("  Relationship types:")
                for rel_type, count in type_summary.items():
                    logger.info(f"    - {rel_type}: {count}")

                metadata = {
                    'total_relationships': total_count,
                    'relationship_types': type_summary,
                    'exported_at': datetime.now().isoformat()
                }
            else:
                metadata = {
                    'total_relationships': 0,
                    'relationship_types': {},
                    'exported_at': datetime.now().isoformat()
                }

            with open(self.export_dir / "relationships_metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)

            return total_count

        finally:
            conn.close()

    def export_eclass_etim_classifications(self):
        """Export ECLASS and ETIM classifications"""
        logger.info("=" * 70)
        logger.info("EXPORTING ECLASS/ETIM CLASSIFICATIONS")
        logger.info("=" * 70)

        conn = self.connect()

        try:
            # ETIM classifications
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM etim_classification")
                etim_count = cur.fetchone()[0]
                logger.info(f"ETIM classifications: {etim_count:,}")

            if etim_count > 0:
                etim_df = pd.read_sql_query(
                    "SELECT * FROM etim_classification ORDER BY product_id",
                    conn
                )
                etim_df.to_parquet(
                    self.export_dir / "etim_classifications.parquet",
                    index=False,
                    compression='snappy'
                )
                logger.info(f"✓ ETIM exported: {etim_count:,} classifications")

            # ECLASS classifications
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM eclass_product_classifications")
                eclass_count = cur.fetchone()[0]
                logger.info(f"ECLASS classifications: {eclass_count:,}")

            if eclass_count > 0:
                eclass_df = pd.read_sql_query(
                    "SELECT * FROM eclass_product_classifications ORDER BY product_id",
                    conn
                )
                eclass_df.to_parquet(
                    self.export_dir / "eclass_classifications.parquet",
                    index=False,
                    compression='snappy'
                )
                logger.info(f"✓ ECLASS exported: {eclass_count:,} classifications")

            # ECLASS attributes
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM eclass_attributes")
                attr_count = cur.fetchone()[0]
                logger.info(f"ECLASS attributes: {attr_count:,}")

            if attr_count > 0:
                attr_df = pd.read_sql_query(
                    "SELECT * FROM eclass_attributes ORDER BY product_id, id",
                    conn
                )
                attr_df.to_parquet(
                    self.export_dir / "eclass_attributes.parquet",
                    index=False,
                    compression='snappy'
                )
                logger.info(f"✓ ECLASS attributes exported: {attr_count:,}")

            return etim_count, eclass_count, attr_count

        finally:
            conn.close()

    def export_all(self):
        """Export all Bosch data"""
        logger.info("=" * 70)
        logger.info("BOSCH DATA EXPORT - STARTING")
        logger.info("=" * 70)
        logger.info(f"Source: {self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}")
        logger.info(f"Target: {self.export_dir}")
        logger.info("")

        start_time = datetime.now()

        try:
            # Export all data
            products_count = self.export_products()
            features_count = self.export_product_features()
            embeddings_count = self.export_embeddings()
            relationships_count = self.export_graph_relationships()
            etim_count, eclass_count, attr_count = self.export_eclass_etim_classifications()

            # Create summary
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            summary = {
                'export_completed_at': end_time.isoformat(),
                'duration_seconds': duration,
                'source_database': self.db_config['database'],
                'export_directory': str(self.export_dir),
                'data_exported': {
                    'products': products_count,
                    'features': features_count,
                    'embeddings': embeddings_count,
                    'relationships': relationships_count,
                    'etim_classifications': etim_count,
                    'eclass_classifications': eclass_count,
                    'eclass_attributes': attr_count
                }
            }

            summary_file = self.export_dir / "export_summary.json"
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)

            logger.info("")
            logger.info("=" * 70)
            logger.info("EXPORT COMPLETE!")
            logger.info("=" * 70)
            logger.info(f"Duration: {duration:.1f} seconds")
            logger.info(f"Products: {products_count:,}")
            logger.info(f"Features: {features_count:,}")
            logger.info(f"Embeddings: {embeddings_count:,}")
            logger.info(f"Relationships: {relationships_count:,}")
            logger.info(f"ETIM: {etim_count:,}")
            logger.info(f"ECLASS: {eclass_count:,}")
            logger.info(f"Summary: {summary_file}")
            logger.info("=" * 70)

            return summary

        except Exception as e:
            logger.error(f"✗ Export failed: {e}", exc_info=True)
            raise


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Export Bosch data from PostgreSQL')
    parser.add_argument('--host', default='localhost', help='PostgreSQL host')
    parser.add_argument('--port', type=int, default=5434, help='PostgreSQL port')
    parser.add_argument('--database', default='bosch_products', help='Database name')
    parser.add_argument('--user', default='bosch_user', help='Database user')
    parser.add_argument('--password', default='bosch_secure_2024', help='Database password')
    parser.add_argument('--export-dir', help='Export directory')
    parser.add_argument('--what', choices=['all', 'products', 'embeddings', 'relationships', 'eclass-etim'],
                       default='all', help='What to export')

    args = parser.parse_args()

    exporter = BoschDataExporter(
        db_host=args.host,
        db_port=args.port,
        db_name=args.database,
        db_user=args.user,
        db_password=args.password,
        export_dir=args.export_dir
    )

    if args.what == 'all':
        exporter.export_all()
    elif args.what == 'products':
        exporter.export_products()
    elif args.what == 'embeddings':
        exporter.export_embeddings()
    elif args.what == 'relationships':
        exporter.export_graph_relationships()
    elif args.what == 'eclass-etim':
        exporter.export_eclass_etim_classifications()


if __name__ == '__main__':
    main()
