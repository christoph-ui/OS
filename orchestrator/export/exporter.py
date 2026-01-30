"""
0711-OS Data Export Service

Exports processed customer data from staging lakehouse to portable bundle.
Bundle can be imported into any fresh 0711-OS instance (cloud or on-prem).
"""

import asyncio
import hashlib
import json
import logging
import shutil
import tarfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class ExportStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ExportComponent:
    """Single component in export bundle"""
    name: str
    path: str
    size_bytes: int
    checksum_sha256: str
    file_count: int
    format: str  # parquet, lance, json, safetensors, python


@dataclass
class ExportManifest:
    """Manifest describing export bundle contents"""
    version: str = "1.0.0"
    schema_version: str = "2025.01"
    customer_id: str = ""
    created_at: str = ""
    created_by: str = "0711-os-playground"
    
    # Component checksums and metadata
    components: List[ExportComponent] = field(default_factory=list)
    
    # Stats
    total_documents: int = 0
    total_chunks: int = 0
    total_embeddings: int = 0
    total_size_bytes: int = 0
    
    # Import instructions
    min_os_version: str = "1.0.0"
    required_services: List[str] = field(default_factory=lambda: [
        "postgres", "minio", "embeddings", "vllm"
    ])
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "schema_version": self.schema_version,
            "customer_id": self.customer_id,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "components": [
                {
                    "name": c.name,
                    "path": c.path,
                    "size_bytes": c.size_bytes,
                    "checksum_sha256": c.checksum_sha256,
                    "file_count": c.file_count,
                    "format": c.format,
                }
                for c in self.components
            ],
            "stats": {
                "total_documents": self.total_documents,
                "total_chunks": self.total_chunks,
                "total_embeddings": self.total_embeddings,
                "total_size_bytes": self.total_size_bytes,
            },
            "import_requirements": {
                "min_os_version": self.min_os_version,
                "required_services": self.required_services,
            },
        }


@dataclass
class ExportBundle:
    """Complete export bundle"""
    manifest: ExportManifest
    bundle_path: Path
    archive_path: Optional[Path] = None  # .tar.gz location
    
    @property
    def download_url(self) -> Optional[str]:
        """URL to download bundle (set by hosting service)"""
        return None


class DataExporter:
    """
    Exports customer data from staging lakehouse to portable bundle.
    
    The bundle contains:
    - delta/: Delta Lake tables (parquet)
    - vectors/: LanceDB indices
    - metadata/: Document metadata, relationships
    - lora/: Customer LoRA adapter weights
    - handlers/: Claude-generated custom parsers
    - manifest.json: Bundle manifest with checksums
    """
    
    def __init__(
        self,
        staging_base: Path = Path("/data/staging"),
        export_base: Path = Path("/data/exports"),
        minio_endpoint: str = "localhost:4050",
        minio_access_key: str = "0711admin",
        minio_secret_key: str = "0711secret",
    ):
        self.staging_base = staging_base
        self.export_base = export_base
        self.minio_endpoint = minio_endpoint
        self.minio_access_key = minio_access_key
        self.minio_secret_key = minio_secret_key
        
        self.export_base.mkdir(parents=True, exist_ok=True)
    
    async def export_customer(
        self,
        customer_id: str,
        include_raw: bool = False,
        on_progress: Optional[callable] = None,
    ) -> ExportBundle:
        """
        Export customer staging data to portable bundle.
        
        Args:
            customer_id: Customer identifier
            include_raw: Include original uploaded files (larger bundle)
            on_progress: Callback for progress updates
        
        Returns:
            ExportBundle with manifest and paths
        """
        logger.info(f"📦 Starting export for customer {customer_id}")
        
        staging_path = self.staging_base / customer_id
        bundle_path = self.export_base / customer_id / datetime.now().strftime("%Y%m%d_%H%M%S")
        bundle_path.mkdir(parents=True, exist_ok=True)
        
        manifest = ExportManifest(
            customer_id=customer_id,
            created_at=datetime.utcnow().isoformat() + "Z",
        )
        
        components_to_export = [
            ("delta", "delta", "parquet"),
            ("vectors", "vectors", "lance"),
            ("metadata", "metadata", "json"),
            ("lora", "lora", "safetensors"),
            ("handlers", "handlers", "python"),
        ]
        
        if include_raw:
            components_to_export.append(("raw", "raw", "mixed"))
        
        total_steps = len(components_to_export) + 2  # +2 for manifest and archive
        current_step = 0
        
        for component_name, subdir, format_type in components_to_export:
            current_step += 1
            if on_progress:
                await on_progress({
                    "step": f"Exporting {component_name}",
                    "progress": int((current_step / total_steps) * 100),
                })
            
            source_path = staging_path / subdir
            if source_path.exists():
                component = await self._export_component(
                    source_path,
                    bundle_path / subdir,
                    component_name,
                    format_type,
                )
                manifest.components.append(component)
                manifest.total_size_bytes += component.size_bytes
        
        # Export from MinIO if staging is there
        await self._export_from_minio(customer_id, bundle_path, manifest)
        
        # Calculate aggregate stats
        await self._calculate_stats(bundle_path, manifest)
        
        # Write manifest
        current_step += 1
        if on_progress:
            await on_progress({
                "step": "Writing manifest",
                "progress": int((current_step / total_steps) * 100),
            })
        
        manifest_path = bundle_path / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest.to_dict(), f, indent=2)
        
        # Create archive
        current_step += 1
        if on_progress:
            await on_progress({
                "step": "Creating archive",
                "progress": int((current_step / total_steps) * 100),
            })
        
        archive_path = await self._create_archive(bundle_path, customer_id)
        
        logger.info(f"✅ Export complete: {archive_path}")
        
        return ExportBundle(
            manifest=manifest,
            bundle_path=bundle_path,
            archive_path=archive_path,
        )
    
    async def _export_component(
        self,
        source: Path,
        dest: Path,
        name: str,
        format_type: str,
    ) -> ExportComponent:
        """Export single component with checksum"""
        dest.mkdir(parents=True, exist_ok=True)
        
        # Copy files
        file_count = 0
        total_size = 0
        hasher = hashlib.sha256()
        
        if source.is_dir():
            for file_path in source.rglob("*"):
                if file_path.is_file():
                    rel_path = file_path.relative_to(source)
                    dest_file = dest / rel_path
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy and hash
                    shutil.copy2(file_path, dest_file)
                    
                    with open(dest_file, "rb") as f:
                        data = f.read()
                        hasher.update(data)
                        total_size += len(data)
                    
                    file_count += 1
        
        return ExportComponent(
            name=name,
            path=name + "/",
            size_bytes=total_size,
            checksum_sha256=hasher.hexdigest(),
            file_count=file_count,
            format=format_type,
        )
    
    async def _export_from_minio(
        self,
        customer_id: str,
        bundle_path: Path,
        manifest: ExportManifest,
    ):
        """Export data stored in MinIO staging bucket"""
        try:
            from minio import Minio
            
            client = Minio(
                self.minio_endpoint,
                access_key=self.minio_access_key,
                secret_key=self.minio_secret_key,
                secure=False,
            )
            
            bucket_name = f"staging-{customer_id}"
            
            if not client.bucket_exists(bucket_name):
                logger.info(f"No MinIO staging bucket for {customer_id}")
                return
            
            # Download relevant objects
            for obj in client.list_objects(bucket_name, recursive=True):
                # Determine component from path
                obj_path = Path(obj.object_name)
                component = obj_path.parts[0] if obj_path.parts else "raw"
                
                dest_dir = bundle_path / component
                dest_dir.mkdir(parents=True, exist_ok=True)
                
                dest_file = dest_dir / obj_path.name
                client.fget_object(bucket_name, obj.object_name, str(dest_file))
            
            logger.info(f"✓ Exported MinIO data for {customer_id}")
            
        except ImportError:
            logger.warning("minio package not installed, skipping MinIO export")
        except Exception as e:
            logger.error(f"MinIO export failed: {e}")
    
    async def _calculate_stats(self, bundle_path: Path, manifest: ExportManifest):
        """Calculate aggregate statistics"""
        # Count documents from metadata
        metadata_dir = bundle_path / "metadata"
        if metadata_dir.exists():
            for json_file in metadata_dir.glob("*.json"):
                try:
                    with open(json_file) as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            manifest.total_documents += len(data)
                        elif isinstance(data, dict) and "documents" in data:
                            manifest.total_documents += len(data["documents"])
                except:
                    pass
        
        # Count chunks from delta
        delta_dir = bundle_path / "delta" / "chunks"
        if delta_dir.exists():
            manifest.total_chunks = len(list(delta_dir.glob("*.parquet")))
        
        # Count embeddings from vectors
        vectors_dir = bundle_path / "vectors"
        if vectors_dir.exists():
            manifest.total_embeddings = manifest.total_chunks  # Usually 1:1
    
    async def _create_archive(self, bundle_path: Path, customer_id: str) -> Path:
        """Create compressed tar archive"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"{customer_id}_export_{timestamp}.tar.gz"
        archive_path = self.export_base / archive_name
        
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(bundle_path, arcname=customer_id)
        
        return archive_path
    
    async def get_export_url(self, archive_path: Path) -> str:
        """
        Upload archive to MinIO and return download URL.
        
        For on-prem deployments, this URL will be used to sync data.
        """
        try:
            from minio import Minio
            
            client = Minio(
                self.minio_endpoint,
                access_key=self.minio_access_key,
                secret_key=self.minio_secret_key,
                secure=False,
            )
            
            bucket_name = "exports"
            if not client.bucket_exists(bucket_name):
                client.make_bucket(bucket_name)
            
            object_name = archive_path.name
            client.fput_object(bucket_name, object_name, str(archive_path))
            
            # Generate presigned URL (7 days)
            url = client.presigned_get_object(bucket_name, object_name, expires=timedelta(days=7))
            return url
            
        except ImportError:
            # Fallback: return local path
            return f"file://{archive_path}"
        except Exception as e:
            logger.error(f"Failed to upload to MinIO: {e}")
            return f"file://{archive_path}"


# Convenience function for CLI/API
async def export_customer_data(
    customer_id: str,
    include_raw: bool = False,
    staging_base: str = "/data/staging",
    export_base: str = "/data/exports",
) -> Dict[str, Any]:
    """
    Export customer data and return bundle info.
    
    Returns:
        {
            "bundle_path": "/data/exports/customer_123/...",
            "archive_path": "/data/exports/customer_123_export_20250130.tar.gz",
            "manifest": {...},
            "download_url": "https://..."
        }
    """
    exporter = DataExporter(
        staging_base=Path(staging_base),
        export_base=Path(export_base),
    )
    
    bundle = await exporter.export_customer(customer_id, include_raw)
    download_url = await exporter.get_export_url(bundle.archive_path)
    
    return {
        "bundle_path": str(bundle.bundle_path),
        "archive_path": str(bundle.archive_path),
        "manifest": bundle.manifest.to_dict(),
        "download_url": download_url,
    }
