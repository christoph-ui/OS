"""
Onboarding API Routes
Handles the complete onboarding flow for new customers
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

from api.database import get_db
from api.models.customer import Customer
from api.models.deployment import Deployment
from api.models.subscription import Subscription
from api.services.license_service import LicenseService
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


class CompanyInfoRequest(BaseModel):
    company_name: str
    industry: str
    company_size: str
    country: str
    goals: List[str]


class DataSourceRequest(BaseModel):
    files: List[dict]
    connectors: List[str]


class MCPSelectionRequest(BaseModel):
    selected_mcps: List[str]


class ConnectorSelectionRequest(BaseModel):
    selected_connectors: List[str]


class CompleteOnboardingRequest(BaseModel):
    company_name: str
    industry: str
    company_size: str
    country: str
    goals: List[str]
    selected_mcps: List[str]
    selected_connectors: List[str]
    contact_email: Optional[EmailStr] = None
    contact_name: Optional[str] = None


class OnboardingStatusResponse(BaseModel):
    step: str
    status: str
    message: str
    progress: float
    deployment_id: Optional[str] = None


@router.post("/company-info")
async def save_company_info(
    data: CompanyInfoRequest,
    db: Session = Depends(get_db)
):
    """
    Save company information during onboarding
    Step 2: Company Information
    """
    try:
        # In a real implementation, this would save to a temporary onboarding session
        # For now, we'll just validate and return success
        logger.info(f"Saving company info for: {data.company_name}")

        return {
            "success": True,
            "message": "Company information saved",
            "data": data.dict()
        }
    except Exception as e:
        logger.error(f"Error saving company info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/data-sources")
async def configure_data_sources(
    data: DataSourceRequest,
    db: Session = Depends(get_db)
):
    """
    Configure data sources and connectors
    Step 3: Data Upload/Configuration
    """
    try:
        logger.info(f"Configuring {len(data.files)} files and {len(data.connectors)} connectors")

        return {
            "success": True,
            "message": "Data sources configured",
            "stats": {
                "files": len(data.files),
                "connectors": len(data.connectors),
                "estimated_records": sum(f.get("records", 0) for f in data.files)
            }
        }
    except Exception as e:
        logger.error(f"Error configuring data sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mcps")
async def select_mcps(
    data: MCPSelectionRequest,
    db: Session = Depends(get_db)
):
    """
    Select MCPs for the deployment
    Step 4: MCP Selection
    """
    try:
        # Calculate pricing
        base_price = 8000  # Orchestrator base
        mcp_pricing = {
            "tender": 2500,
            "pricing": 3000,
            "pipeline": 2000,
            "etim": 2000,
            "product": 3500,
            "multichannel": 2000,
            "ctax": 3000,
            "fpa": 2500,
            "procurement": 2000,
            "law": 3000,
            "compliance": 3000,
            "research": 2500
        }

        total_mcp_cost = sum(mcp_pricing.get(mcp, 2000) for mcp in data.selected_mcps)
        total_monthly = base_price + total_mcp_cost

        logger.info(f"Selected {len(data.selected_mcps)} MCPs, total: €{total_monthly}/mo")

        return {
            "success": True,
            "message": f"{len(data.selected_mcps)} MCPs selected",
            "pricing": {
                "base": base_price,
                "mcps": total_mcp_cost,
                "total_monthly": total_monthly,
                "total_annual": total_monthly * 12 * 0.8  # 20% annual discount
            },
            "selected": data.selected_mcps
        }
    except Exception as e:
        logger.error(f"Error selecting MCPs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connectors")
async def configure_connectors(
    data: ConnectorSelectionRequest,
    db: Session = Depends(get_db)
):
    """
    Configure external system connectors
    Step 5: Connector Selection
    """
    try:
        connector_price = len(data.selected_connectors) * 400  # €400 per connector

        logger.info(f"Configured {len(data.selected_connectors)} connectors")

        return {
            "success": True,
            "message": f"{len(data.selected_connectors)} connectors configured",
            "pricing": {
                "connector_cost": connector_price,
                "connectors": data.selected_connectors
            }
        }
    except Exception as e:
        logger.error(f"Error configuring connectors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_deployment(
    customer_id: str,
    data: CompleteOnboardingRequest,
    db: Session
):
    """
    Background task to process REAL deployment
    Provisions complete per-customer stack
    """
    deployment = None
    try:
        # Real deployment code
        from provisioning.api.services.deployment_orchestrator import CustomerDeploymentOrchestrator
        # Step 1: Create customer record if needed
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer and data.contact_email:
            customer = Customer(
                id=customer_id,
                contact_email=data.contact_email,
                company_name=data.company_name,
                tier="Enterprise",  # All onboarding customers start as Enterprise
                status="active"
            )
            db.add(customer)
            db.commit()
            logger.info(f"Created customer: {data.company_name} ({customer_id})")

        # Step 2: Create deployment record
        license_key = LicenseService.generate_license_key()
        deployment = Deployment(
            customer_id=customer_id,
            license_key=license_key,
            deployment_type="managed",
            status="provisioning"
        )
        db.add(deployment)
        db.commit()
        logger.info(f"Created deployment: {deployment.id}")

        # Step 3: REAL DEPLOYMENT - Provision complete stack
        logger.info(f"🚀 Starting REAL deployment for {data.company_name}")

        orchestrator = CustomerDeploymentOrchestrator()

        deployment_result = await orchestrator.deploy_customer(
            customer_id=customer_id,
            company_name=data.company_name,
            selected_mcps=data.selected_mcps,
            uploaded_files_bucket=f"customer-{customer_id}",
            deployment_type="managed"
        )

        logger.info(f"✓ Deployment completed: {deployment_result}")

        # Step 4: Update deployment with provisioned info
        deployment.status = "active"

        # Mark onboarding as completed
        customer.onboarding_status = "completed"
        customer.onboarding_step = "done"
        customer.onboarding_completed_at = datetime.utcnow()

        db.commit()

        logger.info(f"🎉 Deployment {deployment.id} completed successfully")
        logger.info(f"✅ Onboarding marked as completed for customer {customer_id}")
        logger.info(f"   vLLM: {deployment_result['services']['vllm']}")
        logger.info(f"   Console: {deployment_result['services']['console']}")
        logger.info(f"   MCPs: {len(deployment_result['services']['mcps'])} deployed")

    except Exception as e:
        logger.error(f"❌ Error in deployment processing: {e}")
        if deployment:
            deployment.status = "failed"
            db.commit()
        raise


@router.post("/deploy", response_model=OnboardingStatusResponse)
async def deploy_system(
    data: CompleteOnboardingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Complete onboarding and initiate deployment
    Step 6: Deploy
    """
    try:
        # Generate customer ID (in production, this would come from auth)
        customer_id = f"cust_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Start deployment in background
        background_tasks.add_task(process_deployment, customer_id, data, db)

        logger.info(f"Deployment initiated for customer {customer_id}")

        return OnboardingStatusResponse(
            step="deploy",
            status="processing",
            message="Deployment initiated",
            progress=0.0,
            deployment_id=customer_id
        )

    except Exception as e:
        logger.error(f"Error initiating deployment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{deployment_id}", response_model=OnboardingStatusResponse)
async def get_deployment_status(
    deployment_id: str,
    db: Session = Depends(get_db)
):
    """
    Get deployment status during processing
    """
    try:
        # In a real implementation, this would query the deployment status
        # For now, we'll return a simulated progress

        steps = [
            ("Initializing Docker containers", 0.2),
            ("Ingesting data", 0.4),
            ("Building embeddings", 0.6),
            ("Deploying LLM", 0.75),
            ("Installing MCPs", 0.85),
            ("Connecting systems", 0.95),
            ("Complete", 1.0)
        ]

        # Simulate progress (in production, read from deployment record)
        current_step = "Building embeddings"
        progress = 0.6

        return OnboardingStatusResponse(
            step=current_step,
            status="processing" if progress < 1.0 else "complete",
            message=f"Processing: {current_step}",
            progress=progress,
            deployment_id=deployment_id
        )

    except Exception as e:
        logger.error(f"Error getting deployment status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available-mcps")
async def get_available_mcps():
    """
    Get list of available MCPs for selection
    """
    mcps = [
        {
            "id": "tender",
            "name": "Tender MCP",
            "category": "sales",
            "price": 2500,
            "description": "Automated tender analysis and response generation"
        },
        {
            "id": "pricing",
            "name": "Pricing & Competitor MCP",
            "category": "sales",
            "price": 3000,
            "description": "Dynamic pricing and competitive analysis"
        },
        {
            "id": "pipeline",
            "name": "Pipeline MCP",
            "category": "sales",
            "price": 2000,
            "description": "Sales pipeline intelligence and forecasting"
        },
        {
            "id": "etim",
            "name": "ETIM Classification MCP",
            "category": "product",
            "price": 2000,
            "description": "Automated product classification to ETIM/ECLASS"
        },
        {
            "id": "product",
            "name": "Product Management MCP",
            "category": "product",
            "price": 3500,
            "description": "Product data management and enrichment"
        },
        {
            "id": "multichannel",
            "name": "Multi-Channel Publishing MCP",
            "category": "product",
            "price": 2000,
            "description": "Publish product data to multiple channels"
        },
        {
            "id": "ctax",
            "name": "CTAX Engine",
            "category": "finance",
            "price": 3000,
            "description": "German tax automation (UStG, EStG, etc.)"
        },
        {
            "id": "fpa",
            "name": "FP&A Automation MCP",
            "category": "finance",
            "price": 2500,
            "description": "Financial planning and analysis automation"
        },
        {
            "id": "procurement",
            "name": "Procurement MCP",
            "category": "finance",
            "price": 2000,
            "description": "Purchase order and supplier management"
        },
        {
            "id": "law",
            "name": "Law MCP",
            "category": "legal",
            "price": 3000,
            "description": "Legal document analysis and contract review"
        },
        {
            "id": "compliance",
            "name": "Sanctions & Compliance MCP",
            "category": "legal",
            "price": 3000,
            "description": "OFAC, EU, UK sanctions screening"
        },
        {
            "id": "research",
            "name": "Research MCP",
            "category": "legal",
            "price": 2500,
            "description": "Market and competitive research"
        }
    ]

    return {
        "success": True,
        "mcps": mcps,
        "categories": ["sales", "product", "finance", "legal"]
    }


@router.get("/available-connectors")
async def get_available_connectors():
    """
    Get list of available connectors
    """
    connectors = [
        {"id": "slack", "name": "Slack", "icon": "💬", "description": "Team Communication"},
        {"id": "microsoft365", "name": "Microsoft 365", "icon": "📧", "description": "Email & Docs"},
        {"id": "teams", "name": "Microsoft Teams", "icon": "👥", "description": "Team Communication"},
        {"id": "google", "name": "Google Workspace", "icon": "📊", "description": "Docs & Sheets"},
        {"id": "sap", "name": "SAP", "icon": "🗄️", "description": "ERP System"},
        {"id": "datev", "name": "DATEV", "icon": "💰", "description": "Accounting"},
        {"id": "salesforce", "name": "Salesforce", "icon": "📈", "description": "CRM"},
        {"id": "hubspot", "name": "HubSpot", "icon": "🎯", "description": "Marketing & CRM"},
        {"id": "jira", "name": "Jira", "icon": "📋", "description": "Project Management"},
        {"id": "confluence", "name": "Confluence", "icon": "📝", "description": "Documentation"},
        {"id": "shopify", "name": "Shopify", "icon": "🛒", "description": "E-Commerce"},
        {"id": "api", "name": "REST API", "icon": "🔗", "description": "Custom Systems"}
    ]

    return {
        "success": True,
        "connectors": connectors
    }


@router.get("/verify/{customer_id}")
async def verify_deployment(customer_id: str):
    """
    Verify deployment status and get service URLs
    Checks actual deployed services and returns real stats
    """
    import subprocess
    from minio import Minio

    try:
        # Check MinIO for uploaded files
        try:
            minio = Minio(
                endpoint="localhost:4050",
                access_key="0711admin",
                secret_key="0711secret",
                secure=False
            )

            bucket_name = f"customer-{customer_id}"
            if minio.bucket_exists(bucket_name=bucket_name):
                objects = list(minio.list_objects(bucket_name=bucket_name, recursive=True))
                file_count = len(objects)
                total_size = sum(obj.size for obj in objects)
            else:
                file_count = 0
                total_size = 0
        except Exception as e:
            logger.warning(f"Could not connect to MinIO: {e}")
            file_count = 0
            total_size = 0

        # Check Docker containers
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={customer_id}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            running_containers = result.stdout.strip().split('\n') if result.stdout.strip() else []
        except Exception as e:
            logger.warning(f"Could not check Docker containers: {e}")
            running_containers = []

        # Build service URLs (from deployment orchestrator port allocation)
        from provisioning.api.services.deployment_orchestrator import CustomerDeploymentOrchestrator
        orchestrator = CustomerDeploymentOrchestrator()
        ports = orchestrator.allocate_ports(customer_id)

        services = {
            "console": {
                "url": f"http://localhost:{ports['console']}",
                "status": "running" if running_containers else "pending"
            },
            "vllm": {
                "url": f"http://localhost:{ports['vllm']}",
                "status": "running" if running_containers else "pending"
            }
        }

        return {
            "success": True,
            "customer_id": customer_id,
            "services": services,
            "stats": {
                "files_uploaded": file_count,
                "total_size_mb": round(total_size / 1024 / 1024, 2),
                "containers_running": len(running_containers),
                "container_names": running_containers[:5]  # First 5
            },
            "status": "active" if running_containers else "provisioning"
        }

    except Exception as e:
        logger.error(f"Verification failed for {customer_id}: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# New endpoints for onboarding status tracking


class OnboardingStatusFullResponse(BaseModel):
    """Full onboarding status response"""
    status: str  # not_started, plan_selected, payment_completed, data_uploaded, completed
    step: Optional[str]  # Current step: plan, payment, upload, mcps
    customer_id: str
    has_deployment: bool
    onboarding_data: dict


class PlanChoiceRequest(BaseModel):
    """Plan selection during onboarding"""
    plan: str  # starter, professional, business
    billing_cycle: str  # monthly, annual


@router.get("/status")
async def get_onboarding_status(db: Session = Depends(get_db)):
    """
    Get onboarding status for currently authenticated user

    Returns current onboarding state to determine where user should be redirected
    """
    try:
        # TODO: Get customer_id from JWT token
        # For now, get the most recent customer (dev/testing)
        customer = db.query(Customer).order_by(Customer.created_at.desc()).first()

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Check if customer has any deployments
        deployment = db.query(Deployment).filter(
            Deployment.customer_id == customer.id,
            Deployment.status.in_(['active', 'provisioning'])
        ).first()

        return OnboardingStatusFullResponse(
            status=customer.onboarding_status or "not_started",
            step=customer.onboarding_step,
            customer_id=str(customer.id),
            has_deployment=deployment is not None,
            onboarding_data=customer.onboarding_data or {}
        )

    except Exception as e:
        logger.error(f"Error getting onboarding status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plan")
async def save_plan_choice(
    data: PlanChoiceRequest,
    db: Session = Depends(get_db)
):
    """
    Save plan choice during onboarding

    Updates customer's onboarding status to plan_selected
    """
    try:
        # TODO: Get customer_id from JWT token
        # For now, get the most recent customer (dev/testing)
        customer = db.query(Customer).order_by(Customer.created_at.desc()).first()

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Update onboarding status
        customer.onboarding_status = "plan_selected"
        customer.onboarding_step = "payment"
        customer.onboarding_data = {
            "plan": data.plan,
            "billing_cycle": data.billing_cycle
        }

        db.commit()

        return {
            "success": True,
            "message": "Plan choice saved",
            "customer_id": str(customer.id),
            "status": customer.onboarding_status
        }

    except Exception as e:
        logger.error(f"Error saving plan choice: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
