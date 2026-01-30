"""
Claude Schema Analyzer - Intelligent data structure detection

Analyzes file content to determine optimal storage strategy:
- Structured data → SQL tables (Delta Lake)
- Entities & relationships → Graph (Neo4j)
- Searchable content → Vector indices (LanceDB)
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class DataType(str, Enum):
    """Type of data detected"""
    STRUCTURED_CATALOG = "structured_catalog"  # Product catalogs, price lists
    STRUCTURED_DOCS = "structured_documents"  # Contracts, invoices with fields
    UNSTRUCTURED_TEXT = "unstructured_text"  # PDFs, Word docs
    MIXED = "mixed"  # Combination


@dataclass
class TableSchema:
    """SQL table schema"""
    name: str
    description: str
    columns: List[Dict[str, str]]  # [{name, type, description}]
    primary_key: Optional[str] = None
    foreign_keys: List[Dict[str, str]] = field(default_factory=list)
    json_path: Optional[str] = None  # JSON path to extract data from


@dataclass
class GraphSchema:
    """Graph database schema"""
    nodes: List[Dict[str, Any]]  # [{type, properties, id_field}]
    relationships: List[Dict[str, str]]  # [{from, to, type, properties}]


@dataclass
class VectorIndex:
    """Vector search index"""
    name: str
    fields: List[str]  # JSON paths to index
    description: str


@dataclass
class StorageStrategy:
    """Complete storage strategy for a file"""
    data_type: DataType
    sql_tables: List[TableSchema] = field(default_factory=list)
    graph_schema: Optional[GraphSchema] = None
    vector_indices: List[VectorIndex] = field(default_factory=list)
    confidence: str = "medium"  # high, medium, low


@dataclass
class DataSchema:
    """Analyzed data schema"""
    file_path: Path
    classification: str  # From DocumentClassifier
    detected_format: str  # JSON, XML, CSV, etc.
    storage_strategy: StorageStrategy
    sample_record: Optional[Dict] = None


class SchemaAnalyzer:
    """
    Analyzes data structure using Claude to determine optimal storage.

    For each file, Claude decides:
    1. Is this structured data that should go to SQL?
    2. Are there entities that should be in a graph?
    3. What text should be vector-indexed for search?
    """

    def __init__(self, claude_api_key: Optional[str] = None):
        """
        Args:
            claude_api_key: Anthropic API key for Claude
        """
        self.claude_client = None
        if claude_api_key:
            import anthropic
            self.claude_client = anthropic.Anthropic(api_key=claude_api_key)
            logger.info("✅ Claude Schema Analyzer initialized")

    async def analyze(
        self,
        file_path: Path,
        content: str,
        classification: str
    ) -> DataSchema:
        """
        Analyze file content and determine storage strategy.

        Args:
            file_path: Path to file
            content: Extracted text content
            classification: MCP classification (tax, legal, products, etc.)

        Returns:
            DataSchema with storage recommendations
        """
        # Quick format detection
        detected_format = self._detect_format(file_path, content)

        # If no Claude, use heuristic approach
        if not self.claude_client:
            return self._heuristic_analysis(file_path, content, classification, detected_format)

        # Use Claude for intelligent schema detection
        storage_strategy = await self._claude_analyze(
            file_path=file_path,
            content=content,
            classification=classification,
            detected_format=detected_format
        )

        # Extract sample record for validation
        sample_record = None
        if detected_format == "json":
            try:
                data = json.loads(content)
                sample_record = self._extract_sample(data)
            except:
                pass

        return DataSchema(
            file_path=file_path,
            classification=classification,
            detected_format=detected_format,
            storage_strategy=storage_strategy,
            sample_record=sample_record
        )

    def _detect_format(self, file_path: Path, content: str) -> str:
        """Quick format detection"""
        ext = file_path.suffix.lower()

        if ext == '.json':
            return 'json'
        elif ext in ['.xml', '.html']:
            return 'xml'
        elif ext in ['.csv', '.tsv']:
            return 'csv'
        elif ext in ['.xlsx', '.xls']:
            return 'excel'
        else:
            # Analyze content
            content_sample = content[:500].strip()
            if content_sample.startswith('{') or content_sample.startswith('['):
                return 'json'
            elif content_sample.startswith('<?xml') or content_sample.startswith('<'):
                return 'xml'
            elif '\t' in content_sample or ',' in content_sample:
                return 'delimited'
            else:
                return 'text'

    def _extract_sample(self, data: Any, max_items: int = 3) -> Dict:
        """Extract sample record from data"""
        if isinstance(data, dict):
            # If it's a single object, return first few fields
            sample = {}
            for i, (k, v) in enumerate(data.items()):
                if i >= max_items:
                    sample['...'] = f'{len(data) - max_items} more fields'
                    break
                sample[k] = v if not isinstance(v, (dict, list)) else type(v).__name__
            return sample
        elif isinstance(data, list) and len(data) > 0:
            return self._extract_sample(data[0], max_items)
        else:
            return {"sample": str(data)[:200]}

    async def _claude_analyze(
        self,
        file_path: Path,
        content: str,
        classification: str,
        detected_format: str
    ) -> StorageStrategy:
        """
        Use Claude Sonnet to analyze data structure and recommend storage strategy.
        """
        # Truncate content for analysis
        content_sample = content[:8000]  # First 8K chars

        prompt = f"""Analyze this {classification} data file and determine the optimal multi-modal storage strategy.

**File:** {file_path.name}
**Format:** {detected_format}
**Classification:** {classification}

**Content Sample:**
```{detected_format}
{content_sample}
```

**Your Task:**
Design a storage strategy that maximizes data value by routing to appropriate storage layers:

1. **SQL Tables** (Delta Lake) - For structured, queryable data
2. **Graph Database** (Neo4j) - For entity relationships
3. **Vector Search** (LanceDB) - For semantic search

**Output (JSON only, no markdown):**
{{
  "data_type": "structured_catalog|structured_documents|unstructured_text|mixed",
  "confidence": "high|medium|low",

  "sql_tables": [
    {{
      "name": "products",
      "description": "Core product catalog",
      "columns": [
        {{"name": "gtin", "type": "string", "description": "Global Trade Item Number"}},
        {{"name": "supplier_pid", "type": "string", "description": "Supplier product ID"}},
        {{"name": "brand", "type": "string"}},
        {{"name": "price", "type": "float"}},
        {{"name": "etim_class", "type": "string"}}
      ],
      "primary_key": "gtin",
      "json_path": "$.product_master_data.identifiers"
    }}
  ],

  "graph_entities": [
    {{"type": "Product", "id_field": "gtin", "properties": ["brand", "model"]}},
    {{"type": "Manufacturer", "id_field": "manufacturer_gln", "properties": ["name", "address"]}}
  ],

  "graph_relationships": [
    {{"from": "Product", "to": "Manufacturer", "type": "MANUFACTURED_BY", "from_field": "gtin", "to_field": "manufacturer_gln"}}
  ],

  "vector_indices": [
    {{"name": "product_descriptions", "fields": ["$.descriptions.short_description", "$.descriptions.long_description"]}},
    {{"name": "technical_specs", "fields": ["$.technical_specifications"]}}
  ],

  "extraction_notes": "Brief explanation of strategy"
}}

**Important:** Focus on creating queryable, structured data. Respond with ONLY valid JSON.
        response = self.claude_client.messages.create(
            model="claude-sonnet-4-5-20250929",  # Use Sonnet for complex analysis
            max_tokens=2000,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse JSON response
        response_text = response.content[0].text.strip()

        # Remove markdown if present
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
            response_text = response_text.strip()

        try:
            strategy_dict = json.loads(response_text)

            # Parse into StorageStrategy object
            sql_tables = []
            for table_def in strategy_dict.get("sql_tables", []):
                sql_tables.append(TableSchema(
                    name=table_def["name"],
                    description=table_def.get("description", ""),
                    columns=table_def.get("columns", []),
                    primary_key=table_def.get("primary_key"),
                    foreign_keys=table_def.get("foreign_keys", []),
                    json_path=table_def.get("json_path")
                ))

            graph_schema = None
            if strategy_dict.get("graph_entities"):
                graph_schema = GraphSchema(
                    nodes=strategy_dict.get("graph_entities", []),
                    relationships=strategy_dict.get("graph_relationships", [])
                )

            vector_indices = []
            for idx_def in strategy_dict.get("vector_indices", []):
                vector_indices.append(VectorIndex(
                    name=idx_def["name"],
                    fields=idx_def["fields"],
                    description=idx_def.get("description", "")
                ))

            data_type = DataType(strategy_dict.get("data_type", "mixed"))

            logger.info(f"📊 Claude analysis complete for {file_path.name}")
            logger.info(f"  Data type: {data_type}")
            logger.info(f"  SQL tables: {len(sql_tables)}")
            logger.info(f"  Graph entities: {len(graph_schema.nodes) if graph_schema else 0}")
            logger.info(f"  Vector indices: {len(vector_indices)}")

            return StorageStrategy(
                data_type=data_type,
                sql_tables=sql_tables,
                graph_schema=graph_schema,
                vector_indices=vector_indices,
                confidence=strategy_dict.get("confidence", "medium")
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude schema analysis: {e}")
            logger.debug(f"Response was: {response_text[:500]}")
            return self._heuristic_analysis(file_path, content, classification, detected_format)

        except Exception as e:
            logger.error(f"Claude schema analysis failed: {e}")
            return self._heuristic_analysis(file_path, content, classification, detected_format)

    def _heuristic_analysis(
        self,
        file_path: Path,
        content: str,
        classification: str,
        detected_format: str
    ) -> StorageStrategy:
        """
        Fallback: Rule-based schema detection without Claude.
        """
        logger.info(f"Using heuristic analysis for {file_path.name}")

        # Default strategy based on classification
        if classification == "products" and detected_format == "json":
            # Product catalogs → structured tables
            return StorageStrategy(
                data_type=DataType.STRUCTURED_CATALOG,
                sql_tables=[
                    TableSchema(
                        name="products",
                        description="Product catalog",
                        columns=[
                            {"name": "id", "type": "string"},
                            {"name": "name", "type": "string"},
                            {"name": "price", "type": "float"},
                        ],
                        primary_key="id"
                    )
                ],
                vector_indices=[
                    VectorIndex(
                        name="product_search",
                        fields=["description", "name"],
                        description="Product descriptions"
                    )
                ],
                confidence="low"
            )

        elif classification in ["tax", "legal"]:
            # Documents → vector search primarily
            return StorageStrategy(
                data_type=DataType.UNSTRUCTURED_TEXT,
                vector_indices=[
                    VectorIndex(
                        name=f"{classification}_documents",
                        fields=["full_text"],
                        description=f"{classification.title()} document search"
                    )
                ],
                confidence="low"
            )

        else:
            # Generic strategy
            return StorageStrategy(
                data_type=DataType.MIXED,
                vector_indices=[
                    VectorIndex(
                        name="general_search",
                        fields=["content"],
                        description="General document search"
                    )
                ],
                confidence="low"
            )
