#!/usr/bin/env python3
"""
Customer Data Export Pipeline

Exports all customer data from running deployment for Docker image baking:
- Lakehouse data (Delta Lake + LanceDB)
- Neo4j graph database
- MinIO uploaded files
- Installation Parameters from Cradle DB

Usage:
    python scripts/export_customer_data.py eaton

Output:
    /tmp/customer-data/eaton/
    ├── lakehouse/      (327MB - Delta + Lance)
    ├── neo4j/          (50MB - Graph database)
    ├── minio/          (270MB - Original files)
    └── config.json     (Installation Parameters)
"""

import sys
import json
import logging
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime
import hashlib

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CustomerDataExporter:
    """Export customer data from running Docker deployment"""

    def __init__(self, customer_id: str, output_base: Path = Path("/tmp/customer-data")):
        """
        Args:
            customer_id: Customer identifier
            output_base: Base directory for exports
        """
        self.customer_id = customer_id
        self.output_dir = output_base / customer_id
        self.stats = {
            "started_at": datetime.now().isoformat(),
            "customer_id": customer_id,
            "exports": {},
            "errors": []
        }

    def export_all(self) -> bool:
        """
        Export all customer data.

        Returns:
            True if successful
        """
        try:
            logger.info(f"=" * 70)
            logger.info(f"Starting export for customer: {self.customer_id}")
            logger.info(f"Output directory: {self.output_dir}")
            logger.info(f"=" * 70)

            # Step 0: Verify deployment exists
            if not self._verify_deployment():
                logger.error(f"Customer deployment not found: {self.customer_id}")
                return False

            # Step 1: Create output directory
            self._prepare_output_directory()

            # Step 2: Export lakehouse data
            logger.info("\n[1/5] Exporting lakehouse data (Delta Lake + LanceDB)...")
            self._export_lakehouse()

            # Step 3: Export Neo4j database
            logger.info("\n[2/5] Exporting Neo4j graph database...")
            self._export_neo4j()

            # Step 4: Export MinIO files
            logger.info("\n[3/5] Exporting MinIO uploaded files...")
            self._export_minio()

            # Step 5: Export Installation Parameters
            logger.info("\n[4/5] Exporting Installation Parameters...")
            self._export_config()

            # Step 6: Generate manifest
            logger.info("\n[5/5] Generating export manifest...")
            self._generate_manifest()

            # Success summary
            self._print_summary()

            return True

        except Exception as e:
            logger.error(f"Export failed: {e}", exc_info=True)
            self.stats["errors"].append(str(e))
            return False

    def _verify_deployment(self) -> bool:
        """Verify customer deployment is running"""
        try:
            # Check if lakehouse container exists
            result = subprocess.run(
                ["docker", "ps", "-a", "--filter", f"name={self.customer_id}-lakehouse", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                check=True
            )

            return f"{self.customer_id}-lakehouse" in result.stdout

        except subprocess.CalledProcessError:
            return False

    def _prepare_output_directory(self):
        """Create clean output directory"""
        if self.output_dir.exists():
            logger.warning(f"Output directory exists, removing: {self.output_dir}")
            shutil.rmtree(self.output_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "lakehouse").mkdir(exist_ok=True)
        (self.output_dir / "neo4j").mkdir(exist_ok=True)
        (self.output_dir / "minio").mkdir(exist_ok=True)

        logger.info(f"✓ Created output directory structure")

    def _export_lakehouse(self):
        """Export lakehouse data from Docker volume"""
        try:
            container_name = f"{self.customer_id}-lakehouse"
            source_path = "/data/lakehouse"
            dest_path = self.output_dir / "lakehouse"

            # Copy data from container
            logger.info(f"  Copying from {container_name}:{source_path}...")
            subprocess.run(
                ["docker", "cp", f"{container_name}:{source_path}/.", str(dest_path)],
                check=True,
                capture_output=True
            )

            # Verify export
            size = self._get_directory_size(dest_path)
            logger.info(f"  ✓ Exported lakehouse: {size:.2f} MB")

            self.stats["exports"]["lakehouse"] = {
                "size_mb": size,
                "path": str(dest_path),
                "success": True
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"  ✗ Lakehouse export failed: {e}")
            self.stats["errors"].append(f"Lakehouse: {e}")
            self.stats["exports"]["lakehouse"] = {"success": False, "error": str(e)}

    def _export_neo4j(self):
        """Export Neo4j database"""
        try:
            container_name = f"{self.customer_id}-neo4j"

            # Check if Neo4j container exists
            result = subprocess.run(
                ["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True
            )

            if container_name not in result.stdout:
                logger.warning("  ⚠️  Neo4j container not found, skipping")
                self.stats["exports"]["neo4j"] = {"success": False, "error": "Container not found"}
                return

            # Create database dump
            dump_file = f"/tmp/{self.customer_id}-neo4j.dump"
            logger.info(f"  Creating Neo4j dump...")

            subprocess.run(
                ["docker", "exec", container_name, "neo4j-admin", "database", "dump", "neo4j",
                 "--to-path=/tmp", "--overwrite-destination=true"],
                check=True,
                capture_output=True
            )

            # Copy dump from container
            logger.info(f"  Copying Neo4j dump...")
            subprocess.run(
                ["docker", "cp", f"{container_name}:/tmp/neo4j.dump",
                 str(self.output_dir / "neo4j" / "neo4j.dump")],
                check=True
            )

            # Also copy live data directory (for direct mount)
            logger.info(f"  Copying Neo4j data directory...")
            subprocess.run(
                ["docker", "cp", f"{container_name}:/data/.",
                 str(self.output_dir / "neo4j" / "data")],
                check=True,
                capture_output=True
            )

            size = self._get_directory_size(self.output_dir / "neo4j")
            logger.info(f"  ✓ Exported Neo4j: {size:.2f} MB")

            self.stats["exports"]["neo4j"] = {
                "size_mb": size,
                "path": str(self.output_dir / "neo4j"),
                "success": True
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"  ✗ Neo4j export failed: {e}")
            self.stats["errors"].append(f"Neo4j: {e}")
            self.stats["exports"]["neo4j"] = {"success": False, "error": str(e)}

    def _export_minio(self):
        """Export MinIO uploaded files"""
        try:
            bucket_name = f"customer-{self.customer_id}"
            dest_path = self.output_dir / "minio"

            # Check if bucket exists
            logger.info(f"  Checking MinIO bucket: {bucket_name}...")
            result = subprocess.run(
                ["docker", "exec", "0711-minio", "mc", "ls", f"/data/{bucket_name}/"],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.warning(f"  ⚠️  MinIO bucket not found: {bucket_name}")
                self.stats["exports"]["minio"] = {"success": False, "error": "Bucket not found"}
                return

            # Copy files from MinIO
            logger.info(f"  Copying files from MinIO bucket...")
            subprocess.run(
                ["docker", "exec", "0711-minio", "mc", "cp", "--recursive",
                 f"/data/{bucket_name}", f"/tmp/{self.customer_id}-minio/"],
                check=True,
                capture_output=True
            )

            # Copy from container temp to host
            subprocess.run(
                ["docker", "cp", f"0711-minio:/tmp/{self.customer_id}-minio/.",
                 str(dest_path)],
                check=True
            )

            # Cleanup temp in container
            subprocess.run(
                ["docker", "exec", "0711-minio", "rm", "-rf", f"/tmp/{self.customer_id}-minio"],
                check=True,
                capture_output=True
            )

            size = self._get_directory_size(dest_path)
            file_count = len(list(dest_path.rglob("*")))

            logger.info(f"  ✓ Exported MinIO: {size:.2f} MB ({file_count} files)")

            self.stats["exports"]["minio"] = {
                "size_mb": size,
                "file_count": file_count,
                "path": str(dest_path),
                "success": True
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"  ✗ MinIO export failed: {e}")
            self.stats["errors"].append(f"MinIO: {e}")
            self.stats["exports"]["minio"] = {"success": False, "error": str(e)}

    def _export_config(self):
        """Export Installation Parameters from Cradle DB"""
        try:
            logger.info(f"  Querying Cradle Installation DB...")

            # Query Installation Parameters
            result = subprocess.run(
                ["docker", "exec", "cradle-installation-db",
                 "psql", "-U", "cradle", "-d", "installation_configs",
                 "-t", "-A", "-F", ",",
                 "-c", f"SELECT row_to_json(installation_configs) FROM installation_configs WHERE customer_id='{self.customer_id}'"],
                capture_output=True,
                text=True,
                check=True
            )

            if not result.stdout.strip():
                logger.warning(f"  ⚠️  No configuration found for {self.customer_id}")
                self.stats["exports"]["config"] = {"success": False, "error": "Not found"}
                return

            # Parse JSON
            config = json.loads(result.stdout.strip())

            # Save to file
            config_file = self.output_dir / "config.json"
            config_file.write_text(json.dumps(config, indent=2))

            logger.info(f"  ✓ Exported configuration")

            self.stats["exports"]["config"] = {
                "path": str(config_file),
                "success": True
            }

        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.error(f"  ✗ Config export failed: {e}")
            self.stats["errors"].append(f"Config: {e}")
            self.stats["exports"]["config"] = {"success": False, "error": str(e)}

    def _generate_manifest(self):
        """Generate export manifest with checksums"""
        manifest = {
            "customer_id": self.customer_id,
            "export_date": datetime.now().isoformat(),
            "export_version": "1.0",
            "stats": self.stats,
            "checksums": {}
        }

        # Generate checksums for important files
        for export_type in ["lakehouse", "neo4j", "minio"]:
            export_dir = self.output_dir / export_type
            if export_dir.exists():
                checksum = self._directory_checksum(export_dir)
                manifest["checksums"][export_type] = checksum

        manifest_file = self.output_dir / "manifest.json"
        manifest_file.write_text(json.dumps(manifest, indent=2))

        logger.info(f"  ✓ Generated manifest with checksums")

    def _get_directory_size(self, path: Path) -> float:
        """Get directory size in MB"""
        if not path.exists():
            return 0.0

        total_size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        return total_size / (1024 * 1024)  # Convert to MB

    def _directory_checksum(self, path: Path) -> str:
        """Generate SHA256 checksum for directory contents"""
        hasher = hashlib.sha256()

        for file in sorted(path.rglob('*')):
            if file.is_file():
                hasher.update(file.name.encode())
                with open(file, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b''):
                        hasher.update(chunk)

        return hasher.hexdigest()

    def _print_summary(self):
        """Print export summary"""
        total_size = sum(
            exp.get("size_mb", 0)
            for exp in self.stats["exports"].values()
            if exp.get("success")
        )

        logger.info("\n" + "=" * 70)
        logger.info("✅ EXPORT COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Customer: {self.customer_id}")
        logger.info(f"Output: {self.output_dir}")
        logger.info(f"Total size: {total_size:.2f} MB")
        logger.info("")

        for export_type, data in self.stats["exports"].items():
            status = "✓" if data.get("success") else "✗"
            size = f"{data.get('size_mb', 0):.2f} MB" if data.get("success") else "Failed"
            logger.info(f"  {status} {export_type:12} {size}")

        if self.stats["errors"]:
            logger.warning(f"\n⚠️  Errors encountered: {len(self.stats['errors'])}")
            for error in self.stats["errors"]:
                logger.warning(f"    - {error}")

        logger.info("\n" + "=" * 70)


def main():
    if len(sys.argv) < 2:
        print("Usage: python export_customer_data.py <customer_id>")
        print("Example: python export_customer_data.py eaton")
        sys.exit(1)

    customer_id = sys.argv[1]

    exporter = CustomerDataExporter(customer_id)
    success = exporter.export_all()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
