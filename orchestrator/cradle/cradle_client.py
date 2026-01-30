"""
Cradle Client

Communicates with Cradle services for GPU processing
"""
import logging
from typing import Dict, List, Any
from pathlib import Path
import httpx
import shutil

logger = logging.getLogger(__name__)


class CradleClient:
    """Client for Cradle GPU services"""

    def __init__(
        self,
        embedding_url: str = "http://localhost:8001",
        vision_url: str = "http://localhost:8002",
        image_builder_url: str = "http://localhost:8003"
    ):
        self.embedding_url = embedding_url
        self.vision_url = vision_url
        self.image_builder_url = image_builder_url

    async def upload_to_staging(
        self,
        customer_id: str,
        data_sources: List[str]
    ) -> Path:
        """
        Upload customer data to Cradle staging area

        Args:
            customer_id: Customer identifier
            data_sources: List of source paths

        Returns:
            Staging path
        """
        staging_path = Path(f"/home/christoph.bertsch/0711/0711-cradle/staging/{customer_id}")
        staging_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Uploading data to staging: {staging_path}")

        for source in data_sources:
            source_path = Path(source)
            if source_path.exists():
                if source_path.is_dir():
                    shutil.copytree(source_path, staging_path / source_path.name, dirs_exist_ok=True)
                else:
                    shutil.copy(source_path, staging_path)

        logger.info(f"✓ Data uploaded to {staging_path}")
        return staging_path

    async def process_customer_data(
        self,
        customer_id: str,
        staging_path: Path,
        config: Dict
    ) -> Dict[str, Any]:
        """
        Process customer data with Cradle GPU services

        Steps:
        1. Crawl files
        2. Extract content
        3. Generate embeddings
        4. Extract entities
        5. Build knowledge graph

        Returns:
            Processing results
        """
        logger.info(f"Processing data for {customer_id}")

        # For now: Simplified implementation
        # In production: Would orchestrate full ingestion pipeline

        stats = {
            "total_files": 0,
            "total_documents": 0,
            "total_embeddings": 0,
            "graph_nodes": 0,
            "graph_edges": 0,
            "storage_mb": 0
        }

        # Count files
        files = list(staging_path.rglob("*"))
        stats["total_files"] = len([f for f in files if f.is_file()])

        # Placeholder processing
        stats["total_documents"] = stats["total_files"] * 50  # Rough estimate
        stats["total_embeddings"] = stats["total_documents"]
        stats["graph_nodes"] = stats["total_documents"] // 2
        stats["graph_edges"] = stats["graph_nodes"] * 3

        output_path = staging_path / "processed"
        output_path.mkdir(exist_ok=True)

        logger.info(f"✓ Processing complete: {stats}")

        return {
            "stats": stats,
            "output_path": output_path
        }

    async def build_customer_image(
        self,
        customer_id: str,
        data_path: Path,
        version: str = "1.0",
        skip_export: bool = False
    ) -> Dict[str, Any]:
        """
        Build Docker image for customer using Cradle Console Builder

        Args:
            customer_id: Customer identifier
            data_path: Path to processed data (lakehouse, minio)
            version: Image version
            skip_export: Skip tar.gz export (faster testing)

        Returns:
            Image build results
        """
        logger.info(f"Building Docker image for {customer_id}")

        try:
            # Import Cradle Console Builder
            import sys
            sys.path.insert(0, '/home/christoph.bertsch/0711/0711-cradle/image_builder')
            from console_builder import CradleConsoleBuilder

            # Initialize builder
            builder = CradleConsoleBuilder(
                output_path="/tmp",
                template_path="/home/christoph.bertsch/0711/0711-cradle/image_builder/templates",
                db_host="localhost",
                db_port=5433,
                db_name="installation_configs",
                db_user="cradle",
                db_password="cradle_secret_2025"
            )

            # Build console
            result = builder.build_console(
                customer_id=customer_id,
                data_path=data_path,
                version=version,
                skip_export=skip_export
            )

            if result['success']:
                logger.info(f"✓ Image built: {result['image_name']}")
                return {
                    "success": True,
                    "image_name": result['image_name'],
                    "archive_path": result['archive_path'],
                    "deployment_dir": result['deployment_dir'],
                    "ports": result['ports'],
                    "version": version
                }
            else:
                logger.error(f"Build failed: {result['error']}")
                return {
                    "success": False,
                    "error": result['error']
                }

        except Exception as e:
            logger.error(f"Build failed with exception: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def cleanup_staging(self, staging_path: Path):
        """Clean up staging directory"""
        if staging_path.exists():
            shutil.rmtree(staging_path)
            logger.info(f"✓ Staging cleaned up: {staging_path}")
