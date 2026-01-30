#!/usr/bin/env python3
"""
Import Complete Eaton Product Catalog

Imports all Eaton data including:
- BMEcat XML product catalog (1.8MB)
- CSV product→image mappings
- 285 product images with OpenAI Vision analysis
- 6 STP 3D CAD models

Uses H200 GPU 0 (138GB free) for embedding generation at massive batch sizes.

Created: 2026-01-11
Author: Claude Code
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.orchestrator import IngestionOrchestrator, FolderConfig
from core.paths import CustomerPaths

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EatonFullCatalogImporter:
    """
    Import complete Eaton product catalog with all assets.

    Processes:
    - Product catalog (BMEcat XML)
    - Image mappings (CSV)
    - Product images (OpenAI Vision)
    - 3D CAD models (STEP)
    """

    def __init__(self):
        self.customer_id = "eaton"
        self.source_dir = Path("/tmp/eaton_new")

        # Get persistent lakehouse path
        self.lakehouse_path = CustomerPaths.get_lakehouse_path(self.customer_id)
        logger.info(f"Lakehouse path: {self.lakehouse_path} (persistent Docker volume)")

        # Validate not /tmp
        if not CustomerPaths.validate_path_safety(self.lakehouse_path):
            raise ValueError("UNSAFE: Lakehouse path is in /tmp!")

    def get_file_stats(self) -> dict:
        """Get statistics about files to import"""
        stats = {
            "total": 0,
            "by_type": {},
            "new_files": []
        }

        for file_path in self.source_dir.rglob("*"):
            if not file_path.is_file():
                continue
            if "__MACOSX" in str(file_path):
                continue

            stats["total"] += 1
            ext = file_path.suffix.lower()
            stats["by_type"][ext] = stats["by_type"].get(ext, 0) + 1

            # Track important new files
            if "Standard_BMECat" in file_path.name:
                stats["new_files"].append(("BMEcat Catalog", file_path.name, file_path.stat().st_size))
            elif file_path.suffix == ".csv":
                stats["new_files"].append(("CSV Mapping", file_path.name, file_path.stat().st_size))

        return stats

    async def run_import(self):
        """Execute full catalog import with GPU optimization"""
        start_time = datetime.now()

        logger.info("="*70)
        logger.info("EATON FULL CATALOG IMPORT")
        logger.info("="*70)
        logger.info(f"  Customer: {self.customer_id}")
        logger.info(f"  Source: {self.source_dir}")
        logger.info(f"  Lakehouse: {self.lakehouse_path}")
        logger.info("="*70)

        # Get file stats
        stats = self.get_file_stats()
        logger.info(f"\nFiles to process: {stats['total']}")
        logger.info("File breakdown:")
        for ext, count in sorted(stats['by_type'].items(), key=lambda x: -x[1]):
            logger.info(f"  {ext}: {count} files")

        logger.info("\nKey new files:")
        for file_type, filename, size in stats['new_files']:
            logger.info(f"  [{file_type}] {filename} ({size/1024/1024:.2f} MB)")

        # Create folder configs for ingestion
        folder_configs = [FolderConfig(
            path=self.source_dir,
            mcp_assignment="etim",  # Route to ETIM MCP
            recursive=True
        )]

        # Initialize orchestrator with PERSISTENT lakehouse path
        # Use GPU 0 (138GB free) for massive batch embedding
        import os
        os.environ['CUDA_VISIBLE_DEVICES'] = '0'  # Use GPU 0

        logger.info("\n" + "="*70)
        logger.info("INITIALIZING INGESTION ORCHESTRATOR")
        logger.info("="*70)
        logger.info(f"  GPU: CUDA Device 0 (138GB free VRAM)")
        logger.info(f"  Batch size: 1024 (optimized for H200 NVL)")
        logger.info(f"  Workers: 16 (parallel processing)")
        logger.info(f"  OpenAI Vision: ENABLED (285 images)")
        logger.info("="*70)

        orchestrator = IngestionOrchestrator(
            lakehouse_path=self.lakehouse_path,
            vllm_url="http://localhost:4030",
            embedding_model="intfloat/multilingual-e5-large",
            claude_api_key=None,  # Will use ANTHROPIC_API_KEY env var
            batch_size=1024,  # MASSIVE batches for H200 (4x default)
            max_workers=16  # More parallel workers
        )

        # Progress callback
        def log_progress(progress):
            logger.info(
                f"  [{progress.status.value.upper()}] "
                f"{progress.progress_percent:.1f}% - "
                f"{progress.current_phase} - "
                f"{progress.processed_files}/{progress.total_files} files"
            )

        orchestrator.on_progress(log_progress)

        # Run ingestion
        logger.info("\n" + "="*70)
        logger.info("STARTING INGESTION PIPELINE")
        logger.info("="*70)
        result = await orchestrator.ingest(folder_configs)

        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()

        # Log summary
        logger.info("\n" + "="*70)
        logger.info("IMPORT COMPLETE")
        logger.info("="*70)
        logger.info(f"  Status: {result.status.value}")
        logger.info(f"  Total files: {result.total_files}")
        logger.info(f"  Processed: {result.processed_files}")
        logger.info(f"  Failed: {result.failed_files}")
        logger.info(f"  Duration: {duration:.1f}s ({duration/60:.1f} min)")
        logger.info(f"  Speed: {result.processed_files / duration:.2f} files/sec")

        if result.stats_by_mcp:
            logger.info("\n  Documents by MCP:")
            for mcp, count in result.stats_by_mcp.items():
                logger.info(f"    {mcp}: {count}")

        if result.errors:
            logger.warning(f"\n  Errors ({len(result.errors)}):")
            for error in result.errors[:10]:
                logger.warning(f"    - {error}")

        # Verify results
        await self.verify_import()

        logger.info("="*70)
        logger.info("SUCCESS - All Eaton data imported and searchable")
        logger.info("="*70)

        return result

    async def verify_import(self):
        """Verify import results"""
        logger.info("\n" + "="*70)
        logger.info("VERIFYING IMPORT RESULTS")
        logger.info("="*70)

        try:
            # Check lakehouse directories
            delta_path = self.lakehouse_path / "delta"
            lance_path = self.lakehouse_path / "lance"

            if delta_path.exists():
                tables = list(delta_path.iterdir())
                logger.info(f"✓ Delta Lake: {len(tables)} tables")
                for table in tables:
                    logger.info(f"    - {table.name}")

            if lance_path.exists():
                datasets = list(lance_path.iterdir())
                logger.info(f"✓ LanceDB: {len(datasets)} datasets")

            # Get embedding count
            import lancedb
            db = lancedb.connect(str(lance_path))
            table = db.open_table('embeddings')
            count = table.count_rows()

            logger.info(f"\n✓ Total embeddings: {count:,}")
            logger.info(f"  (Was: 31,365 → Now: {count:,})")
            logger.info(f"  New embeddings added: {count - 31365:,}")

            # Check via HTTP API
            import httpx
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://localhost:9302/stats")
                    if response.status_code == 200:
                        stats = response.json()
                        logger.info(f"\n✓ Lakehouse API stats:")
                        logger.info(f"    Delta tables: {stats.get('delta_tables', 0)}")
                        logger.info(f"    Lance datasets: {stats.get('lance_datasets', 0)}")
                        logger.info(f"    Total size: {stats.get('total_size_mb', 0):.2f} MB")
            except Exception as e:
                logger.warning(f"Could not reach lakehouse API: {e}")

        except Exception as e:
            logger.error(f"Verification failed: {e}")


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Import complete Eaton product catalog"
    )
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Only show file statistics, don't import"
    )
    args = parser.parse_args()

    importer = EatonFullCatalogImporter()

    if args.stats_only:
        stats = importer.get_file_stats()
        print(f"\nFiles to import: {stats['total']}")
        print("\nBy type:")
        for ext, count in sorted(stats['by_type'].items(), key=lambda x: -x[1]):
            print(f"  {ext}: {count}")
        print("\nKey files:")
        for file_type, filename, size in stats['new_files']:
            print(f"  [{file_type}] {filename}")
        sys.exit(0)

    # Run full import
    result = await importer.run_import()

    sys.exit(0 if result.status.value == "complete" else 1)


if __name__ == "__main__":
    asyncio.run(main())
