"""
Bosch Data Import Script

Imports exported Bosch data into 0711-OS lakehouse:
- Products → Delta Lake tables
- Embeddings → LanceDB with indexing
- Graph relationships → Neo4j
- ECLASS/ETIM classifications → Delta Lake

Source: /home/christoph.bertsch/0711/0711-OS/lakehouse/clients/bosch/export/
Target: 0711-OS Lakehouse (Delta + Lance + Neo4j)
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
import json
import lancedb
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from delta import configure_spark_with_delta_pip, DeltaTable
from pyspark.sql import SparkSession
from neo4j import GraphDatabase

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BoschDataImporter:
    """Imports Bosch data into 0711-OS lakehouse"""

    def __init__(
        self,
        export_dir: str = None,
        delta_path: str = None,
        lance_path: str = None,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "password"
    ):
        self.export_dir = Path(export_dir or "/home/christoph.bertsch/0711/0711-OS/lakehouse/clients/bosch/export")
        self.delta_path = Path(delta_path or "/home/christoph.bertsch/0711/0711-OS/lakehouse/clients/bosch/delta")
        self.lance_path = Path(lance_path or "/home/christoph.bertsch/0711/0711-OS/lakehouse/clients/bosch/vector")

        self.delta_path.mkdir(parents=True, exist_ok=True)
        self.lance_path.mkdir(parents=True, exist_ok=True)

        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password

        # Initialize Spark with Delta
        self.spark = self._init_spark()

        logger.info(f"Import from: {self.export_dir}")
        logger.info(f"Delta Lake: {self.delta_path}")
        logger.info(f"LanceDB: {self.lance_path}")
        logger.info(f"Neo4j: {self.neo4j_uri}")

    def _init_spark(self):
        """Initialize Spark session with Delta Lake"""
        builder = SparkSession.builder \
            .appName("BoschDataImport") \
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
            .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
            .config("spark.driver.memory", "4g") \
            .config("spark.executor.memory", "4g")

        spark = configure_spark_with_delta_pip(builder).getOrCreate()
        logger.info("✓ Spark session initialized with Delta Lake")
        return spark

    def import_products_to_delta(self):
        """Import products to Delta Lake"""
        logger.info("=" * 70)
        logger.info("IMPORTING PRODUCTS TO DELTA LAKE")
        logger.info("=" * 70)

        # Find all product chunks
        product_chunks = sorted(self.export_dir.glob("products_chunk_*.parquet"))
        logger.info(f"Found {len(product_chunks)} product chunks")

        if not product_chunks:
            logger.error("No product chunks found!")
            return 0

        # Read all chunks
        dfs = []
        for chunk_file in product_chunks:
            df = self.spark.read.parquet(str(chunk_file))
            dfs.append(df)
            logger.info(f"  Loaded {chunk_file.name}: {df.count()} products")

        # Union all chunks
        products_df = dfs[0]
        for df in dfs[1:]:
            products_df = products_df.union(df)

        total_products = products_df.count()
        logger.info(f"Total products to import: {total_products:,}")

        # Write to Delta Lake
        products_table_path = self.delta_path / "products"
        products_df.write \
            .format("delta") \
            .mode("overwrite") \
            .option("overwriteSchema", "true") \
            .save(str(products_table_path))

        logger.info(f"✓ Products imported to Delta: {total_products:,} → {products_table_path}")

        # Create optimized indexes
        logger.info("  Creating indexes...")
        delta_table = DeltaTable.forPath(self.spark, str(products_table_path))
        delta_table.optimize().executeCompaction()
        logger.info("  ✓ Table optimized")

        return total_products

    def import_features_to_delta(self):
        """Import product features to Delta Lake"""
        logger.info("=" * 70)
        logger.info("IMPORTING FEATURES TO DELTA LAKE")
        logger.info("=" * 70)

        feature_chunks = sorted(self.export_dir.glob("features_chunk_*.parquet"))
        logger.info(f"Found {len(feature_chunks)} feature chunks")

        if not feature_chunks:
            logger.warning("No feature chunks found, skipping")
            return 0

        dfs = []
        for chunk_file in feature_chunks:
            df = self.spark.read.parquet(str(chunk_file))
            dfs.append(df)
            logger.info(f"  Loaded {chunk_file.name}: {df.count()} features")

        features_df = dfs[0]
        for df in dfs[1:]:
            features_df = features_df.union(df)

        total_features = features_df.count()
        logger.info(f"Total features to import: {total_features:,}")

        features_table_path = self.delta_path / "features"
        features_df.write \
            .format("delta") \
            .mode("overwrite") \
            .save(str(features_table_path))

        logger.info(f"✓ Features imported to Delta: {total_features:,} → {features_table_path}")

        return total_features

    def import_embeddings_to_lance(self):
        """Import embeddings to LanceDB"""
        logger.info("=" * 70)
        logger.info("IMPORTING EMBEDDINGS TO LANCEDB")
        logger.info("=" * 70)

        embeddings_file = self.export_dir / "embeddings.npz"

        if not embeddings_file.exists():
            logger.warning("No embeddings file found, skipping")
            return 0

        # Load embeddings
        data = np.load(embeddings_file)
        product_ids = data['product_ids']
        embeddings = data['embeddings']
        models = data['models']

        logger.info(f"Loaded {len(product_ids):,} embeddings")
        logger.info(f"  Shape: {embeddings.shape}")
        logger.info(f"  Model: {models[0] if len(models) > 0 else 'unknown'}")

        # Create LanceDB database
        db = lancedb.connect(str(self.lance_path))

        # Prepare data for LanceDB
        records = []
        for i, (pid, emb) in enumerate(zip(product_ids, embeddings)):
            records.append({
                'product_id': int(pid),
                'vector': emb.tolist(),
                'model': str(models[i] if i < len(models) else models[0]),
                'created_at': datetime.now().isoformat()
            })

        # Create table with IVF-PQ index for fast similarity search
        table = db.create_table(
            "product_embeddings",
            data=records,
            mode="overwrite"
        )

        # Create index for similarity search
        logger.info("  Creating vector index...")
        table.create_index(
            metric="cosine",
            num_partitions=256,
            num_sub_vectors=16
        )

        logger.info(f"✓ Embeddings imported to LanceDB: {len(records):,} vectors")
        logger.info(f"  Index created: IVF-PQ (256 partitions, 16 sub-vectors)")

        return len(records)

    def import_graph_to_neo4j(self):
        """Import graph relationships to Neo4j"""
        logger.info("=" * 70)
        logger.info("IMPORTING GRAPH TO NEO4J")
        logger.info("=" * 70)

        relationships_file = self.export_dir / "relationships.parquet"

        if not relationships_file.exists():
            logger.warning("No relationships file found, skipping")
            return 0

        # Load relationships
        df = pd.read_parquet(relationships_file)
        logger.info(f"Loaded {len(df):,} relationships")

        # Connect to Neo4j
        driver = GraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_user, self.neo4j_password)
        )

        with driver.session() as session:
            # Create constraints and indexes
            logger.info("  Creating constraints...")
            session.run("CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE")

            # Clear existing data (optional - comment out to preserve)
            logger.info("  Clearing existing Bosch data...")
            session.run("MATCH (p:Product {client: 'bosch'}) DETACH DELETE p")

            # Import relationships in batches
            batch_size = 1000
            total_imported = 0

            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i+batch_size]

                # Create nodes and relationships
                for _, row in batch.iterrows():
                    session.run("""
                        MERGE (source:Product {id: $source_id, client: 'bosch'})
                        MERGE (target:Product {id: $target_id, client: 'bosch'})
                        MERGE (source)-[r:RELATED {
                            type: $rel_type,
                            strength: $strength
                        }]->(target)
                    """, source_id=int(row['source_product_id']),
                         target_id=int(row['target_product_id']),
                         rel_type=row['relationship_type'],
                         strength=float(row['strength']))

                total_imported += len(batch)
                logger.info(f"  Imported {total_imported:,}/{len(df):,} relationships")

        driver.close()
        logger.info(f"✓ Graph imported to Neo4j: {len(df):,} relationships")

        return len(df)

    def import_classifications_to_delta(self):
        """Import ECLASS/ETIM classifications to Delta Lake"""
        logger.info("=" * 70)
        logger.info("IMPORTING ECLASS/ETIM CLASSIFICATIONS")
        logger.info("=" * 70)

        # ETIM
        etim_file = self.export_dir / "etim_classifications.parquet"
        if etim_file.exists():
            etim_df = self.spark.read.parquet(str(etim_file))
            etim_count = etim_df.count()
            etim_table_path = self.delta_path / "etim_classifications"
            etim_df.write.format("delta").mode("overwrite").save(str(etim_table_path))
            logger.info(f"✓ ETIM classifications: {etim_count:,} → {etim_table_path}")
        else:
            etim_count = 0
            logger.warning("No ETIM classifications found")

        # ECLASS
        eclass_file = self.export_dir / "eclass_classifications.parquet"
        if eclass_file.exists():
            eclass_df = self.spark.read.parquet(str(eclass_file))
            eclass_count = eclass_df.count()
            eclass_table_path = self.delta_path / "eclass_classifications"
            eclass_df.write.format("delta").mode("overwrite").save(str(eclass_table_path))
            logger.info(f"✓ ECLASS classifications: {eclass_count:,} → {eclass_table_path}")
        else:
            eclass_count = 0
            logger.warning("No ECLASS classifications found")

        # ECLASS attributes
        attr_file = self.export_dir / "eclass_attributes.parquet"
        if attr_file.exists():
            attr_df = self.spark.read.parquet(str(attr_file))
            attr_count = attr_df.count()
            attr_table_path = self.delta_path / "eclass_attributes"
            attr_df.write.format("delta").mode("overwrite").save(str(attr_table_path))
            logger.info(f"✓ ECLASS attributes: {attr_count:,} → {attr_table_path}")
        else:
            attr_count = 0

        return etim_count, eclass_count, attr_count

    def import_all(self):
        """Import all Bosch data to lakehouse"""
        logger.info("=" * 70)
        logger.info("BOSCH DATA IMPORT - STARTING")
        logger.info("=" * 70)
        logger.info("")

        start_time = datetime.now()

        try:
            # Import all data
            products_count = self.import_products_to_delta()
            features_count = self.import_features_to_delta()
            embeddings_count = self.import_embeddings_to_lance()
            relationships_count = self.import_graph_to_neo4j()
            etim_count, eclass_count, attr_count = self.import_classifications_to_delta()

            # Create summary
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            summary = {
                'import_completed_at': end_time.isoformat(),
                'duration_seconds': duration,
                'delta_path': str(self.delta_path),
                'lance_path': str(self.lance_path),
                'neo4j_uri': self.neo4j_uri,
                'data_imported': {
                    'products': products_count,
                    'features': features_count,
                    'embeddings': embeddings_count,
                    'relationships': relationships_count,
                    'etim_classifications': etim_count,
                    'eclass_classifications': eclass_count,
                    'eclass_attributes': attr_count
                }
            }

            summary_file = self.delta_path / "import_summary.json"
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)

            logger.info("")
            logger.info("=" * 70)
            logger.info("IMPORT COMPLETE!")
            logger.info("=" * 70)
            logger.info(f"Duration: {duration:.1f} seconds")
            logger.info(f"Products (Delta): {products_count:,}")
            logger.info(f"Features (Delta): {features_count:,}")
            logger.info(f"Embeddings (Lance): {embeddings_count:,}")
            logger.info(f"Relationships (Neo4j): {relationships_count:,}")
            logger.info(f"ETIM (Delta): {etim_count:,}")
            logger.info(f"ECLASS (Delta): {eclass_count:,}")
            logger.info(f"Summary: {summary_file}")
            logger.info("=" * 70)

            return summary

        except Exception as e:
            logger.error(f"✗ Import failed: {e}", exc_info=True)
            raise
        finally:
            self.spark.stop()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Import Bosch data to lakehouse')
    parser.add_argument('--export-dir', help='Export directory')
    parser.add_argument('--delta-path', help='Delta Lake path')
    parser.add_argument('--lance-path', help='LanceDB path')
    parser.add_argument('--neo4j-uri', default='bolt://localhost:7687', help='Neo4j URI')
    parser.add_argument('--neo4j-user', default='neo4j', help='Neo4j user')
    parser.add_argument('--neo4j-password', default='password', help='Neo4j password')
    parser.add_argument('--what', choices=['all', 'products', 'embeddings', 'graph', 'classifications'],
                       default='all', help='What to import')

    args = parser.parse_args()

    importer = BoschDataImporter(
        export_dir=args.export_dir,
        delta_path=args.delta_path,
        lance_path=args.lance_path,
        neo4j_uri=args.neo4j_uri,
        neo4j_user=args.neo4j_user,
        neo4j_password=args.neo4j_password
    )

    if args.what == 'all':
        importer.import_all()
    elif args.what == 'products':
        importer.import_products_to_delta()
        importer.import_features_to_delta()
    elif args.what == 'embeddings':
        importer.import_embeddings_to_lance()
    elif args.what == 'graph':
        importer.import_graph_to_neo4j()
    elif args.what == 'classifications':
        importer.import_classifications_to_delta()


if __name__ == '__main__':
    main()
