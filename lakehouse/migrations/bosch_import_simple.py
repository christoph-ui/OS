"""
Simplified Bosch Data Import (No Spark dependency)

Uses pandas + LanceDB + Neo4j directly
Faster and simpler for initial migration
"""

import os
import logging
import numpy as np
import pandas as pd
import json
import lancedb
from pathlib import Path
from datetime import datetime
from neo4j import GraphDatabase

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BoschSimpleImporter:
    """Simple importer using pandas (no Spark required)"""

    def __init__(
        self,
        export_dir: str = None,
        delta_path: str = None,
        lance_path: str = None,
        neo4j_uri: str = "bolt://localhost:7688",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "zeroseven2024"
    ):
        self.export_dir = Path(export_dir or "lakehouse/clients/bosch/export")
        self.delta_path = Path(delta_path or "lakehouse/clients/bosch/delta")
        self.lance_path = Path(lance_path or "lakehouse/clients/bosch/vector")

        self.delta_path.mkdir(parents=True, exist_ok=True)
        self.lance_path.mkdir(parents=True, exist_ok=True)

        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password

        logger.info(f"Import from: {self.export_dir}")
        logger.info(f"Delta (Parquet): {self.delta_path}")
        logger.info(f"LanceDB: {self.lance_path}")
        logger.info(f"Neo4j: {self.neo4j_uri}")

    def import_products(self):
        """Import products to Delta Lake (as Parquet for now)"""
        logger.info("=" * 70)
        logger.info("IMPORTING PRODUCTS")
        logger.info("=" * 70)

        # Find all chunks
        chunks = sorted(self.export_dir.glob("products_chunk_*.parquet"))
        logger.info(f"Found {len(chunks)} chunks")

        # Combine all chunks
        dfs = []
        for chunk in chunks:
            df = pd.read_parquet(chunk)
            dfs.append(df)
            logger.info(f"  Loaded {chunk.name}: {len(df)} products")

        products_df = pd.concat(dfs, ignore_index=True)
        total = len(products_df)
        logger.info(f"Total products: {total:,}")

        # Save as single Parquet (Delta format without Spark)
        output_file = self.delta_path / "products.parquet"
        products_df.to_parquet(output_file, index=False, compression='snappy')

        logger.info(f"✓ Products saved: {total:,} → {output_file}")
        return total

    def import_features(self):
        """Import product features"""
        logger.info("=" * 70)
        logger.info("IMPORTING FEATURES")
        logger.info("=" * 70)

        chunks = sorted(self.export_dir.glob("features_chunk_*.parquet"))
        if not chunks:
            logger.warning("No feature chunks found")
            return 0

        dfs = []
        for chunk in chunks:
            df = pd.read_parquet(chunk)
            dfs.append(df)

        features_df = pd.concat(dfs, ignore_index=True)
        total = len(features_df)

        output_file = self.delta_path / "features.parquet"
        features_df.to_parquet(output_file, index=False, compression='snappy')

        logger.info(f"✓ Features saved: {total:,} → {output_file}")
        return total

    def import_embeddings(self):
        """Import embeddings to LanceDB"""
        logger.info("=" * 70)
        logger.info("IMPORTING EMBEDDINGS TO LANCEDB")
        logger.info("=" * 70)

        embeddings_file = self.export_dir / "embeddings.npz"
        if not embeddings_file.exists():
            logger.warning("No embeddings found")
            return 0

        # Load
        data = np.load(embeddings_file)
        product_ids = data['product_ids']
        embeddings = data['embeddings']
        models = data['models']

        logger.info(f"Loaded {len(product_ids):,} embeddings ({embeddings.shape[1]}D)")

        # Connect to LanceDB
        db = lancedb.connect(str(self.lance_path))

        # Prepare records
        records = []
        for i, (pid, emb) in enumerate(zip(product_ids, embeddings)):
            records.append({
                'product_id': int(pid),
                'vector': emb.tolist(),
                'model': str(models[i] if i < len(models) else models[0]),
                'created_at': datetime.now().isoformat()
            })

        # Create table
        logger.info("Creating LanceDB table...")
        table = db.create_table(
            "product_embeddings",
            data=records,
            mode="overwrite"
        )

        # Create index
        logger.info("Creating vector index (IVF-PQ)...")
        table.create_index(
            metric="cosine",
            num_partitions=256,
            num_sub_vectors=16
        )

        logger.info(f"✓ Embeddings imported: {len(records):,} vectors with IVF-PQ index")
        return len(records)

    def import_graph(self):
        """Import graph to Neo4j"""
        logger.info("=" * 70)
        logger.info("IMPORTING GRAPH TO NEO4J")
        logger.info("=" * 70)

        relationships_file = self.export_dir / "relationships.parquet"
        if not relationships_file.exists():
            logger.warning("No relationships found")
            return 0

        df = pd.read_parquet(relationships_file)
        total = len(df)
        logger.info(f"Loaded {total:,} relationships")

        # Connect to Neo4j
        driver = GraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_user, self.neo4j_password)
        )

        with driver.session() as session:
            # Clear existing Bosch data
            logger.info("  Clearing existing Bosch data...")
            session.run("MATCH (p:Product {client: 'bosch'}) DETACH DELETE p")

            # Import in batches
            batch_size = 1000
            imported = 0

            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i+batch_size]

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
                         rel_type=str(row['relationship_type']),
                         strength=float(row['strength']))

                imported += len(batch)
                if imported % 10000 == 0:
                    logger.info(f"  Progress: {imported:,}/{total:,} relationships")

        driver.close()
        logger.info(f"✓ Graph imported: {total:,} relationships")
        return total

    def import_classifications(self):
        """Import ECLASS/ETIM classifications"""
        logger.info("=" * 70)
        logger.info("IMPORTING CLASSIFICATIONS")
        logger.info("=" * 70)

        counts = {}

        # ETIM
        etim_file = self.export_dir / "etim_classifications.parquet"
        if etim_file.exists():
            df = pd.read_parquet(etim_file)
            output = self.delta_path / "etim_classifications.parquet"
            df.to_parquet(output, index=False)
            counts['etim'] = len(df)
            logger.info(f"✓ ETIM: {len(df):,}")
        else:
            counts['etim'] = 0

        # ECLASS
        eclass_file = self.export_dir / "eclass_classifications.parquet"
        if eclass_file.exists():
            df = pd.read_parquet(eclass_file)
            output = self.delta_path / "eclass_classifications.parquet"
            df.to_parquet(output, index=False)
            counts['eclass'] = len(df)
            logger.info(f"✓ ECLASS: {len(df):,}")
        else:
            counts['eclass'] = 0

        # Attributes
        attr_file = self.export_dir / "eclass_attributes.parquet"
        if attr_file.exists():
            df = pd.read_parquet(attr_file)
            output = self.delta_path / "eclass_attributes.parquet"
            df.to_parquet(output, index=False)
            counts['attributes'] = len(df)
            logger.info(f"✓ Attributes: {len(df):,}")
        else:
            counts['attributes'] = 0

        return counts

    def import_all(self):
        """Import everything"""
        logger.info("=" * 70)
        logger.info("BOSCH SIMPLE IMPORT - STARTING")
        logger.info("=" * 70)
        logger.info("")

        start_time = datetime.now()

        try:
            products = self.import_products()
            features = self.import_features()
            embeddings = self.import_embeddings()
            graph = self.import_graph()
            classifications = self.import_classifications()

            duration = (datetime.now() - start_time).total_seconds()

            logger.info("")
            logger.info("=" * 70)
            logger.info("IMPORT COMPLETE!")
            logger.info("=" * 70)
            logger.info(f"Duration: {duration:.1f} seconds")
            logger.info(f"Products: {products:,}")
            logger.info(f"Features: {features:,}")
            logger.info(f"Embeddings: {embeddings:,}")
            logger.info(f"Graph: {graph:,}")
            logger.info(f"ETIM: {classifications.get('etim', 0):,}")
            logger.info(f"ECLASS: {classifications.get('eclass', 0):,}")
            logger.info("=" * 70)

            # Save summary
            summary = {
                'completed_at': datetime.now().isoformat(),
                'duration_seconds': duration,
                'data_imported': {
                    'products': products,
                    'features': features,
                    'embeddings': embeddings,
                    'graph_relationships': graph,
                    'etim': classifications.get('etim', 0),
                    'eclass': classifications.get('eclass', 0),
                    'attributes': classifications.get('attributes', 0)
                }
            }

            with open(self.delta_path / "import_summary.json", 'w') as f:
                json.dump(summary, f, indent=2)

            return summary

        except Exception as e:
            logger.error(f"✗ Import failed: {e}", exc_info=True)
            raise


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--export-dir', default='lakehouse/clients/bosch/export')
    parser.add_argument('--neo4j-uri', default='bolt://localhost:7688')
    parser.add_argument('--neo4j-user', default='neo4j')
    parser.add_argument('--neo4j-password', default='zeroseven2024')

    args = parser.parse_args()

    importer = BoschSimpleImporter(
        export_dir=args.export_dir,
        neo4j_uri=args.neo4j_uri,
        neo4j_user=args.neo4j_user,
        neo4j_password=args.neo4j_password
    )

    importer.import_all()
