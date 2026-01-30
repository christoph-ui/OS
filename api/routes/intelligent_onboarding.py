"""
Intelligent Onboarding API Routes
Zero-config onboarding with AI-powered data discovery

"Dump your data. We figure out the rest."
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import uuid4
import logging
import os
import json

from ..database import get_db
from ..services.intelligent_onboarding_service import (
    IntelligentOnboardingService,
    DataDiscoveryReport,
    get_intelligent_onboarding_service
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/smart-onboarding", tags=["smart-onboarding"])


# ============================================================================
# SCHEMAS
# ============================================================================

class AnalysisStatusResponse(BaseModel):
    upload_id: str
    status: str
    progress: float
    message: str


class MappingAdjustment(BaseModel):
    filename: str
    mappings: Dict[str, str]


class ConfirmMappingRequest(BaseModel):
    confirmed: bool = True
    adjustments: Optional[List[MappingAdjustment]] = None


class DeployRequest(BaseModel):
    selected_connectors: Optional[List[str]] = None
    contact_email: Optional[str] = None
    contact_name: Optional[str] = None
    company_name: Optional[str] = None


# ============================================================================
# ROUTES
# ============================================================================

@router.post("/upload")
async def upload_and_analyze(
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Step 1: Upload files and start automatic analysis
    
    Upload any files (CSV, Excel, JSON, XML, etc.) and the AI will:
    - Detect file formats
    - Understand data structure
    - Identify business model
    - Recommend connectors
    - Calculate value potential
    
    Returns upload_id for tracking analysis progress.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    
    upload_id = str(uuid4())
    logger.info(f"Starting intelligent onboarding with {len(files)} files, upload_id={upload_id}")
    
    # Read file contents
    file_data = []
    for file in files:
        try:
            content = await file.read()
            file_data.append({
                "filename": file.filename,
                "content": content.decode("utf-8", errors="ignore") if len(content) < 10_000_000 else "[large file]",
                "size_bytes": len(content),
                "content_type": file.content_type
            })
        except Exception as e:
            logger.warning(f"Failed to read file {file.filename}: {e}")
            file_data.append({
                "filename": file.filename,
                "content": "",
                "size_bytes": 0,
                "error": str(e)
            })
    
    # Start analysis
    claude_api_key = os.getenv("ANTHROPIC_API_KEY")
    service = get_intelligent_onboarding_service(db, claude_api_key)
    
    try:
        await service.start_analysis(
            upload_id=upload_id,
            files=file_data
        )
        
        return {
            "success": True,
            "upload_id": upload_id,
            "files_received": len(files),
            "total_size_bytes": sum(f["size_bytes"] for f in file_data),
            "status": "analyzing",
            "message": "Ihre Daten werden analysiert. Dies dauert 1-2 Minuten."
        }
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/analysis/{upload_id}")
async def get_analysis(
    upload_id: str,
    db: Session = Depends(get_db)
):
    """
    Step 2: Get analysis results
    
    Returns comprehensive data discovery report including:
    - File analysis (formats, record counts, quality)
    - Business model detection
    - Product analysis (if applicable)
    - Connector recommendations
    - Value projection
    - Proposed field mappings
    - Human-readable summary
    """
    claude_api_key = os.getenv("ANTHROPIC_API_KEY")
    service = get_intelligent_onboarding_service(db, claude_api_key)
    
    report = service.get_analysis(upload_id)
    
    if not report:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found. Please upload files first."
        )
    
    return {
        "success": True,
        "upload_id": upload_id,
        "status": "complete",
        "report": report.to_dict()
    }


@router.get("/analysis/{upload_id}/summary")
async def get_analysis_summary(
    upload_id: str,
    db: Session = Depends(get_db)
):
    """
    Get simplified summary for UI display
    
    Returns:
    - Summary text (human-readable)
    - Key metrics
    - Top recommendations
    - Value highlights
    """
    claude_api_key = os.getenv("ANTHROPIC_API_KEY")
    service = get_intelligent_onboarding_service(db, claude_api_key)
    
    report = service.get_analysis(upload_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return {
        "success": True,
        "upload_id": upload_id,
        
        # Key metrics
        "metrics": {
            "total_files": report.total_files,
            "total_records": report.total_records,
            "total_products": report.product_analysis.total_products if report.product_analysis else 0,
            "data_quality": sum(fa.quality_score for fa in report.file_analyses) / len(report.file_analyses) if report.file_analyses else 0
        },
        
        # Business model
        "business_model": {
            "type": report.business_model.model.value,
            "confidence": report.business_model.confidence,
            "indicators": report.business_model.indicators[:3]
        },
        
        # Value
        "value": {
            "revenue_opportunity": report.value_projection.revenue_opportunity,
            "cost_savings": report.value_projection.cost_savings,
            "time_to_value": report.value_projection.time_to_value
        },
        
        # Top recommendations
        "top_recommendations": [
            {
                "connector": r.connector_name,
                "reason": r.reason,
                "value": r.estimated_value
            }
            for r in report.connector_recommendations[:3]
        ],
        
        # Summary
        "summary": report.summary_text,
        "next_steps": report.next_steps
    }


@router.get("/analysis/{upload_id}/mappings")
async def get_proposed_mappings(
    upload_id: str,
    db: Session = Depends(get_db)
):
    """
    Get proposed field mappings
    
    Returns the AI's best guess for mapping your fields to standard schemas.
    You can adjust these before confirming.
    """
    claude_api_key = os.getenv("ANTHROPIC_API_KEY")
    service = get_intelligent_onboarding_service(db, claude_api_key)
    
    report = service.get_analysis(upload_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Build mapping preview with sample data
    mappings_with_preview = {}
    
    for filename, mapping in report.proposed_mappings.items():
        # Find file analysis
        fa = next((f for f in report.file_analyses if f.filename == filename), None)
        
        mappings_with_preview[filename] = {
            "mapping": mapping,
            "unmapped_fields": [f for f in (fa.sample_fields if fa else []) if f not in mapping],
            "sample_row": fa.sample_data[0] if fa and fa.sample_data else {}
        }
    
    return {
        "success": True,
        "upload_id": upload_id,
        "mappings": mappings_with_preview,
        "target_schema": {
            "products": {
                "required": ["sku", "title"],
                "optional": ["gtin", "description", "price", "brand", "category", "images"]
            }
        }
    }


@router.post("/analysis/{upload_id}/mappings/confirm")
async def confirm_mappings(
    upload_id: str,
    request: ConfirmMappingRequest,
    db: Session = Depends(get_db)
):
    """
    Confirm or adjust field mappings
    
    After reviewing the AI's proposed mappings, confirm them or provide adjustments.
    """
    claude_api_key = os.getenv("ANTHROPIC_API_KEY")
    service = get_intelligent_onboarding_service(db, claude_api_key)
    
    # Convert adjustments to dict format
    adjustments = None
    if request.adjustments:
        adjustments = {adj.filename: adj.mappings for adj in request.adjustments}
    
    success = await service.confirm_mapping(upload_id, adjustments)
    
    if not success:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return {
        "success": True,
        "upload_id": upload_id,
        "message": "Mappings bestätigt. Bereit für den Import.",
        "next_step": "deploy"
    }


@router.get("/analysis/{upload_id}/value")
async def get_value_report(
    upload_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed value/ROI projection
    """
    claude_api_key = os.getenv("ANTHROPIC_API_KEY")
    service = get_intelligent_onboarding_service(db, claude_api_key)
    
    report = service.get_analysis(upload_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return {
        "success": True,
        "upload_id": upload_id,
        "value_projection": {
            "headline": f"💰 {report.value_projection.revenue_opportunity} Umsatzpotenzial",
            "revenue_opportunity": report.value_projection.revenue_opportunity,
            "cost_savings": report.value_projection.cost_savings,
            "time_savings": report.value_projection.time_savings,
            "time_to_value": report.value_projection.time_to_value,
            "breakdown": report.value_projection.breakdown
        },
        "recommendations": [
            {
                "connector_id": r.connector_id,
                "connector_name": r.connector_name,
                "reason": r.reason,
                "products_applicable": r.products_applicable,
                "estimated_value": r.estimated_value,
                "priority": r.priority
            }
            for r in report.connector_recommendations
        ]
    }


@router.post("/analysis/{upload_id}/deploy")
async def deploy_from_analysis(
    upload_id: str,
    request: DeployRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Step 4: Deploy based on analysis
    
    One-click deployment that:
    1. Creates customer record
    2. Imports data with confirmed mappings
    3. Activates selected connectors
    4. Starts AI learning
    5. Returns chat interface access
    """
    claude_api_key = os.getenv("ANTHROPIC_API_KEY")
    service = get_intelligent_onboarding_service(db, claude_api_key)
    
    report = service.get_analysis(upload_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # For now, return deployment info
    # In production, this would trigger actual deployment
    
    selected = request.selected_connectors or [r.connector_id for r in report.connector_recommendations[:3]]
    
    return {
        "success": True,
        "upload_id": upload_id,
        "status": "deploying",
        "message": "Ihre Daten werden importiert und die KI wird trainiert...",
        "deployment": {
            "total_files": report.total_files,
            "total_records": report.total_records,
            "connectors_activating": selected,
            "estimated_time": "5-10 Minuten"
        },
        "next_steps": [
            "Daten werden importiert",
            "KI lernt Ihre Produkte",
            "Connectors werden aktiviert",
            "Chat wird freigeschaltet"
        ]
    }


# ============================================================================
# DEMO/TEST ENDPOINTS
# ============================================================================

@router.post("/demo/analyze")
async def demo_analyze(
    db: Session = Depends(get_db)
):
    """
    Demo endpoint with sample data
    
    Tests the intelligent onboarding with sample product data.
    """
    # Sample data simulating a B2B distributor
    sample_files = [
        {
            "filename": "produktkatalog.csv",
            "content": """artikelnummer;bezeichnung;hersteller;gtin;preis;kategorie;etim_klasse
12345;Leitungsschutzschalter 3P 16A;Eaton;4015082123456;45.50;Schutzgeräte;EC001234
12346;Schütz 230V 25A;Eaton;4015082123457;89.90;Schaltgeräte;EC001235
12347;Frequenzumrichter 5.5kW;Siemens;4015082123458;1250.00;Antriebstechnik;EC001236
12348;SPS Steuerung 16DI/16DO;Siemens;4015082123459;890.00;Automatisierung;EC001237
12349;Kabelkanal 40x60mm;OBO;4015082123460;12.50;Kabelführung;EC001238""",
            "size_bytes": 500
        },
        {
            "filename": "preise_staffel.json",
            "content": json.dumps([
                {"sku": "12345", "price_1": 45.50, "price_10": 42.00, "price_100": 38.50},
                {"sku": "12346", "price_1": 89.90, "price_10": 82.00, "price_100": 75.00}
            ]),
            "size_bytes": 200
        }
    ]
    
    upload_id = str(uuid4())
    claude_api_key = os.getenv("ANTHROPIC_API_KEY")
    service = get_intelligent_onboarding_service(db, claude_api_key)
    
    await service.start_analysis(
        upload_id=upload_id,
        files=sample_files
    )
    
    report = service.get_analysis(upload_id)
    
    return {
        "success": True,
        "upload_id": upload_id,
        "demo": True,
        "summary": report.summary_text if report else "Analysis in progress",
        "report": report.to_dict() if report else None
    }
