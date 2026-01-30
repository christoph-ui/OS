#!/usr/bin/env python3
"""
Re-import Eaton Data After /tmp Disaster Fix

This script re-ingests all 617 Eaton files from MinIO after fixing
the /tmp/lakehouse disaster. Data will be stored in persistent Docker
volume instead of ephemeral /tmp directory.

Created: 2026-01-11
Author: Claude Code
Reason: Eaton data was lost due to /tmp bind mount

Usage:
    python scripts/reimport_eaton.py [--dry-run]

Requirements:
    - eaton-lakehouse container running with Docker volume
    - MinIO accessible at localhost:4050
    - customer-eaton bucket exists with 617 files
"""

import asyncio
import logging
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from minio import Minio
from minio.error import S3Error

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.orchestrator import IngestionOrchestrator, FolderConfig
from core.paths import CustomerPaths

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EatonReimporter:
    """Re-import Eaton data from MinIO with persistent storage"""

    def __init__(self, dry_run: bool = False):
        self.customer_id = "eaton"
        self.minio_bucket = "customer-eaton"
        self.dry_run = dry_run

        # MinIO client
        self.minio = Minio(
            endpoint="localhost:4050",
            access_key="0711admin",
            secret_key="0711secret",
            secure=False
        )

        # Get persistent lakehouse path (Docker volume or /var/lib)
        self.lakehouse_path = CustomerPaths.get_lakehouse_path(self.customer_id)
        logger.info(f"Lakehouse path: {self.lakehouse_path} (persistent storage)")

        # Validate path is NOT /tmp
        if not CustomerPaths.validate_path_safety(self.lakehouse_path):
            raise ValueError(
                f"UNSAFE PATH DETECTED: {self.lakehouse_path}\n"
                "Lakehouse path must NOT be in /tmp! Fix CustomerPaths configuration."
            )

    async def count_minio_files(self) -> int:
        """Count files in MinIO bucket"""
        try:
            objects = list(self.minio.list_objects(bucket_name=self.minio_bucket))
            count = len(objects)
            logger.info(f"Found {count} files in MinIO bucket: {self.minio_bucket}")
            return count
        except S3Error as e:
            logger.error(f"MinIO error: {e}")
            return 0

    async def download_from_minio(self, temp_dir: Path) -> int:
        """
        Download all files from MinIO to temporary directory.

        Args:
            temp_dir: Temporary directory for downloads

        Returns:
            Number of files downloaded
        """
        logger.info(f"Downloading files from MinIO to {temp_dir}...")

        downloaded = 0
        objects = self.minio.list_objects(bucket_name=self.minio_bucket)

        for obj in objects:
            try:
                # Create subdirectories if object name contains /
                file_path = temp_dir / obj.object_name.strip('/')
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # Download file
                self.minio.fget_object(
                    bucket_name=self.minio_bucket,
                    object_name=obj.object_name,
                    file_path=str(file_path)
                )

                downloaded += 1
                if downloaded % 50 == 0:
                    logger.info(f"  Downloaded {downloaded} files...")

            except S3Error as e:
                logger.error(f"Failed to download {obj.object_name}: {e}")
                continue

        logger.info(f"✓ Downloaded {downloaded} files from MinIO")
        return downloaded

    async def run_ingestion(self, data_dir: Path):
        """
        Run ingestion pipeline on downloaded files.

        Args:
            data_dir: Directory containing downloaded files
        """
        logger.info("="*70)
        logger.info(f"STARTING INGESTION PIPELINE")
        logger.info(f"  Customer: {self.customer_id}")
        logger.info(f"  Source: {data_dir}")
        logger.info(f"  Lakehouse: {self.lakehouse_path}")
        logger.info("="*70)

        # Create folder config for ingestion
        folder_configs = [FolderConfig(
            path=data_dir,
            mcp_assignment="general",  # Can be classified later
            recursive=True
        )]

        # Initialize orchestrator with PERSISTENT lakehouse path
        # Use GPU 0 (138GB free) for embeddings with large batch size
        import os
        os.environ['CUDA_VISIBLE_DEVICES'] = '0'  # Use GPU 0

        orchestrator = IngestionOrchestrator(
            lakehouse_path=self.lakehouse_path,
            vllm_url="http://localhost:4030",
            embedding_model="intfloat/multilingual-e5-large",
            claude_api_key=None,  # Will use ANTHROPIC_API_KEY env var
            batch_size=512,  # Increased from 128 (GPU 0 has 138GB free!)
            max_workers=8  # Increased from 4 (more CPU cores available)
        )

        logger.info(f"Using GPU 0 for embeddings (138GB free VRAM)")
        logger.info(f"Batch size: 512 (optimized for H200 NVL)")

        # Progress callback
        def log_progress(progress):
            logger.info(
                f"  [{progress.status.value}] "
                f"{progress.progress_percent:.1f}% - "
                f"{progress.current_phase} - "
                f"{progress.processed_files}/{progress.total_files} files"
            )

        orchestrator.on_progress(log_progress)

        # Run ingestion
        result = await orchestrator.ingest(folder_configs)

        # Log summary
        logger.info("="*70)
        logger.info("INGESTION COMPLETE")
        logger.info("="*70)
        logger.info(f"  Status: {result.status.value}")
        logger.info(f"  Total files: {result.total_files}")
        logger.info(f"  Processed: {result.processed_files}")
        logger.info(f"  Failed: {result.failed_files}")
        logger.info(f"  Duration: {(result.completed_at - result.started_at).total_seconds():.1f}s")

        if result.stats_by_mcp:
            logger.info("\n  Documents by MCP:")
            for mcp, count in result.stats_by_mcp.items():
                logger.info(f"    {mcp}: {count}")

        if result.errors:
            logger.warning(f"\n  Errors ({len(result.errors)}):")
            for error in result.errors[:10]:
                logger.warning(f"    - {error}")

        return result

    async def verify_results(self):
        """Verify ingestion results by checking lakehouse"""
        logger.info("="*70)
        logger.info("VERIFYING RESULTS")
        logger.info("="*70)

        try:
            # Check if lakehouse directories exist
            delta_path = self.lakehouse_path / "delta"
            lance_path = self.lakehouse_path / "lance"

            if delta_path.exists():
                tables = list(delta_path.iterdir())
                logger.info(f"✓ Delta Lake: {len(tables)} tables found")
                for table in tables[:5]:
                    logger.info(f"    - {table.name}")
            else:
                logger.warning("✗ Delta Lake directory not found")

            if lance_path.exists():
                datasets = list(lance_path.iterdir())
                logger.info(f"✓ LanceDB: {len(datasets)} datasets found")
                for dataset in datasets:
                    logger.info(f"    - {dataset.name}")
            else:
                logger.warning("✗ LanceDB directory not found")

            # Try to get stats from lakehouse container HTTP API
            import httpx
            try:
                response = httpx.get("http://localhost:9302/stats", timeout=10)
                if response.status_code == 200:
                    stats = response.json()
                    logger.info(f"\n✓ Lakehouse API stats:")
                    logger.info(f"    Delta tables: {stats.get('delta_tables', 0)}")
                    logger.info(f"    Lance datasets: {stats.get('lance_datasets', 0)}")
                    logger.info(f"    Total size: {stats.get('total_size_mb', 0):.2f} MB")
                else:
                    logger.warning(f"Lakehouse API returned {response.status_code}")
            except Exception as e:
                logger.warning(f"Could not reach lakehouse API: {e}")

        except Exception as e:
            logger.error(f"Verification failed: {e}")

    async def run(self):
        """Main execution flow"""
        start_time = datetime.now()

        logger.info("="*70)
        logger.info("EATON DATA RE-IMPORT")
        logger.info("="*70)
        logger.info(f"  Customer ID: {self.customer_id}")
        logger.info(f"  MinIO Bucket: {self.minio_bucket}")
        logger.info(f"  Lakehouse Path: {self.lakehouse_path}")
        logger.info(f"  Dry Run: {self.dry_run}")
        logger.info("="*70)

        # Step 1: Check MinIO
        file_count = await self.count_minio_files()
        if file_count == 0:
            logger.error("No files found in MinIO bucket! Cannot proceed.")
            return False

        if self.dry_run:
            logger.info(f"\nDRY RUN: Would process {file_count} files")
            logger.info(f"Target lakehouse: {self.lakehouse_path}")
            return True

        # Step 2: Download files from MinIO
        temp_dir = CustomerPaths.get_temp_path(self.customer_id, prefix="reimport")
        logger.info(f"\nTemporary download directory: {temp_dir}")

        try:
            downloaded = await self.download_from_minio(temp_dir)

            if downloaded == 0:
                logger.error("Failed to download files from MinIO")
                return False

            # Step 3: Run ingestion
            result = await self.run_ingestion(temp_dir)

            # Step 4: Verify results
            await self.verify_results()

            # Step 5: Summary
            duration = (datetime.now() - start_time).total_seconds()
            logger.info("="*70)
            logger.info("RE-IMPORT COMPLETED SUCCESSFULLY")
            logger.info("="*70)
            logger.info(f"  Files downloaded: {downloaded}")
            logger.info(f"  Files processed: {result.processed_files}")
            logger.info(f"  Total duration: {duration:.1f}s")
            logger.info(f"  Data stored in: {self.lakehouse_path}")
            logger.info("="*70)

            return result.status.value == "complete"

        finally:
            # Cleanup temp directory
            if temp_dir.exists():
                logger.info(f"Cleaning up temp directory: {temp_dir}")
                shutil.rmtree(temp_dir, ignore_errors=True)


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Re-import Eaton data after /tmp disaster fix"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode (check MinIO, don't process)"
    )
    args = parser.parse_args()

    reimporter = EatonReimporter(dry_run=args.dry_run)
    success = await reimporter.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
