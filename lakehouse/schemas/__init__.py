"""
Standard Lakehouse Schemas

Pydantic models for all standard tables that ingestion must create.
These schemas are the contract between ingestion and the lakehouse.
"""

from .standard import (
    ProductRecord,
    SyndicationProductRecord,
    DataQualityAuditRecord,
    GeneralDocumentRecord,
    GeneralChunkRecord,
)

__all__ = [
    "ProductRecord",
    "SyndicationProductRecord",
    "DataQualityAuditRecord",
    "GeneralDocumentRecord",
    "GeneralChunkRecord",
]
