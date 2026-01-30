"""
Product Intelligence API Routes

Provides product data analysis and connector recommendations.
This is the brain behind "upload products → instant value".
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import os
import json
import csv
import io

from ..database import get_db
from ..services.product_intelligence_service import (
    ProductIntelligenceService,
    ProductIntelligenceReport,
    get_product_intelligence_service
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/product-intelligence", tags=["product-intelligence"])


# ============================================================================
# SCHEMAS
# ============================================================================

class AnalyzeRequest(BaseModel):
    """Request to analyze products from various sources"""
    products: Optional[List[Dict[str, Any]]] = None
    sample_size: int = 1000


class ConnectorActionRequest(BaseModel):
    """Request to enable/disable connectors"""
    connector_ids: List[str]
    customer_id: Optional[str] = None


# ============================================================================
# ROUTES
# ============================================================================

@router.post("/analyze")
async def analyze_products(
    request: AnalyzeRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze product data and get intelligent recommendations.
    
    This endpoint analyzes your product data to:
    1. Detect product category (electrical, automotive, industrial, etc.)
    2. Assess data completeness
    3. Identify existing classifications (ETIM, ECLASS)
    4. Recommend relevant Connectors
    5. Calculate potential value
    
    Input: List of product dictionaries with any field structure
    Output: ProductIntelligenceReport with recommendations
    """
    if not request.products or len(request.products) == 0:
        raise HTTPException(status_code=400, detail="No products provided")
    
    claude_api_key = os.getenv("ANTHROPIC_API_KEY")
    service = get_product_intelligence_service(claude_api_key)
    
    try:
        report = await service.analyze_products(
            products=request.products,
            sample_size=request.sample_size
        )
        
        return {
            "success": True,
            "report": report.to_dict()
        }
    except Exception as e:
        logger.error(f"Product analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-file")
async def analyze_product_file(
    file: UploadFile = File(...),
    sample_size: int = 1000,
    db: Session = Depends(get_db)
):
    """
    Analyze product data from uploaded file.
    
    Supports: CSV, JSON, Excel (xlsx)
    
    Upload your product file and get instant analysis + recommendations.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    filename = file.filename.lower()
    content = await file.read()
    
    try:
        # Parse file based on format
        products = []
        
        if filename.endswith('.csv'):
            # Parse CSV
            text = content.decode('utf-8-sig')  # Handle BOM
            reader = csv.DictReader(io.StringIO(text), delimiter=';')  # German CSVs often use ;
            
            # Try comma if semicolon didn't work
            rows = list(reader)
            if rows and len(rows[0]) <= 1:
                reader = csv.DictReader(io.StringIO(text), delimiter=',')
                rows = list(reader)
            
            products = rows
        
        elif filename.endswith('.json'):
            # Parse JSON
            data = json.loads(content.decode('utf-8'))
            if isinstance(data, list):
                products = data
            elif isinstance(data, dict):
                # Check for common wrapper keys
                for key in ['products', 'items', 'data', 'records']:
                    if key in data and isinstance(data[key], list):
                        products = data[key]
                        break
                if not products:
                    products = [data]  # Single product
        
        elif filename.endswith(('.xlsx', '.xls')):
            # Parse Excel
            try:
                import pandas as pd
                df = pd.read_excel(io.BytesIO(content))
                products = df.to_dict('records')
            except ImportError:
                raise HTTPException(
                    status_code=400,
                    detail="Excel support requires pandas. Please use CSV or JSON."
                )
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format: {filename}. Use CSV, JSON, or XLSX."
            )
        
        if not products:
            raise HTTPException(status_code=400, detail="No products found in file")
        
        logger.info(f"Parsed {len(products)} products from {filename}")
        
        # Run analysis
        claude_api_key = os.getenv("ANTHROPIC_API_KEY")
        service = get_product_intelligence_service(claude_api_key)
        
        report = await service.analyze_products(
            products=products,
            sample_size=sample_size
        )
        
        return {
            "success": True,
            "filename": file.filename,
            "products_found": len(products),
            "report": report.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connector-mapping")
async def get_connector_mapping():
    """
    Get the connector mapping rules.
    
    Shows which connectors are recommended for which scenarios.
    """
    from ..services.product_intelligence_service import ProductIntelligenceService
    
    return {
        "success": True,
        "mappings": ProductIntelligenceService.CONNECTOR_MAPPINGS,
        "categories": [e.value for e in ProductIntelligenceService.ProductCategory.__class__.__mro__[0].__members__.values()],
        "description": {
            "condition_types": {
                "missing_classification": "Products don't have ETIM/ECLASS codes",
                "missing_descriptions": "Products have no or short descriptions",
                "missing_images": "Products have no images",
                "marketplace_ready": "Products have enough data for marketplaces",
                "has_prices": "Products have pricing information",
                "has_classification": "Products have classification codes",
            }
        }
    }


@router.post("/enable-connectors")
async def enable_recommended_connectors(
    request: ConnectorActionRequest,
    db: Session = Depends(get_db)
):
    """
    Enable recommended connectors for a customer.
    
    After analysis, this endpoint activates the recommended connectors
    so they're immediately available for the customer.
    """
    if not request.connector_ids:
        raise HTTPException(status_code=400, detail="No connectors specified")
    
    # In production, this would:
    # 1. Create Connection records for each connector
    # 2. Initialize connector configurations
    # 3. Start any background processing
    
    enabled = []
    for connector_id in request.connector_ids:
        # TODO: Actually create Connection records
        enabled.append({
            "connector_id": connector_id,
            "status": "enabled",
            "message": f"Connector {connector_id} enabled"
        })
    
    return {
        "success": True,
        "enabled_connectors": enabled,
        "message": f"Enabled {len(enabled)} connectors"
    }


@router.get("/quick-analysis")
async def quick_analysis_demo():
    """
    Demo endpoint showing what the analysis looks like.
    
    Returns sample analysis for testing/demo purposes.
    """
    # Sample products (electrical components)
    sample_products = [
        {
            "artikelnummer": "LS-3P-16A",
            "bezeichnung": "Leitungsschutzschalter 3P 16A C",
            "hersteller": "Eaton",
            "ean": "4015082123456",
            "vk_preis": 45.50,
            "kategorie": "Schutzgeräte",
            "etim_class": "EC001234"
        },
        {
            "artikelnummer": "SCH-230V-25A",
            "bezeichnung": "Installationsschütz 230V 25A",
            "hersteller": "Eaton",
            "ean": "4015082123457",
            "vk_preis": 89.90,
            "kategorie": "Schaltgeräte"
        },
        {
            "artikelnummer": "FU-5.5KW",
            "bezeichnung": "Frequenzumrichter 5.5kW",
            "hersteller": "Siemens",
            "ean": "4015082123458",
            "vk_preis": 1250.00,
            "kategorie": "Antriebstechnik"
        },
    ] * 100  # Simulate 300 products
    
    claude_api_key = os.getenv("ANTHROPIC_API_KEY")
    service = get_product_intelligence_service(claude_api_key)
    
    report = await service.analyze_products(
        products=sample_products,
        sample_size=100
    )
    
    return {
        "success": True,
        "demo": True,
        "message": "This is a demo analysis with sample electrical products",
        "report": report.to_dict()
    }
