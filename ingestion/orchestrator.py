"""
Ingestion Orchestrator - Coordinates the complete ingestion pipeline

Orchestrates: crawl → classify → process → embed → load
Provides progress tracking, error handling, and statistics.
"""

import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

from .crawler.file_crawler import FileCrawler, FileInfo
from .classifier.document_classifier import DocumentClassifier
from .processor.chunker import SmartChunker
from .processor.embedder import Embedder

logger = logging.getLogger(__name__)


class IngestionStatus(str, Enum):
    """Status of ingestion pipeline"""
    PENDING = "pending"
    CRAWLING = "crawling"
    CLASSIFYING = "classifying"
    PROCESSING = "processing"
    EMBEDDING = "embedding"
    LOADING = "loading"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class IngestionProgress:
    """Track ingestion progress"""
    status: IngestionStatus = IngestionStatus.PENDING
    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    current_file: Optional[str] = None
    current_phase: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)
    stats_by_mcp: Dict[str, int] = field(default_factory=dict)

    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage"""
        if self.total_files == 0:
            return 0.0
        return (self.processed_files / self.total_files) * 100

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "status": self.status.value,
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "failed_files": self.failed_files,
            "current_file": self.current_file,
            "current_phase": self.current_phase,
            "progress_percent": round(self.progress_percent, 1),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "errors": self.errors[-10:],  # Last 10 errors
            "stats_by_mcp": self.stats_by_mcp
        }


@dataclass
class FolderConfig:
    """Configuration for a folder to ingest"""
    path: Path
    mcp_assignment: str
    recursive: bool = True


class IngestionOrchestrator:
    """
    Main orchestrator for the ingestion pipeline.

    Pipeline stages:
    1. Crawl - Discover all files in selected folders
    2. Extract - Extract text content from files
    3. Classify - Determine document type and target MCP
    4. Process - Chunk text and extract entities
    5. Embed - Generate vector embeddings
    6. Load - Store in Delta tables and Lance indices
    """

    def __init__(
        self,
        lakehouse_path: Path,
        vllm_url: str = "http://localhost:8001",
        embedding_model: str = "intfloat/multilingual-e5-large",
        claude_api_key: Optional[str] = None,
        batch_size: int = 32,
        max_workers: int = 4
    ):
        """
        Args:
            lakehouse_path: Path to lakehouse storage
            vllm_url: URL of vLLM inference server
            embedding_model: Embedding model name
            claude_api_key: API key for Claude (handler generation)
            batch_size: Batch size for embeddings
            max_workers: Max concurrent workers
        """
        self.lakehouse_path = Path(lakehouse_path)
        self.vllm_url = vllm_url
        self.embedding_model = embedding_model
        self.batch_size = batch_size
        self.max_workers = max_workers

        # Initialize components
        self.claude_api_key = claude_api_key
        self.crawler = FileCrawler(
            claude_api_key=claude_api_key,
            auto_generate_handlers=True,
            customer_id=None  # Will be set in ingest()
        )
        self.classifier = DocumentClassifier(
            vllm_url=vllm_url,
            claude_api_key=claude_api_key  # Pass Claude for better classification
        )
        self.chunker = SmartChunker()
        self.embedder = Embedder(model_name=embedding_model)

        # Entity extractor for graph database
        self.entity_extractor = None
        try:
            from ingestion.processor.entity_extractor import EntityExtractor
            self.entity_extractor = EntityExtractor(language="de", enable_custom_rules=True)
            logger.info("✅ Entity Extractor initialized")
        except ImportError as e:
            logger.warning(f"Entity extractor not available: {e}")

        # Intelligent extractor for structured data mapping
        self.intelligent_extractor = None
        if claude_api_key:
            from ingestion.extractor.intelligent_extractor import IntelligentExtractor
            self.intelligent_extractor = IntelligentExtractor(claude_api_key=claude_api_key)
            logger.info("✅ Intelligent Extractor initialized")

        # Loaders will be initialized when needed
        self._delta_loader = None
        self._lance_loader = None
        self._multi_table_loader = None
        self._graph_loader = None

        # Neo4j configuration (from environment or defaults)
        import os
        self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "zeroseven2024")

        # Progress tracking
        self.progress = IngestionProgress()
        self._progress_callbacks: List[Callable] = []

    @property
    def delta_loader(self):
        """Lazy load Delta loader"""
        if self._delta_loader is None:
            from lakehouse.delta.delta_loader import DeltaLoader
            self._delta_loader = DeltaLoader(self.lakehouse_path / "delta")
        return self._delta_loader

    @property
    def lance_loader(self):
        """Lazy load Lance loader"""
        if self._lance_loader is None:
            from lakehouse.vector.lance_store import LanceLoader
            self._lance_loader = LanceLoader(self.lakehouse_path / "lance")
        return self._lance_loader

    @property
    def multi_table_loader(self):
        """Lazy load multi-table loader"""
        if self._multi_table_loader is None:
            from lakehouse.delta.multi_table_loader import MultiTableLoader
            self._multi_table_loader = MultiTableLoader(self.lakehouse_path)
        return self._multi_table_loader

    @property
    def graph_loader(self):
        """Lazy load graph (Neo4j) loader"""
        if self._graph_loader is None:
            try:
                from lakehouse.graph import Neo4jStore, GraphConfig
                config = GraphConfig(
                    uri=self.neo4j_uri,
                    username=self.neo4j_user,
                    password=self.neo4j_password
                )
                self._graph_loader = Neo4jStore(config=config, customer_id=None)  # Set per call
                logger.info("✅ Neo4j graph store initialized")
            except Exception as e:
                logger.warning(f"Neo4j not available: {e}")
                self._graph_loader = None
        return self._graph_loader

    def on_progress(self, callback: Callable[[IngestionProgress], None]):
        """Register progress callback"""
        self._progress_callbacks.append(callback)

    def _notify_progress(self):
        """Notify all progress listeners"""
        for callback in self._progress_callbacks:
            try:
                callback(self.progress)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")

    async def ingest(self, folders: List[FolderConfig], customer_id: Optional[str] = None) -> IngestionProgress:
        """
        Run the complete ingestion pipeline.

        Args:
            folders: List of folder configurations to ingest
            customer_id: Customer ID for handler persistence

        Returns:
            Final ingestion progress
        """
        # Phase 0: Read deployment context (if exists)
        deployment_context = None
        if customer_id:
            deployment_context = await self._read_deployment_context(customer_id)
            if deployment_context:
                logger.info(f"📋 Read deployment context for {customer_id}")
                logger.info(f"   Company: {deployment_context.get('company_name', 'Unknown')}")
                logger.info(f"   Industry: {deployment_context.get('industry', 'Unknown')}")
                logger.info(f"   Expected format: {deployment_context.get('source_format', 'Unknown')}")

        # Update crawler with customer_id for handler persistence
        if customer_id and customer_id != self.crawler.customer_id:
            self.crawler = FileCrawler(
                claude_api_key=self.claude_api_key,
                auto_generate_handlers=True,
                customer_id=customer_id
            )
            logger.info(f"🎯 Initialized crawler for customer: {customer_id}")

        self.progress = IngestionProgress(
            status=IngestionStatus.CRAWLING,
            started_at=datetime.now()
        )
        self._notify_progress()

        try:
            # Phase 1: Crawl all folders
            logger.info(f"Starting crawl of {len(folders)} folders for customer: {customer_id or 'default'}")
            all_files = await self._crawl_folders(folders)

            self.progress.total_files = len(all_files)
            logger.info(f"Found {len(all_files)} files to process")

            if not all_files:
                logger.warning("No files found to process")
                self.progress.status = IngestionStatus.COMPLETE
                self.progress.completed_at = datetime.now()
                self._notify_progress()
                return self.progress

            # Phase 2: Extract text from files
            logger.info("Extracting text from files")
            extracted_files = await self._extract_batch(all_files)

            # Phase 3: Classify documents
            self.progress.status = IngestionStatus.CLASSIFYING
            self.progress.current_phase = "Classifying documents with AI"
            self._notify_progress()

            classified_files = await self._classify_batch(extracted_files)

            # Log classification summary
            classification_summary = {}
            for file in classified_files:
                cat = file.classification or "unknown"
                classification_summary[cat] = classification_summary.get(cat, 0) + 1

            logger.info(f"✓ Classification complete: {classification_summary}")

            # Stream classification results to frontend
            self.progress.current_phase = f"Klassifiziert: {len(classified_files)} Dokumente"
            self._notify_progress()

            # Phase 3.5: INTELLIGENT EXTRACTION (NEW!)
            # Extract structured data using deployment context
            if deployment_context and self.intelligent_extractor:
                logger.info("🧠 Starting intelligent data extraction")

                self.progress.status = IngestionStatus.PROCESSING
                self.progress.current_phase = "Intelligent data extraction"
                self._notify_progress()

                # Extract structured data from all classified files
                all_extracted = {
                    "products": [],
                    "syndication_products": [],
                    "data_quality": []
                }

                for i, file_info in enumerate(classified_files, 1):
                    if not file_info.extracted_text:
                        continue

                    # Stream progress
                    self.progress.current_file = file_info.name
                    self.progress.current_phase = f"📊 Extrahiere Struktur: {file_info.name} ({i}/{len(classified_files)})"
                    self._notify_progress()

                    try:
                        # Claude extracts structured fields per deployment rules
                        extracted = await self.intelligent_extractor.extract_to_standard_schema(
                            file_content=file_info.extracted_text,
                            deployment_context=deployment_context,
                            classification=file_info.classification,
                            filename=file_info.name
                        )

                        # Merge records
                        for table_name in all_extracted.keys():
                            if table_name in extracted:
                                all_extracted[table_name].extend(extracted[table_name])

                        if extracted.get("products"):
                            logger.info(f"  ✓ Extracted {len(extracted['products'])} products from {file_info.name}")

                    except Exception as e:
                        logger.error(f"  ✗ Extraction failed for {file_info.name}: {e}")
                        continue

                # Save to standard tables
                if all_extracted["products"]:
                    logger.info(f"💾 Saving {len(all_extracted['products'])} products to standard schema")

                    try:
                        # Save to Delta tables
                        await self.multi_table_loader.upsert_products(all_extracted["products"])
                        await self.multi_table_loader.upsert_syndication_products(all_extracted["syndication_products"])
                        await self.multi_table_loader.upsert_data_quality(all_extracted["data_quality"])

                        logger.info("✅ Standard tables created with structured data")

                        # Add to progress stats
                        self.progress.stats_by_mcp["products_extracted"] = len(all_extracted["products"])

                    except Exception as e:
                        logger.error(f"Failed to save extracted data: {e}", exc_info=True)

            # Phase 4: Process documents (chunk)
            self.progress.status = IngestionStatus.PROCESSING
            self._notify_progress()

            processed_docs = []
            for i, file_info in enumerate(classified_files):
                self.progress.current_file = file_info.name
                self.progress.current_phase = f"Processing ({i+1}/{len(classified_files)})"
                self._notify_progress()

                try:
                    doc = await self._process_file(file_info)
                    if doc:
                        processed_docs.append(doc)
                        self.progress.processed_files += 1

                        # Update MCP stats
                        mcp = doc.get("mcp", "unknown")
                        self.progress.stats_by_mcp[mcp] = \
                            self.progress.stats_by_mcp.get(mcp, 0) + 1
                except Exception as e:
                    logger.error(f"Failed to process {file_info.path}: {e}")
                    self.progress.failed_files += 1
                    self.progress.errors.append(f"{file_info.name}: {str(e)}")

                self._notify_progress()

            # Phase 4.5: Extract entities and relationships (NEW!)
            if self.entity_extractor and self.graph_loader:
                logger.info("🕸️  Starting entity extraction for knowledge graph")
                self.progress.current_phase = "Extracting entities for knowledge graph"
                self._notify_progress()

                # Set customer_id in graph loader
                if customer_id:
                    self.graph_loader.customer_id = customer_id

                total_entities = 0
                total_relationships = 0

                for i, doc in enumerate(processed_docs, 1):
                    self.progress.current_file = doc.get("filename", "unknown")
                    self.progress.current_phase = f"📊 Graph extraction ({i}/{len(processed_docs)})"
                    self._notify_progress()

                    try:
                        # Extract entities and relationships from document text
                        full_text = doc.get("text", "")
                        if not full_text:
                            continue

                        entities, relationships = self.entity_extractor.extract(
                            text=full_text,
                            doc_id=doc.get("id"),
                            extract_relationships=True
                        )

                        # Load to Neo4j
                        if entities:
                            stats = self.graph_loader.load_entities_from_extraction(
                                doc_id=doc.get("id"),
                                filename=doc.get("filename"),
                                mcp=doc.get("mcp", "general"),
                                entities=[e.to_dict() for e in entities],
                                relationships=[r.to_dict() for r in relationships]
                            )

                            total_entities += stats["entities"]
                            total_relationships += stats["relationships"]

                            logger.info(f"  ✓ Loaded {stats['entities']} entities, {stats['relationships']} relationships")

                    except Exception as e:
                        logger.error(f"  ✗ Entity extraction failed for {doc.get('filename')}: {e}")
                        continue

                logger.info(f"✅ Graph extraction complete: {total_entities} entities, {total_relationships} relationships")
                self.progress.stats_by_mcp["graph_entities"] = total_entities
                self.progress.stats_by_mcp["graph_relationships"] = total_relationships

            # Phase 5: Generate embeddings
            self.progress.status = IngestionStatus.EMBEDDING
            self.progress.current_phase = "Generating embeddings"
            self._notify_progress()

            embedded_docs = await self._embed_batch(processed_docs)

            # Phase 6: Load to lakehouse
            self.progress.status = IngestionStatus.LOADING
            self.progress.current_phase = "Loading to lakehouse"
            self._notify_progress()

            await self._load_to_lakehouse(embedded_docs)

            # Complete
            self.progress.status = IngestionStatus.COMPLETE
            self.progress.completed_at = datetime.now()
            self.progress.current_file = None
            self.progress.current_phase = "Complete"

            logger.info(
                f"Ingestion complete: {self.progress.processed_files} files, "
                f"{self.progress.failed_files} failures"
            )

        except Exception as e:
            logger.error(f"Ingestion failed: {e}", exc_info=True)
            self.progress.status = IngestionStatus.FAILED
            self.progress.errors.append(str(e))

        self._notify_progress()
        return self.progress

    async def _crawl_folders(self, folders: List[FolderConfig]) -> List[FileInfo]:
        """Crawl all configured folders"""
        all_files = []

        for folder_config in folders:
            self.progress.current_phase = f"Scanning {folder_config.path.name}"
            self._notify_progress()

            files = await self.crawler.crawl(
                folder_config.path,
                recursive=folder_config.recursive
            )

            # Tag files with their assigned MCP
            for f in files:
                f.assigned_mcp = folder_config.mcp_assignment

            all_files.extend(files)

        return all_files

    async def _extract_batch(self, files: List[FileInfo]) -> List[FileInfo]:
        """Extract text from all files"""
        logger.info(f"Extracting text from {len(files)} files")

        def progress_cb(file_info: FileInfo):
            self.progress.current_file = file_info.name
            self._notify_progress()

        return await self.crawler.extract_batch(
            files,
            max_concurrent=self.max_workers,
            progress_callback=progress_cb
        )

    async def _classify_batch(self, files: List[FileInfo]) -> List[FileInfo]:
        """Classify documents with real-time streaming"""
        logger.info(f"Classifying {len(files)} documents with AI")

        for i, file_info in enumerate(files, 1):
            # Stream current file being classified
            self.progress.current_file = file_info.name
            self.progress.current_phase = f"🤖 Claude analysiert: {file_info.name} ({i}/{len(files)})"
            self._notify_progress()

            # Classify using extracted text or fallback to rule-based
            classification = await self.classifier.classify(
                file_info.path,
                content_sample=file_info.extracted_text,
                assigned_mcp=file_info.assigned_mcp
            )
            file_info.classification = classification

            # Stream classification result
            logger.info(f"  ✓ {file_info.name} → {classification}")

        return files

    async def _process_file(self, file_info: FileInfo) -> Optional[dict]:
        """Process a single file through the pipeline"""
        # Skip files without extracted text
        if not file_info.extracted_text:
            return None

        text = file_info.extracted_text

        # Extract structured metadata using Claude (if available)
        enhanced_metadata = await self._extract_metadata_with_claude(file_info, text)

        # Chunk text
        chunks = self.chunker.chunk(text, file_info.extension)

        if not chunks:
            return None

        return {
            "id": str(file_info.path),
            "path": str(file_info.path),
            "filename": file_info.name,
            "mcp": file_info.classification,
            "text": text,
            "chunks": chunks,
            "metadata": {
                "size": file_info.size_bytes,
                "modified": file_info.modified.isoformat(),
                "mime_type": file_info.mime_type,
                "extension": file_info.extension,
                **enhanced_metadata  # Add Claude-extracted metadata
            }
        }

    async def _extract_metadata_with_claude(self, file_info: FileInfo, text: str) -> dict:
        """
        Use Claude to extract structured metadata from document.

        Args:
            file_info: File information
            text: Extracted text content

        Returns:
            Dictionary of extracted metadata fields
        """
        # Only use Claude if API key is available
        if not self.classifier.claude_client:
            return {}

        try:
            sample = text[:3000]  # First 3K chars

            prompt = f"""Extract key metadata from this business document.

Filename: {file_info.name}
Type: {file_info.classification}

Content:
{sample}

Extract and return ONLY a JSON object with these fields (use null if not found):
- document_type: (invoice, datasheet, catalog, spec, contract, etc)
- key_entities: (list of important entities: product IDs, company names, etc)
- date: (any date mentioned in ISO format)
- language: (de, en, etc)
- summary: (one sentence describing the document)

Respond with ONLY valid JSON, nothing else."""

            response = self.classifier.claude_client.messages.create(
                model="claude-haiku-3-5-20250514",
                max_tokens=200,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}]
            )

            import json
            metadata_json = response.content[0].text.strip()
            # Remove markdown code blocks if present
            if metadata_json.startswith("```"):
                metadata_json = metadata_json.split("```")[1]
                if metadata_json.startswith("json"):
                    metadata_json = metadata_json[4:]
                metadata_json = metadata_json.strip()

            metadata = json.loads(metadata_json)
            logger.debug(f"Extracted metadata for {file_info.name}: {metadata}")
            return metadata

        except Exception as e:
            logger.warning(f"Metadata extraction failed for {file_info.name}: {e}")
            return {}

    async def _embed_batch(self, docs: List[dict]) -> List[dict]:
        """Generate embeddings for all chunks"""
        if not docs:
            return []

        logger.info(f"Generating embeddings for {len(docs)} documents")

        # Collect all chunks with IDs
        all_chunks = []
        chunk_to_doc = {}

        for doc in docs:
            for i, chunk in enumerate(doc["chunks"]):
                chunk_id = f"{doc['id']}_{i}"
                all_chunks.append({"id": chunk_id, "text": chunk})
                chunk_to_doc[chunk_id] = doc["id"]

        logger.info(f"Total chunks to embed: {len(all_chunks)}")

        # Batch embed
        texts = [c["text"] for c in all_chunks]
        embeddings = await self.embedder.embed_batch(
            texts,
            batch_size=self.batch_size,
            show_progress=True
        )

        # Attach embeddings back to documents
        embedding_map = {
            all_chunks[i]["id"]: emb
            for i, emb in enumerate(embeddings)
        }

        for doc in docs:
            doc["chunk_embeddings"] = []
            for i in range(len(doc["chunks"])):
                chunk_id = f"{doc['id']}_{i}"
                doc["chunk_embeddings"].append(embedding_map.get(chunk_id))

        return docs

    async def _load_to_lakehouse(self, docs: List[dict]):
        """Load processed documents to Delta tables and Lance indices"""
        if not docs:
            return

        logger.info(f"Loading {len(docs)} documents to lakehouse")

        # Group by MCP
        by_mcp = {}
        for doc in docs:
            mcp = doc["mcp"]
            if mcp not in by_mcp:
                by_mcp[mcp] = []
            by_mcp[mcp].append(doc)

        # Load to Delta tables (structured data)
        for mcp, mcp_docs in by_mcp.items():
            logger.info(f"Loading {len(mcp_docs)} documents to {mcp} Delta table")
            await self.delta_loader.load_documents(mcp, mcp_docs)

        # Load to Lance (vector index)
        logger.info(f"Loading embeddings to Lance")
        await self.lance_loader.load_embeddings(docs)

        logger.info(f"Successfully loaded {len(docs)} documents to lakehouse")

    def get_statistics(self) -> dict:
        """Get detailed ingestion statistics"""
        return {
            "progress": self.progress.to_dict(),
            "crawler_stats": self.crawler.get_statistics(
                []  # Would need to store files list
            ),
            "unknown_formats": list(self.crawler.get_unknown_formats())
        }

    async def _read_deployment_context(self, customer_id: str) -> Optional[Dict]:
        """
        Read DEPLOYMENT.md for customer to get transformation rules.

        Args:
            customer_id: Customer ID

        Returns:
            Dict with deployment context or None if not found
        """
        try:
            # Find deployment directory
            deployment_dir = Path(f"/home/christoph.bertsch/0711/deployments/{customer_id}")
            deployment_md = deployment_dir / "DEPLOYMENT.md"

            if not deployment_md.exists():
                logger.warning(f"DEPLOYMENT.md not found for customer {customer_id}")
                return None

            # Read deployment markdown
            with open(deployment_md, 'r', encoding='utf-8') as f:
                deployment_content = f.read()

            # Parse key information from DEPLOYMENT.md
            context = {
                "customer_id": customer_id,
                "deployment_content": deployment_content,  # Full content for Claude
            }

            # Extract company name (line starts with "**Company Name**:")
            import re
            company_match = re.search(r'\*\*Company Name\*\*:\s*`?([^`\n]+)', deployment_content)
            if company_match:
                context["company_name"] = company_match.group(1).strip()

            # Extract industry
            industry_match = re.search(r'\*\*Industry\*\*:\s*([^\n]+)', deployment_content)
            if industry_match:
                context["industry"] = industry_match.group(1).strip()

            # Extract source format
            format_match = re.search(r'\*\*Source Format\*\*:\s*([^\n]+)', deployment_content)
            if format_match:
                context["source_format"] = format_match.group(1).strip()

            # Extract transformation rules section (full ingestion instructions)
            rules_match = re.search(
                r'## 📥 Ingestion Instructions for Claude.*?(?=##|$)',
                deployment_content,
                re.DOTALL
            )
            if rules_match:
                context["transformation_rules"] = rules_match.group(0)
            else:
                context["transformation_rules"] = {}

            logger.info(f"✓ Loaded deployment context for {customer_id}")
            return context

        except Exception as e:
            logger.error(f"Failed to read deployment context for {customer_id}: {e}")
            return None


# CLI entry point
async def main():
    """Main entry point for CLI"""
    import argparse
    import os

    parser = argparse.ArgumentParser(description="0711 Platform Ingestion")
    parser.add_argument("folders", nargs="+", help="Folders to ingest")
    parser.add_argument("--mcp", default="general", help="MCP assignment")
    parser.add_argument("--lakehouse", default="/app/lakehouse", help="Lakehouse path")
    parser.add_argument("--vllm-url", default="http://localhost:8001", help="vLLM URL")
    parser.add_argument(
        "--claude-key",
        default=os.getenv("ANTHROPIC_API_KEY"),
        help="Claude API key"
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create folder configs
    folder_configs = [
        FolderConfig(path=Path(folder), mcp_assignment=args.mcp)
        for folder in args.folders
    ]

    # Create orchestrator
    orchestrator = IngestionOrchestrator(
        lakehouse_path=Path(args.lakehouse),
        vllm_url=args.vllm_url,
        claude_api_key=args.claude_key
    )

    # Progress callback
    def print_progress(progress: IngestionProgress):
        print(
            f"[{progress.status.value}] "
            f"{progress.progress_percent:.1f}% - "
            f"{progress.current_phase}"
        )

    orchestrator.on_progress(print_progress)

    # Run ingestion
    print(f"\n🚀 Starting ingestion of {len(folder_configs)} folders...\n")
    result = await orchestrator.ingest(folder_configs)

    # Print summary
    print("\n" + "="*60)
    print("📊 Ingestion Summary")
    print("="*60)
    print(f"Status: {result.status.value}")
    print(f"Total files: {result.total_files}")
    print(f"Processed: {result.processed_files}")
    print(f"Failed: {result.failed_files}")
    print(f"Duration: {(result.completed_at - result.started_at).total_seconds():.1f}s")
    print("\nDocuments by MCP:")
    for mcp, count in result.stats_by_mcp.items():
        print(f"  {mcp}: {count}")

    if result.errors:
        print(f"\n⚠️  Errors ({len(result.errors)}):")
        for error in result.errors[:5]:
            print(f"  - {error}")


if __name__ == "__main__":
    asyncio.run(main())
