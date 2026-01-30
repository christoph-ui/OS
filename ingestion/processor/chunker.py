"""
Smart Chunker - Intelligent text chunking for RAG

Respects document structure (paragraphs, sentences, code blocks, tables)
and maintains semantic coherence.
"""

import re
from typing import List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ChunkConfig:
    """Configuration for text chunking"""
    max_chunk_size: int = 1000  # Maximum characters per chunk
    min_chunk_size: int = 100   # Minimum characters per chunk
    overlap: int = 100          # Character overlap between chunks
    respect_sentences: bool = True    # Don't split mid-sentence
    respect_paragraphs: bool = True   # Prefer paragraph boundaries


class SmartChunker:
    """
    Intelligent text chunking that respects document structure.

    Strategies:
    - Respects paragraph boundaries (double newlines)
    - Keeps sentences together
    - Handles different document types (prose, code, tables)
    - Maintains context with overlapping chunks
    """

    def __init__(self, config: Optional[ChunkConfig] = None):
        """
        Args:
            config: Chunking configuration
        """
        self.config = config or ChunkConfig()

    def chunk(self, text: str, file_type: str = ".txt") -> List[str]:
        """
        Chunk text into semantically meaningful pieces.

        Args:
            text: Input text
            file_type: File extension for type-specific handling

        Returns:
            List of text chunks
        """
        if not text or len(text.strip()) < self.config.min_chunk_size:
            return [text.strip()] if text.strip() else []

        # Clean text first
        text = self._clean_text(text)

        # Handle different document types
        if file_type in ['.csv', '.tsv', '.xlsx', '.xls']:
            return self._chunk_tabular(text)
        elif file_type in ['.py', '.js', '.ts', '.java', '.cpp', '.c']:
            return self._chunk_code(text)
        elif file_type in ['.json', '.xml', '.html']:
            return self._chunk_structured(text)
        else:
            return self._chunk_prose(text)

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 consecutive newlines
        text = re.sub(r'[ \t]+', ' ', text)     # Collapse spaces/tabs
        text = re.sub(r' ?\n ?', '\n', text)    # Clean around newlines

        return text.strip()

    def _chunk_prose(self, text: str) -> List[str]:
        """
        Chunk prose text respecting paragraphs and sentences.

        Strategy:
        1. Split into paragraphs
        2. Group paragraphs into chunks
        3. If paragraph too long, split by sentences
        4. Add overlap between chunks
        """
        chunks = []
        current_chunk = []
        current_size = 0

        # Split into paragraphs (double newline or more)
        paragraphs = re.split(r'\n\s*\n', text)

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_size = len(para)

            # If paragraph fits in current chunk
            if current_size + para_size + 2 <= self.config.max_chunk_size:
                current_chunk.append(para)
                current_size += para_size + 2  # +2 for paragraph separator

            # If paragraph is too large, split by sentences
            elif para_size > self.config.max_chunk_size:
                # Save current chunk first
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = []
                    current_size = 0

                # Split paragraph into sentences and chunk
                sentences = self._split_sentences(para)
                for sentence in sentences:
                    sent_size = len(sentence)

                    if current_size + sent_size + 1 <= self.config.max_chunk_size:
                        current_chunk.append(sentence)
                        current_size += sent_size + 1
                    else:
                        if current_chunk:
                            chunks.append(" ".join(current_chunk))

                        # Start new chunk with overlap
                        overlap_text = current_chunk[-1] if current_chunk else ""
                        if len(overlap_text) > self.config.overlap:
                            overlap_text = overlap_text[-self.config.overlap:]

                        current_chunk = [overlap_text, sentence] if overlap_text else [sentence]
                        current_size = len(overlap_text) + sent_size + 1

            # Start new chunk with current paragraph
            else:
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))

                # Add overlap from last paragraph
                overlap_text = current_chunk[-1] if current_chunk else ""
                if len(overlap_text) > self.config.overlap:
                    # Take last N characters for overlap
                    overlap_text = overlap_text[-self.config.overlap:]

                current_chunk = [overlap_text, para] if overlap_text else [para]
                current_size = len(overlap_text) + para_size + 2

        # Don't forget last chunk
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        # Filter out too-small chunks (except if it's the only one)
        if len(chunks) > 1:
            chunks = [c for c in chunks if len(c) >= self.config.min_chunk_size]

        return chunks

    def _chunk_tabular(self, text: str) -> List[str]:
        """
        Chunk tabular data keeping rows together.

        Strategy:
        - Keep header with each chunk
        - Group rows into appropriately-sized chunks
        """
        lines = text.split('\n')
        if not lines:
            return []

        chunks = []
        current_chunk = []
        current_size = 0

        # Identify header (first line, or lines before data rows)
        header_line = lines[0] if lines else ""
        header_size = len(header_line) + 1

        # Process data rows
        for i, line in enumerate(lines):
            line_size = len(line) + 1

            # If this is first line (header), always include
            if i == 0:
                current_chunk.append(line)
                current_size = line_size
                continue

            # If line fits in current chunk
            if current_size + line_size <= self.config.max_chunk_size:
                current_chunk.append(line)
                current_size += line_size

            # Start new chunk
            else:
                if current_chunk:
                    chunks.append("\n".join(current_chunk))

                # Start new chunk with header
                current_chunk = [header_line, line]
                current_size = header_size + line_size

        # Last chunk
        if current_chunk and len(current_chunk) > 1:  # Must have more than just header
            chunks.append("\n".join(current_chunk))

        return chunks

    def _chunk_code(self, text: str) -> List[str]:
        """
        Chunk code respecting function/class boundaries.

        Strategy:
        - Split on function/class definitions
        - Keep related code together
        """
        chunks = []
        current_chunk = []
        current_size = 0

        lines = text.split('\n')

        # Patterns for function/class definitions
        definition_patterns = [
            r'^\s*(def |class |function |const |let |var |public |private )',
            r'^\s*@\w+',  # Decorators
        ]

        for i, line in enumerate(lines):
            line_size = len(line) + 1

            # Check if this is a definition
            is_definition = any(
                re.match(pattern, line)
                for pattern in definition_patterns
            )

            # If definition and current chunk has content, start new chunk
            if is_definition and current_chunk and current_size > self.config.min_chunk_size:
                chunks.append("\n".join(current_chunk))
                current_chunk = [line]
                current_size = line_size

            # If line fits in current chunk
            elif current_size + line_size <= self.config.max_chunk_size:
                current_chunk.append(line)
                current_size += line_size

            # Start new chunk
            else:
                if current_chunk:
                    chunks.append("\n".join(current_chunk))
                current_chunk = [line]
                current_size = line_size

        # Last chunk
        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks

    def _chunk_structured(self, text: str) -> List[str]:
        """
        Chunk structured data (JSON, XML) respecting hierarchy.

        Simple strategy: chunk by lines, try to keep objects/elements together.
        """
        # For now, use line-based chunking
        # Could be enhanced to parse structure and chunk by elements

        lines = text.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0

        for line in lines:
            line_size = len(line) + 1

            if current_size + line_size <= self.config.max_chunk_size:
                current_chunk.append(line)
                current_size += line_size
            else:
                if current_chunk:
                    chunks.append("\n".join(current_chunk))
                current_chunk = [line]
                current_size = line_size

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks

    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.

        Handles German and English sentence boundaries.
        """
        # Pattern for sentence boundaries
        # Matches period/exclamation/question followed by space and capital letter
        pattern = r'(?<=[.!?])\s+(?=[A-ZÄÖÜ])'

        sentences = re.split(pattern, text)
        return [s.strip() for s in sentences if s.strip()]

    def chunk_with_metadata(
        self,
        text: str,
        file_type: str = ".txt",
        document_id: Optional[str] = None
    ) -> List[dict]:
        """
        Chunk text and return chunks with metadata.

        Args:
            text: Input text
            file_type: File extension
            document_id: Optional document identifier

        Returns:
            List of dicts with 'text', 'chunk_index', 'document_id'
        """
        chunks = self.chunk(text, file_type)

        return [
            {
                'text': chunk,
                'chunk_index': i,
                'document_id': document_id,
                'char_count': len(chunk),
                'word_count': len(chunk.split())
            }
            for i, chunk in enumerate(chunks)
        ]

    def estimate_chunk_count(self, text: str, file_type: str = ".txt") -> int:
        """
        Estimate number of chunks without actually chunking.

        Useful for progress estimation.
        """
        text_length = len(text)
        avg_chunk_size = (self.config.max_chunk_size + self.config.min_chunk_size) // 2
        estimated = max(1, text_length // avg_chunk_size)
        return estimated
