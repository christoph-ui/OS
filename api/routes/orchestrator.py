"""
Orchestrator API Routes

REST API for Orchestrator MCP functionality
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

from api.utils.security import get_current_user
from api.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orchestrator", tags=["orchestrator"])


# =========================================================================
# REQUEST/RESPONSE MODELS
# =========================================================================

class InitializeCustomerRequest(BaseModel):
    """Request to initialize customer deployment"""
    company_name: str
    contact_email: str
    data_sources: List[str]
    deployment_target: str = "on-premise"
    mcps: Optional[List[str]] = None
    installation_params: Optional[Dict[str, Any]] = None


class ProcessDocumentsRequest(BaseModel):
    """Request to process new documents"""
    customer_id: str
    file_paths: List[str]


class GenerateEmbeddingsRequest(BaseModel):
    """Request to generate embeddings"""
    customer_id: str
    texts: List[str]


class QueryDatabaseRequest(BaseModel):
    """Request to query customer database"""
    customer_id: str
    database: str  # 'neo4j', 'lakehouse', 'minio'
    query: str
    require_approval: bool = True


# =========================================================================
# DEPLOYMENT ENDPOINTS
# =========================================================================

@router.post("/initialize-customer")
async def initialize_customer(
    request: InitializeCustomerRequest,
    background_tasks: BackgroundTasks
):
    """
    Initialize new customer deployment

    Complete onboarding:
    1. Create user account
    2. Process data with Cradle GPU
    3. Build Docker image
    4. Deploy
    5. Archive initial image

    This is a long-running operation (10-30 minutes)
    """
    try:
        from mcps.registry import get_mcp

        orchestrator = get_mcp("orchestrator")

        if not orchestrator:
            raise HTTPException(500, "Orchestrator MCP not available")

        # Execute initialization
        result = await orchestrator.initialize_customer(
            company_name=request.company_name,
            contact_email=request.contact_email,
            data_sources=request.data_sources,
            deployment_target=request.deployment_target,
            mcps=request.mcps,
            installation_params=request.installation_params
        )

        return {
            "success": True,
            "message": "Customer initialized successfully",
            "data": result
        }

    except Exception as e:
        logger.error(f"Customer initialization failed: {e}", exc_info=True)
        raise HTTPException(500, f"Initialization failed: {str(e)}")


# =========================================================================
# INCREMENTAL UPDATE ENDPOINTS
# =========================================================================

@router.post("/process-documents")
async def process_documents(
    request: ProcessDocumentsRequest,
    user: User = Depends(get_current_user)
):
    """
    Process new documents for customer

    Uses MCP Central services for consistent processing
    """
    try:
        from mcps.registry import get_mcp

        orchestrator = get_mcp("orchestrator")

        if not orchestrator:
            raise HTTPException(500, "Orchestrator MCP not available")

        # Get user token
        user_token = user.get_token()  # Would need to implement

        result = await orchestrator.process_new_documents(
            customer_id=request.customer_id,
            user_token=user_token,
            file_paths=request.file_paths
        )

        return {
            "success": True,
            "message": f"Processed {len(request.file_paths)} documents",
            "data": result
        }

    except Exception as e:
        logger.error(f"Document processing failed: {e}", exc_info=True)
        raise HTTPException(500, f"Processing failed: {str(e)}")


@router.post("/generate-embeddings")
async def generate_embeddings(
    request: GenerateEmbeddingsRequest,
    user: User = Depends(get_current_user)
):
    """
    Generate embeddings via MCP Central

    Uses saved installation parameters for consistency
    """
    try:
        from mcps.registry import get_mcp

        orchestrator = get_mcp("orchestrator")

        if not orchestrator:
            raise HTTPException(500, "Orchestrator MCP not available")

        user_token = user.get_token()

        result = await orchestrator.generate_embeddings(
            customer_id=request.customer_id,
            user_token=user_token,
            texts=request.texts
        )

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        logger.error(f"Embedding generation failed: {e}", exc_info=True)
        raise HTTPException(500, f"Generation failed: {str(e)}")


# =========================================================================
# DATABASE ACCESS ENDPOINTS
# =========================================================================

@router.post("/query-database")
async def query_database(
    request: QueryDatabaseRequest,
    user: User = Depends(get_current_user)
):
    """
    Query customer database with authorization

    Write operations require human approval
    """
    try:
        from mcps.registry import get_mcp

        orchestrator = get_mcp("orchestrator")

        if not orchestrator:
            raise HTTPException(500, "Orchestrator MCP not available")

        user_token = user.get_token()

        result = await orchestrator.query_customer_database(
            customer_id=request.customer_id,
            user_token=user_token,
            database=request.database,
            query=request.query,
            require_approval=request.require_approval
        )

        return {
            "success": True,
            "data": result
        }

    except PermissionError as e:
        raise HTTPException(403, str(e))
    except Exception as e:
        logger.error(f"Database query failed: {e}", exc_info=True)
        raise HTTPException(500, f"Query failed: {str(e)}")


# =========================================================================
# MARKETPLACE ENDPOINTS
# =========================================================================

@router.get("/marketplace/mcps")
async def list_marketplace_mcps(
    category: Optional[str] = None,
    search: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """List available MCPs in marketplace"""
    try:
        from mcps.registry import get_mcp

        orchestrator = get_mcp("orchestrator")

        if not orchestrator:
            raise HTTPException(500, "Orchestrator MCP not available")

        user_token = user.get_token()

        result = await orchestrator.list_marketplace_mcps(
            user_token=user_token,
            category=category,
            search=search
        )

        return result

    except Exception as e:
        logger.error(f"Marketplace listing failed: {e}", exc_info=True)
        raise HTTPException(500, f"Listing failed: {str(e)}")


class InstallMCPRequest(BaseModel):
    """Request to install MCP"""
    mcp_name: str
    license_key: Optional[str] = None


@router.post("/marketplace/install")
async def install_mcp(
    request: InstallMCPRequest,
    user: User = Depends(get_current_user)
):
    """Install MCP for customer"""
    try:
        from mcps.registry import get_mcp

        orchestrator = get_mcp("orchestrator")

        if not orchestrator:
            raise HTTPException(500, "Orchestrator MCP not available")

        user_token = user.get_token()

        result = await orchestrator.install_mcp(
            user_token=user_token,
            mcp_name=request.mcp_name,
            license_key=request.license_key
        )

        return result

    except Exception as e:
        logger.error(f"MCP installation failed: {e}", exc_info=True)
        raise HTTPException(500, f"Installation failed: {str(e)}")


class ConnectMCPRequest(BaseModel):
    """Request to connect MCP"""
    mcp_name: str
    direction: str  # 'input' or 'output'
    config: Optional[Dict[str, Any]] = None


@router.post("/marketplace/connect")
async def connect_mcp(
    request: ConnectMCPRequest,
    user: User = Depends(get_current_user)
):
    """Connect MCP as input or output"""
    try:
        from mcps.registry import get_mcp

        orchestrator = get_mcp("orchestrator")

        if not orchestrator:
            raise HTTPException(500, "Orchestrator MCP not available")

        user_token = user.get_token()

        result = await orchestrator.connect_mcp(
            user_token=user_token,
            mcp_name=request.mcp_name,
            direction=request.direction,
            config=request.config
        )

        return result

    except Exception as e:
        logger.error(f"MCP connection failed: {e}", exc_info=True)
        raise HTTPException(500, f"Connection failed: {str(e)}")


class QueryMCPRequest(BaseModel):
    """Request to query MCP"""
    mcp_name: str
    query: str
    context: Optional[Dict[str, Any]] = None


@router.post("/marketplace/query")
async def query_mcp(
    request: QueryMCPRequest,
    user: User = Depends(get_current_user)
):
    """Query MCP service"""
    try:
        from mcps.registry import get_mcp

        orchestrator = get_mcp("orchestrator")

        if not orchestrator:
            raise HTTPException(500, "Orchestrator MCP not available")

        user_token = user.get_token()

        result = await orchestrator.query_mcp(
            user_token=user_token,
            mcp_name=request.mcp_name,
            query=request.query,
            context=request.context
        )

        return result

    except Exception as e:
        logger.error(f"MCP query failed: {e}", exc_info=True)
        raise HTTPException(500, f"Query failed: {str(e)}")


# =========================================================================
# INTELLIGENCE ENDPOINTS
# =========================================================================

@router.get("/changes/{customer_id}")
async def get_data_changes(
    customer_id: str,
    user: User = Depends(get_current_user)
):
    """Get data changes and service offers"""
    try:
        from mcps.registry import get_mcp

        orchestrator = get_mcp("orchestrator")

        if not orchestrator:
            raise HTTPException(500, "Orchestrator MCP not available")

        user_token = user.get_token()

        result = await orchestrator.get_data_changes(
            customer_id=customer_id,
            user_token=user_token
        )

        return result

    except Exception as e:
        logger.error(f"Change detection failed: {e}", exc_info=True)
        raise HTTPException(500, f"Detection failed: {str(e)}")


# =========================================================================
# RESOURCE ENDPOINTS (Read-only)
# =========================================================================

@router.get("/stats/{customer_id}")
async def get_customer_stats(
    customer_id: str,
    user: User = Depends(get_current_user)
):
    """Get customer statistics"""
    try:
        from mcps.registry import get_mcp

        orchestrator = get_mcp("orchestrator")

        if not orchestrator:
            raise HTTPException(500, "Orchestrator MCP not available")

        user_token = user.get_token()

        stats = await orchestrator.get_customer_stats(customer_id, user_token)

        return {
            "success": True,
            "data": stats
        }

    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}", exc_info=True)
        raise HTTPException(500, f"Retrieval failed: {str(e)}")


@router.get("/config/{customer_id}")
async def get_installation_config(
    customer_id: str,
    user: User = Depends(get_current_user)
):
    """Get installation configuration"""
    try:
        from mcps.registry import get_mcp

        orchestrator = get_mcp("orchestrator")

        if not orchestrator:
            raise HTTPException(500, "Orchestrator MCP not available")

        config = await orchestrator.get_installation_config(customer_id)

        return {
            "success": True,
            "data": config
        }

    except Exception as e:
        logger.error(f"Config retrieval failed: {e}", exc_info=True)
        raise HTTPException(500, f"Retrieval failed: {str(e)}")


@router.get("/deployments")
async def list_deployments():
    """List all customer deployments"""
    try:
        from mcps.registry import get_mcp

        orchestrator = get_mcp("orchestrator")

        if not orchestrator:
            raise HTTPException(500, "Orchestrator MCP not available")

        deployments = await orchestrator.list_customer_deployments()

        return {
            "success": True,
            "total": len(deployments),
            "deployments": deployments
        }

    except Exception as e:
        logger.error(f"Deployment listing failed: {e}", exc_info=True)
        raise HTTPException(500, f"Listing failed: {str(e)}")
