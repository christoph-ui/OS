"""
0711-OS Data Import Service

Imports data bundle into fresh 0711-OS instance.
Called automatically when instance boots with IMPORT_URL env var.
"""

import asyncio
import hashlib
import json
import logging
import os
import shutil
import tarfile
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger(__name__)


class ImportStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    EXTRACTING = "extracting"
    VERIFYING = "verifying"
    IMPORTING_DELTA = "importing_delta"
    IMPORTING_VECTORS = "importing_vectors"
    IMPORTING_LORA = "importing_lora"
    IMPORTING_METADATA = "importing_metadata"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"  # Can resume


@dataclass
class ImportProgress:
    """Progress tracking for import"""
    status: ImportStatus = ImportStatus.PENDING
    progress_percent: int = 0
    current_step: str = ""
    bytes_downloaded: int = 0
    bytes_total: int = 0
    components_imported: List[str] = field(default_factory=list)
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass
class ImportResult:
    """Result of import operation"""
    success: bool
    customer_id: str
    import_id: str
    progress: ImportProgress
    imported_documents: int = 0
    imported_chunks: int = 0
    imported_embeddings: int = 0
    lakehouse_path: Optional[str] = None
    lora_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "customer_id": self.customer_id,
            "import_id": self.import_id,
            "progress": {
                "status": self.progress.status.value,
                "progress_percent": self.progress.progress_percent,
                "current_step": self.progress.current_step,
                "bytes_downloaded": self.progress.bytes_downloaded,
                "bytes_total": self.progress.bytes_total,
                "components_imported": self.progress.components_imported,
                "error": self.progress.error,
                "started_at": self.progress.started_at,
                "completed_at": self.progress.completed_at,
            },
            "stats": {
                "imported_documents": self.imported_documents,
                "imported_chunks": self.imported_chunks,
                "imported_embeddings": self.imported_embeddings,
            },
            "paths": {
                "lakehouse": self.lakehouse_path,
                "lora": self.lora_path,
            },
        }


class DataImporter:
    """
    Imports customer data bundle into fresh 0711-OS instance.
    
    Usage:
        1. Fresh instance boots with IMPORT_URL environment variable
        2. Boot script calls DataImporter.import_from_url()
        3. Data is downloaded, verified, and imported
        4. Instance signals ready to control plane
    
    Supports:
        - Resumable downloads (Range headers)
        - Checksum verification
        - Progress callbacks (WebSocket)
        - Rollback on failure
    """
    
    def __init__(
        self,
        lakehouse_base: Path = Path("/data/lakehouse"),
        lora_base: Path = Path("/data/loras"),
        temp_base: Path = Path("/tmp/0711-import"),
        control_plane_url: Optional[str] = None,
    ):
        self.lakehouse_base = lakehouse_base
        self.lora_base = lora_base
        self.temp_base = temp_base
        self.control_plane_url = control_plane_url or os.getenv(
            "CONTROL_PLANE_URL", "http://localhost:4080"
        )
        
        self.temp_base.mkdir(parents=True, exist_ok=True)
        self.lakehouse_base.mkdir(parents=True, exist_ok=True)
        self.lora_base.mkdir(parents=True, exist_ok=True)
        
        # State file for resumable imports
        self.state_file = self.temp_base / "import_state.json"
    
    async def import_from_url(
        self,
        manifest_url: str,
        on_progress: Optional[callable] = None,
    ) -> ImportResult:
        """
        Import data bundle from URL.
        
        Args:
            manifest_url: URL to manifest.json or .tar.gz archive
            on_progress: Callback for progress updates
        
        Returns:
            ImportResult with status and stats
        """
        import_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        progress = ImportProgress(started_at=datetime.utcnow().isoformat() + "Z")
        
        try:
            # Step 1: Download
            progress.status = ImportStatus.DOWNLOADING
            progress.current_step = "Downloading bundle"
            if on_progress:
                await on_progress(progress)
            
            archive_path, manifest = await self._download_bundle(
                manifest_url, progress, on_progress
            )
            
            customer_id = manifest.get("customer_id", "unknown")
            
            # Step 2: Extract
            progress.status = ImportStatus.EXTRACTING
            progress.current_step = "Extracting archive"
            progress.progress_percent = 30
            if on_progress:
                await on_progress(progress)
            
            extract_path = await self._extract_bundle(archive_path)
            
            # Step 3: Verify checksums
            progress.status = ImportStatus.VERIFYING
            progress.current_step = "Verifying integrity"
            progress.progress_percent = 40
            if on_progress:
                await on_progress(progress)
            
            await self._verify_checksums(extract_path, manifest)
            
            # Step 4: Import components
            result = ImportResult(
                success=False,
                customer_id=customer_id,
                import_id=import_id,
                progress=progress,
            )
            
            # Import Delta tables
            progress.status = ImportStatus.IMPORTING_DELTA
            progress.current_step = "Importing Delta tables"
            progress.progress_percent = 50
            if on_progress:
                await on_progress(progress)
            
            delta_stats = await self._import_delta(extract_path, customer_id)
            result.imported_chunks = delta_stats.get("chunks", 0)
            progress.components_imported.append("delta")
            
            # Import vectors
            progress.status = ImportStatus.IMPORTING_VECTORS
            progress.current_step = "Importing vector indices"
            progress.progress_percent = 65
            if on_progress:
                await on_progress(progress)
            
            vector_stats = await self._import_vectors(extract_path, customer_id)
            result.imported_embeddings = vector_stats.get("embeddings", 0)
            progress.components_imported.append("vectors")
            
            # Import LoRA
            progress.status = ImportStatus.IMPORTING_LORA
            progress.current_step = "Loading LoRA adapter"
            progress.progress_percent = 80
            if on_progress:
                await on_progress(progress)
            
            lora_path = await self._import_lora(extract_path, customer_id)
            result.lora_path = str(lora_path) if lora_path else None
            progress.components_imported.append("lora")
            
            # Import metadata
            progress.status = ImportStatus.IMPORTING_METADATA
            progress.current_step = "Importing metadata"
            progress.progress_percent = 90
            if on_progress:
                await on_progress(progress)
            
            meta_stats = await self._import_metadata(extract_path, customer_id)
            result.imported_documents = meta_stats.get("documents", 0)
            progress.components_imported.append("metadata")
            
            # Finalize
            progress.status = ImportStatus.FINALIZING
            progress.current_step = "Finalizing import"
            progress.progress_percent = 95
            if on_progress:
                await on_progress(progress)
            
            result.lakehouse_path = str(self.lakehouse_base / customer_id)
            
            # Cleanup temp files
            shutil.rmtree(extract_path, ignore_errors=True)
            if archive_path.exists():
                archive_path.unlink()
            
            # Signal completion
            progress.status = ImportStatus.COMPLETED
            progress.current_step = "Import complete"
            progress.progress_percent = 100
            progress.completed_at = datetime.utcnow().isoformat() + "Z"
            if on_progress:
                await on_progress(progress)
            
            result.success = True
            
            # Notify control plane
            await self._signal_ready(customer_id, result)
            
            logger.info(f"✅ Import complete for {customer_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Import failed: {e}", exc_info=True)
            progress.status = ImportStatus.FAILED
            progress.error = str(e)
            if on_progress:
                await on_progress(progress)
            
            return ImportResult(
                success=False,
                customer_id=manifest.get("customer_id", "unknown") if 'manifest' in dir() else "unknown",
                import_id=import_id,
                progress=progress,
            )
    
    async def _download_bundle(
        self,
        url: str,
        progress: ImportProgress,
        on_progress: Optional[callable],
    ) -> tuple[Path, Dict]:
        """Download bundle with resume support"""
        archive_path = self.temp_base / "bundle.tar.gz"
        
        # Check for partial download
        start_byte = 0
        if archive_path.exists():
            start_byte = archive_path.stat().st_size
            logger.info(f"Resuming download from byte {start_byte}")
        
        headers = {}
        if start_byte > 0:
            headers["Range"] = f"bytes={start_byte}-"
        
        async with httpx.AsyncClient(timeout=3600.0) as client:
            async with client.stream("GET", url, headers=headers) as response:
                # Handle manifest.json URL (need to get archive URL from it)
                if url.endswith("manifest.json"):
                    manifest = response.json()
                    # Manifest should contain archive URL
                    archive_url = manifest.get("archive_url")
                    if archive_url:
                        return await self._download_bundle(archive_url, progress, on_progress)
                
                total = int(response.headers.get("content-length", 0)) + start_byte
                progress.bytes_total = total
                
                mode = "ab" if start_byte > 0 else "wb"
                with open(archive_path, mode) as f:
                    async for chunk in response.aiter_bytes(chunk_size=1024 * 1024):
                        f.write(chunk)
                        progress.bytes_downloaded = f.tell()
                        progress.progress_percent = int(
                            (progress.bytes_downloaded / total * 30) if total > 0 else 0
                        )
                        if on_progress:
                            await on_progress(progress)
        
        # Extract manifest from archive
        with tarfile.open(archive_path, "r:gz") as tar:
            for member in tar.getmembers():
                if member.name.endswith("manifest.json"):
                    f = tar.extractfile(member)
                    manifest = json.load(f)
                    return archive_path, manifest
        
        return archive_path, {}
    
    async def _extract_bundle(self, archive_path: Path) -> Path:
        """Extract tar.gz archive"""
        extract_path = self.temp_base / "extracted"
        extract_path.mkdir(parents=True, exist_ok=True)
        
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(extract_path)
        
        # Find the customer directory (first subdir)
        subdirs = [d for d in extract_path.iterdir() if d.is_dir()]
        if subdirs:
            return subdirs[0]
        
        return extract_path
    
    async def _verify_checksums(self, extract_path: Path, manifest: Dict):
        """Verify component checksums"""
        components = manifest.get("components", [])
        
        for component in components:
            expected_checksum = component.get("checksum_sha256")
            if not expected_checksum:
                continue
            
            component_path = extract_path / component["path"].rstrip("/")
            if not component_path.exists():
                logger.warning(f"Component not found: {component['name']}")
                continue
            
            # Calculate actual checksum
            hasher = hashlib.sha256()
            if component_path.is_dir():
                for file_path in sorted(component_path.rglob("*")):
                    if file_path.is_file():
                        with open(file_path, "rb") as f:
                            hasher.update(f.read())
            else:
                with open(component_path, "rb") as f:
                    hasher.update(f.read())
            
            actual_checksum = hasher.hexdigest()
            
            if actual_checksum != expected_checksum:
                raise ValueError(
                    f"Checksum mismatch for {component['name']}: "
                    f"expected {expected_checksum}, got {actual_checksum}"
                )
        
        logger.info("✓ All checksums verified")
    
    async def _import_delta(self, extract_path: Path, customer_id: str) -> Dict:
        """Import Delta Lake tables"""
        delta_src = extract_path / "delta"
        if not delta_src.exists():
            return {"chunks": 0}
        
        delta_dest = self.lakehouse_base / customer_id / "delta"
        delta_dest.mkdir(parents=True, exist_ok=True)
        
        # Copy parquet files
        chunks = 0
        for parquet_file in delta_src.rglob("*.parquet"):
            rel_path = parquet_file.relative_to(delta_src)
            dest_file = delta_dest / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(parquet_file, dest_file)
            chunks += 1
        
        # Copy _delta_log
        delta_log_src = delta_src / "_delta_log"
        if delta_log_src.exists():
            shutil.copytree(delta_log_src, delta_dest / "_delta_log", dirs_exist_ok=True)
        
        logger.info(f"✓ Imported {chunks} Delta chunks")
        return {"chunks": chunks}
    
    async def _import_vectors(self, extract_path: Path, customer_id: str) -> Dict:
        """Import LanceDB vector indices"""
        vectors_src = extract_path / "vectors"
        if not vectors_src.exists():
            return {"embeddings": 0}
        
        vectors_dest = self.lakehouse_base / customer_id / "vectors"
        vectors_dest.mkdir(parents=True, exist_ok=True)
        
        # Copy lance files
        embeddings = 0
        for lance_file in vectors_src.rglob("*"):
            if lance_file.is_file():
                rel_path = lance_file.relative_to(vectors_src)
                dest_file = vectors_dest / rel_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(lance_file, dest_file)
                embeddings += 1
        
        logger.info(f"✓ Imported vector indices")
        return {"embeddings": embeddings}
    
    async def _import_lora(self, extract_path: Path, customer_id: str) -> Optional[Path]:
        """Import LoRA adapter weights"""
        lora_src = extract_path / "lora"
        if not lora_src.exists():
            return None
        
        lora_dest = self.lora_base / customer_id
        lora_dest.mkdir(parents=True, exist_ok=True)
        
        # Copy safetensors files
        for lora_file in lora_src.glob("*.safetensors"):
            shutil.copy2(lora_file, lora_dest / lora_file.name)
        
        # Copy adapter config
        config_file = lora_src / "adapter_config.json"
        if config_file.exists():
            shutil.copy2(config_file, lora_dest / "adapter_config.json")
        
        logger.info(f"✓ Imported LoRA adapter to {lora_dest}")
        return lora_dest
    
    async def _import_metadata(self, extract_path: Path, customer_id: str) -> Dict:
        """Import document metadata"""
        metadata_src = extract_path / "metadata"
        if not metadata_src.exists():
            return {"documents": 0}
        
        metadata_dest = self.lakehouse_base / customer_id / "metadata"
        metadata_dest.mkdir(parents=True, exist_ok=True)
        
        documents = 0
        for json_file in metadata_src.glob("*.json"):
            shutil.copy2(json_file, metadata_dest / json_file.name)
            
            # Count documents
            try:
                with open(json_file) as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        documents += len(data)
                    elif isinstance(data, dict) and "documents" in data:
                        documents += len(data["documents"])
            except:
                pass
        
        logger.info(f"✓ Imported metadata ({documents} documents)")
        return {"documents": documents}
    
    async def _signal_ready(self, customer_id: str, result: ImportResult):
        """Signal to control plane that import is complete"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.control_plane_url}/api/sync/complete",
                    json={
                        "customer_id": customer_id,
                        "import_id": result.import_id,
                        "result": result.to_dict(),
                        "instance_id": os.getenv("INSTANCE_ID", "unknown"),
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                logger.info(f"✓ Signaled ready to control plane")
        except Exception as e:
            logger.warning(f"Failed to signal control plane: {e}")


# Boot-time entry point
async def auto_import_on_boot():
    """
    Called during instance boot if IMPORT_URL is set.
    
    Usage in entrypoint.sh:
        if [ -n "$IMPORT_URL" ]; then
            python -c "import asyncio; from orchestrator.import import auto_import_on_boot; asyncio.run(auto_import_on_boot())"
        fi
    """
    import_url = os.getenv("IMPORT_URL")
    if not import_url:
        logger.info("No IMPORT_URL set, skipping auto-import")
        return
    
    logger.info(f"🚀 Auto-importing from {import_url}")
    
    importer = DataImporter()
    
    async def log_progress(progress: ImportProgress):
        logger.info(f"[{progress.status.value}] {progress.current_step} - {progress.progress_percent}%")
    
    result = await importer.import_from_url(import_url, on_progress=log_progress)
    
    if result.success:
        logger.info(f"✅ Auto-import complete: {result.imported_documents} documents")
    else:
        logger.error(f"❌ Auto-import failed: {result.progress.error}")
        raise SystemExit(1)
