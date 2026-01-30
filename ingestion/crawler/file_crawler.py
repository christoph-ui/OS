"""
File Crawler - Discovers and extracts content from files

Recursively scans folders, identifies supported files, and extracts text content.
Integrates with Claude handler generator for unknown formats.
"""

import asyncio
from pathlib import Path
from typing import List, Optional, Generator, Callable
from dataclasses import dataclass, field
from datetime import datetime
import mimetypes
import logging

from .file_handlers import get_handler, get_supported_extensions, register_custom_handler
from ..claude_handler_generator import ClaudeHandlerGenerator

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """Information about a discovered file"""
    path: Path
    name: str
    extension: str
    size_bytes: int
    modified: datetime
    mime_type: Optional[str]

    # Metadata added during processing
    assigned_mcp: Optional[str] = None
    classification: Optional[str] = None
    extracted_text: Optional[str] = None
    extraction_status: str = "pending"  # pending, success, failed, unknown_format
    extraction_error: Optional[str] = None


class FileCrawler:
    """
    Crawls folders and extracts file contents.

    Features:
    - Recursive folder scanning
    - File type filtering
    - Content extraction via handlers
    - Unknown format detection → Claude generation
    - Progress callbacks
    """

    def __init__(
        self,
        max_file_size_mb: int = 100,
        claude_api_key: Optional[str] = None,
        auto_generate_handlers: bool = True,
        customer_id: Optional[str] = None
    ):
        """
        Args:
            max_file_size_mb: Maximum file size to process
            claude_api_key: API key for Claude (handler generation)
            auto_generate_handlers: Auto-generate handlers for unknown formats
            customer_id: Customer ID for saving generated handlers to deployment
        """
        self.max_file_size = max_file_size_mb * 1024 * 1024
        self.auto_generate_handlers = auto_generate_handlers
        self.customer_id = customer_id  # Store for handler persistence

        # Claude handler generator (optional)
        self.handler_generator = None
        if claude_api_key and auto_generate_handlers:
            self.handler_generator = ClaudeHandlerGenerator(api_key=claude_api_key)

        # Track unknown formats encountered
        self.unknown_formats = set()

        # Generated handlers cache
        self._generated_handlers_cache = {}

        # Load existing generated handlers for this customer
        if customer_id:
            self._load_customer_handlers(customer_id)

    async def crawl(
        self,
        folder: Path,
        recursive: bool = True,
        max_depth: int = 20,
        progress_callback: Optional[Callable[[FileInfo], None]] = None
    ) -> List[FileInfo]:
        """
        Crawl a folder and discover all supported files.

        Args:
            folder: Root folder to crawl
            recursive: Whether to recurse into subfolders
            max_depth: Maximum recursion depth
            progress_callback: Optional callback for progress updates

        Returns:
            List of FileInfo objects for all discovered files
        """
        logger.info(f"Starting crawl of {folder}")

        files = []
        supported_exts = get_supported_extensions()

        for file_info in self._walk_files(folder, recursive, max_depth):
            # Check if we have a handler for this file
            if file_info.extension not in supported_exts:
                self.unknown_formats.add(file_info.extension)
                file_info.extraction_status = "unknown_format"

            files.append(file_info)

            # Progress callback
            if progress_callback:
                try:
                    progress_callback(file_info)
                except Exception as e:
                    logger.warning(f"Progress callback error: {e}")

        logger.info(f"Crawl complete: found {len(files)} files")

        # Report unknown formats
        if self.unknown_formats:
            logger.info(f"Unknown formats detected: {self.unknown_formats}")

        return files

    def _walk_files(
        self,
        folder: Path,
        recursive: bool,
        max_depth: int,
        current_depth: int = 0
    ) -> Generator[FileInfo, None, None]:
        """Walk folder tree and yield file info"""
        if current_depth > max_depth:
            return

        try:
            for entry in folder.iterdir():
                # Skip hidden files/folders
                if entry.name.startswith('.'):
                    continue

                if entry.is_file():
                    try:
                        stat = entry.stat()

                        # Skip files that are too large
                        if stat.st_size > self.max_file_size:
                            logger.warning(
                                f"Skipping large file: {entry} "
                                f"({stat.st_size / (1024*1024):.1f}MB)"
                            )
                            continue

                        # Create FileInfo
                        file_info = FileInfo(
                            path=entry,
                            name=entry.name,
                            extension=entry.suffix.lower(),
                            size_bytes=stat.st_size,
                            modified=datetime.fromtimestamp(stat.st_mtime),
                            mime_type=mimetypes.guess_type(str(entry))[0]
                        )

                        yield file_info

                    except (OSError, PermissionError) as e:
                        logger.warning(f"Cannot access {entry}: {e}")

                elif entry.is_dir() and recursive:
                    yield from self._walk_files(
                        entry, recursive, max_depth, current_depth + 1
                    )

        except PermissionError:
            logger.warning(f"Permission denied: {folder}")

    async def extract_text(self, file_info: FileInfo) -> Optional[str]:
        """
        Extract text content from a file.

        Attempts extraction with built-in handlers first.
        If no handler available, generates one using Claude (if enabled).

        Args:
            file_info: FileInfo object

        Returns:
            Extracted text, or None if extraction fails
        """
        try:
            # Get handler
            handler = get_handler(file_info.path)

            # No handler available
            if handler is None:
                # Try to generate handler with Claude
                if self.handler_generator and self.auto_generate_handlers:
                    handler = await self._generate_handler_for_file(file_info)

                if handler is None:
                    file_info.extraction_status = "no_handler"
                    logger.warning(f"No handler available for {file_info.path}")
                    return None

            # Extract text
            text = await handler.extract(file_info.path)

            # Update file info
            file_info.extracted_text = text
            file_info.extraction_status = "success" if text else "empty"

            return text

        except Exception as e:
            file_info.extraction_status = "failed"
            file_info.extraction_error = str(e)
            logger.error(f"Extraction failed for {file_info.path}: {e}")
            return None

    async def _generate_handler_for_file(self, file_info: FileInfo):
        """
        Generate a custom handler for an unknown file format.

        Args:
            file_info: FileInfo for the unknown file

        Returns:
            Generated handler instance, or None if generation fails
        """
        extension = file_info.extension

        # Check cache first
        if extension in self._generated_handlers_cache:
            logger.info(f"Using cached handler for {extension}")
            return self._generated_handlers_cache[extension]

        logger.info(f"Generating handler for unknown format: {extension}")

        try:
            # Generate handler code
            handler_code, handler_class = await self.handler_generator.generate_handler(
                file_path=file_info.path,
                user_hint=None  # Could be provided by user in wizard
            )

            # Import and instantiate handler
            import tempfile
            import importlib.util

            # Create temporary module
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False
            ) as f:
                # Add necessary imports
                full_code = f"""
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class BaseHandler:
    async def extract(self, path: Path) -> Optional[str]:
        raise NotImplementedError

{handler_code}
"""
                f.write(full_code)
                temp_module_path = f.name

            # Import module
            spec = importlib.util.spec_from_file_location(
                f"generated_handler_{extension.replace('.', '')}",
                temp_module_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Get handler class
            handler_class_obj = getattr(module, handler_class)
            handler = handler_class_obj()

            # Save handler code to customer deployment directory (persistent)
            if self.customer_id:
                from core.paths import CustomerPaths
                customer_handlers_dir = CustomerPaths.get_lakehouse_path(self.customer_id).parent / "generated_handlers"
                customer_handlers_dir.mkdir(exist_ok=True, parents=True)

                handler_file = customer_handlers_dir / f"{extension.replace('.', '')}_handler.py"
                with open(handler_file, 'w') as f:
                    f.write(full_code)

                logger.info(f"💾 Saved generated handler to: {handler_file}")

            # Register handler globally (for this session)
            register_custom_handler(extension, handler)

            # Cache it
            self._generated_handlers_cache[extension] = handler

            # Cleanup temp file
            Path(temp_module_path).unlink(missing_ok=True)

            logger.info(f"✅ Successfully generated and registered handler for {extension}")
            return handler

        except Exception as e:
            logger.error(f"Failed to generate handler for {extension}: {e}")
            return None

    async def extract_batch(
        self,
        files: List[FileInfo],
        max_concurrent: int = 10,
        progress_callback: Optional[Callable[[FileInfo], None]] = None
    ) -> List[FileInfo]:
        """
        Extract text from multiple files concurrently.

        Args:
            files: List of FileInfo objects
            max_concurrent: Maximum concurrent extractions
            progress_callback: Optional callback for progress updates

        Returns:
            List of FileInfo objects with extracted_text populated
        """
        logger.info(f"Starting batch extraction of {len(files)} files")

        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrent)

        async def extract_with_sem(file_info: FileInfo) -> FileInfo:
            async with semaphore:
                await self.extract_text(file_info)

                if progress_callback:
                    try:
                        progress_callback(file_info)
                    except Exception as e:
                        logger.warning(f"Progress callback error: {e}")

                return file_info

        # Extract all files concurrently (with limit)
        results = await asyncio.gather(
            *[extract_with_sem(f) for f in files],
            return_exceptions=True
        )

        # Filter out exceptions
        successful = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Extraction error: {result}")
            else:
                successful.append(result)

        logger.info(
            f"Batch extraction complete: "
            f"{len(successful)}/{len(files)} files processed"
        )

        return successful

    def get_unknown_formats(self) -> set[str]:
        """Get set of unknown file extensions encountered"""
        return self.unknown_formats.copy()

    def get_statistics(self, files: List[FileInfo]) -> dict:
        """
        Get statistics about crawled files.

        Args:
            files: List of FileInfo objects

        Returns:
            Dictionary with statistics
        """
        total = len(files)
        by_status = {}
        by_extension = {}
        total_size = 0

        for file in files:
            # Count by status
            status = file.extraction_status
            by_status[status] = by_status.get(status, 0) + 1

            # Count by extension
            ext = file.extension
            by_extension[ext] = by_extension.get(ext, 0) + 1

            # Total size
            total_size += file.size_bytes

        return {
            "total_files": total,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "by_status": by_status,
            "by_extension": by_extension,
            "unknown_formats": list(self.unknown_formats)
        }

    def _load_customer_handlers(self, customer_id: str):
        """
        Load previously generated handlers for this customer.

        Args:
            customer_id: Customer ID
        """
        try:
            from core.paths import CustomerPaths
            customer_handlers_dir = CustomerPaths.get_lakehouse_path(customer_id).parent / "generated_handlers"

            if not customer_handlers_dir.exists():
                logger.debug(f"No generated handlers directory for customer {customer_id}")
                return

            # Load all .py files in the directory
            for handler_file in customer_handlers_dir.glob("*_handler.py"):
                try:
                    # Extract extension from filename
                    extension = "." + handler_file.stem.replace("_handler", "")

                    logger.info(f"📂 Loading saved handler for {extension} from {handler_file}")

                    # Import the handler
                    import importlib.util
                    spec = importlib.util.spec_from_file_location(
                        f"customer_{customer_id}_handler_{extension.replace('.', '')}",
                        handler_file
                    )
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # Find handler class (should be only class in file besides BaseHandler)
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            attr_name != 'BaseHandler' and 
                            hasattr(attr, 'extract')):
                            handler = attr()
                            register_custom_handler(extension, handler)
                            self._generated_handlers_cache[extension] = handler
                            logger.info(f"✅ Loaded handler for {extension}")
                            break

                except Exception as e:
                    logger.warning(f"Failed to load handler from {handler_file}: {e}")

        except Exception as e:
            logger.warning(f"Failed to load customer handlers: {e}")
