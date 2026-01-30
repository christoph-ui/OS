"""
Standard Lakehouse Schemas - Pydantic Models

Defines standard table schemas that ALL customers use.
All ingestion must transform source data into these tables.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime


class GeneralDocumentRecord(BaseModel):
    """
    General documents table - Created for EVERY ingested file.

    This is the central registry of all documents across all MCPs.
    """
    id: str = Field(..., description="Unique document ID (usually file path)")
    filename: str = Field(..., description="Original filename")
    filepath: Optional[str] = Field(None, description="Original path")
    mcp: str = Field(..., description="Assigned MCP (tax, legal, products, etc.)")
    category: Optional[str] = Field(None, description="Sub-category")
    text: str = Field(..., description="Full extracted text content")
    chunk_count: int = Field(0, description="Number of chunks created")
    size_bytes: int = Field(..., description="File size")
    mime_type: Optional[str] = Field(None, description="MIME type")
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    modified_at: Optional[datetime] = Field(None, description="Source file modification time")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Flexible metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "/path/to/product_8750001291.json",
                "filename": "product_8750001291.json",
                "mcp": "products",
                "text": "Product data...",
                "chunk_count": 24,
                "size_bytes": 35015
            }
        }


class GeneralChunkRecord(BaseModel):
    """
    General chunks table - Text chunks for vector search.

    Created for all documents to enable semantic search.
    """
    id: str = Field(..., description="Unique chunk ID")
    document_id: str = Field(..., description="FK to general_documents")
    chunk_index: int = Field(..., description="Position in document (0-based)")
    text: str = Field(..., description="Chunk text content")
    embedding_id: Optional[str] = Field(None, description="Link to Lance vector")
    tokens: Optional[int] = Field(None, description="Token count")
    mcp: str = Field(..., description="Inherited from document")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProductRecord(BaseModel):
    """
    Products table - Structured product catalog.

    Standard schema ALL customers use for product data.
    UI expects these exact fields.
    """
    gtin: str = Field(..., description="Global Trade Item Number (primary key)")
    supplier_pid: str = Field(..., description="Supplier product ID")
    manufacturer_pid: Optional[str] = Field(None, description="Manufacturer product ID")
    brand: str = Field(..., description="Brand name")
    product_name: str = Field(..., description="Product name/title")
    short_description: Optional[str] = Field(None, description="Short description")
    long_description: Optional[str] = Field(None, description="Long description")
    price: Optional[Decimal] = Field(None, description="List price")
    currency: str = Field(default="EUR", description="Currency code")
    etim_class: Optional[str] = Field(None, description="ETIM classification code")
    eclass_id: Optional[str] = Field(None, description="ECLASS classification")
    manufacturer_name: Optional[str] = Field(None, description="Manufacturer name")
    product_type: Optional[str] = Field(None, description="Product type/category")
    status: str = Field(default="active", description="active, discontinued")
    source_document_id: Optional[str] = Field(None, description="FK to general_documents")
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Full source JSON")

    @field_validator('price', mode='before')
    @classmethod
    def convert_price(cls, v):
        """Convert price to Decimal"""
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        if isinstance(v, str):
            return Decimal(v)
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "gtin": "4062321283001",
                "supplier_pid": "8750001291",
                "brand": "Bosch",
                "product_name": "CS7000iAW 7 IR-S",
                "price": 43.00,
                "currency": "EUR",
                "etim_class": "EC001764",
                "eclass_id": "27-24-11-01",
                "manufacturer_name": "Bosch Thermotechnik GmbH",
                "product_type": "Luftwärmepumpe",
                "status": "active"
            }
        }


class SyndicationProductRecord(BaseModel):
    """
    Syndication products table - Export-ready product data.

    Formatted for BMEcat/ETIM/ECLASS export and syndication.
    """
    id: str = Field(..., description="Usually GTIN")
    gtin: str = Field(..., description="Global Trade Item Number")
    supplier_pid: str = Field(..., description="Supplier product ID")
    product_name: str = Field(..., description="Product name")
    description: str = Field(..., description="Full product description")
    price: Optional[Decimal] = Field(None, description="List price")
    currency: str = Field(default="EUR", description="Currency code")
    etim_class: Optional[str] = Field(None, description="ETIM classification")
    eclass_id: Optional[str] = Field(None, description="ECLASS classification")
    manufacturer: str = Field(..., description="Manufacturer name")
    brand: str = Field(..., description="Brand name")
    images: List[Dict] = Field(default_factory=list, description="Array of image URLs/metadata")
    cad_files: List[Dict] = Field(default_factory=list, description="Array of CAD file URLs/metadata")
    technical_specs: Dict = Field(default_factory=dict, description="Structured technical specs")
    compliance_data: Dict = Field(default_factory=dict, description="Certifications, regulations")
    bmecat_ready: bool = Field(default=False, description="Ready for BMEcat export")
    etim_compliant: bool = Field(default=False, description="ETIM format compliant")
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    @field_validator('price', mode='before')
    @classmethod
    def convert_price(cls, v):
        """Convert price to Decimal"""
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        if isinstance(v, str):
            return Decimal(v)
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "4062321283001",
                "gtin": "4062321283001",
                "supplier_pid": "8750001291",
                "product_name": "CS7000iAW 7 IR-S",
                "description": "Bosch heat pump...",
                "price": 43.00,
                "etim_class": "EC001764",
                "manufacturer": "Bosch Thermotechnik GmbH",
                "brand": "Bosch",
                "bmecat_ready": True,
                "etim_compliant": True
            }
        }


class DataQualityAuditRecord(BaseModel):
    """
    Data quality audit table - Track data completeness and quality.

    Tracks which fields came from which sources and confidence levels.
    """
    document_id: str = Field(..., description="FK to general_documents")
    completeness_percentage: int = Field(..., ge=0, le=100, description="0-100%")
    data_sources: Dict[str, int] = Field(
        default_factory=dict,
        description="Source breakdown (from_database: 25, estimated: 12, ...)"
    )
    confidence_levels: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Fields by confidence (high: [...], medium: [...], low: [...])"
    )
    extraction_notes: List[str] = Field(
        default_factory=list,
        description="Processing notes"
    )
    validation_errors: List[str] = Field(
        default_factory=list,
        description="Any issues found during extraction"
    )
    verified: bool = Field(default=False, description="Human verified")
    verified_by: Optional[str] = Field(None, description="User who verified")
    verified_at: Optional[datetime] = Field(None, description="When verified")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc_123",
                "completeness_percentage": 75,
                "data_sources": {
                    "from_database": 25,
                    "from_datasheet": 55,
                    "estimated": 12
                },
                "confidence_levels": {
                    "high": ["gtin", "brand", "price"],
                    "medium": ["refrigerant_type"],
                    "low": ["exact_weight"]
                },
                "extraction_notes": ["Product data extracted from PostgreSQL database"]
            }
        }
