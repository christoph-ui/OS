"""
MCP Services API Routes
Manage customer access to shared MCP services (not marketplace MCPs)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any
import logging

from api.database import get_db
from api.models.customer import Customer
from api.utils.security import get_current_customer
from orchestrator.mcp.mcp_router import mcp_router

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/mcp-services", tags=["mcp-services"])


class EnableMCPRequest(BaseModel):
    """Request to enable an MCP for a customer"""
    mcp_name: str


class QueryMCPRequest(BaseModel):
    """Request to query an MCP"""
    mcp_name: str
    query: str
    context: Dict[str, Any] = {}


class ConnectMCPRequest(BaseModel):
    """Request to connect an MCP"""
    mcp_name: str
    direction: str  # "input" or "output"
    config: Dict[str, Any] = {}


@router.get("/available")
async def list_available_mcps():
    """
    List all available shared MCP services.

    Returns:
        List of MCP info with capabilities and pricing
    """
    mcps = mcp_router.list_mcps()

    # Add pricing info (could be from database in production)
    pricing = {
        "etim": {
            "monthly": 500,  # €500/month
            "annual": 5000,  # €5000/year (2 months free)
            "description": "ETIM/ECLASS product classification"
        }
    }

    for mcp in mcps:
        mcp["pricing"] = pricing.get(mcp["name"], {
            "monthly": 0,
            "annual": 0,
            "description": "Free tier"
        })

    return {
        "success": True,
        "mcps": mcps
    }


@router.get("/enabled")
async def list_enabled_mcps(
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    List MCPs enabled for the current customer.

    Returns:
        List of enabled MCP names
    """
    enabled_mcps = customer.enabled_mcps or {}

    # Return only MCPs where value is True
    enabled_list = [
        mcp_name for mcp_name, enabled in enabled_mcps.items()
        if enabled
    ]

    return {
        "success": True,
        "enabled_mcps": enabled_list,
        "count": len(enabled_list)
    }


@router.post("/enable/{mcp_name}")
async def enable_mcp(
    mcp_name: str,
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Enable an MCP for the customer.

    No deployment needed - just updates permission flag.

    Args:
        mcp_name: Name of MCP to enable (e.g., "etim")

    Returns:
        Success message
    """
    # Verify MCP exists
    mcp_info = mcp_router.get_mcp_info(mcp_name)
    if not mcp_info:
        raise HTTPException(status_code=404, detail=f"MCP '{mcp_name}' not found")

    # Enable MCP
    enabled_mcps = customer.enabled_mcps or {}
    enabled_mcps[mcp_name] = True
    customer.enabled_mcps = enabled_mcps

    db.commit()

    logger.info(f"Enabled MCP '{mcp_name}' for customer {customer.id}")

    return {
        "success": True,
        "message": f"MCP '{mcp_name}' enabled for {customer.company_name}",
        "mcp": mcp_info
    }


@router.post("/disable/{mcp_name}")
async def disable_mcp(
    mcp_name: str,
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Disable an MCP for the customer.

    Args:
        mcp_name: Name of MCP to disable

    Returns:
        Success message
    """
    # Update enabled_mcps
    enabled_mcps = customer.enabled_mcps or {}
    enabled_mcps[mcp_name] = False
    customer.enabled_mcps = enabled_mcps

    db.commit()

    logger.info(f"Disabled MCP '{mcp_name}' for customer {customer.id}")

    return {
        "success": True,
        "message": f"MCP '{mcp_name}' disabled for {customer.company_name}"
    }


@router.get("/{mcp_name}/info")
async def get_mcp_info(mcp_name: str):
    """
    Get detailed information about an MCP.

    Args:
        mcp_name: Name of MCP

    Returns:
        MCP info including capabilities, version, etc.
    """
    mcp_info = mcp_router.get_mcp_info(mcp_name)
    if not mcp_info:
        raise HTTPException(status_code=404, detail=f"MCP '{mcp_name}' not found")

    return {
        "success": True,
        "mcp": mcp_info
    }


@router.post("/query")
async def query_mcp(
    request: QueryMCPRequest,
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Query an MCP service.

    Requires MCP to be enabled for customer.

    Args:
        request: Query request with mcp_name, query text, and context

    Returns:
        MCP query results
    """
    # Check if MCP is enabled for customer
    enabled_mcps = customer.enabled_mcps or {}
    if not enabled_mcps.get(request.mcp_name, False):
        raise HTTPException(
            status_code=403,
            detail=f"MCP '{request.mcp_name}' is not enabled for your account. "
                   f"Enable it at /api/mcp-services/enable/{request.mcp_name}"
        )

    try:
        # Route query to shared MCP
        result = await mcp_router.query_mcp(
            mcp_name=request.mcp_name,
            customer_id=str(customer.id),
            query=request.query,
            context=request.context
        )

        return {
            "success": True,
            "mcp": request.mcp_name,
            "results": result
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"MCP query failed: {e}")
        raise HTTPException(status_code=500, detail=f"MCP query failed: {str(e)}")


@router.get("/{mcp_name}/health")
async def check_mcp_health(mcp_name: str):
    """
    Check health status of an MCP service.

    Args:
        mcp_name: Name of MCP to check

    Returns:
        Health status
    """
    is_healthy = await mcp_router.check_mcp_health(mcp_name)

    return {
        "success": True,
        "mcp": mcp_name,
        "healthy": is_healthy,
        "status": "online" if is_healthy else "offline"
    }


@router.post("/connect")
async def connect_mcp(
    request: ConnectMCPRequest,
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Connect (activate) an MCP for the customer.

    Moves MCP from subscribed → connected state.
    Makes MCP tools available immediately.

    Args:
        request: Connection request with mcp_name and direction

    Returns:
        Success message with connection details
    """
    # Check if MCP is enabled (subscribed)
    enabled_mcps = customer.enabled_mcps or {}
    if not enabled_mcps.get(request.mcp_name, False):
        raise HTTPException(
            status_code=403,
            detail=f"MCP '{request.mcp_name}' is not subscribed. Subscribe first at /api/mcp-services/enable/{request.mcp_name}"
        )

    # Validate direction
    if request.direction not in ["input", "output"]:
        raise HTTPException(status_code=400, detail="Direction must be 'input' or 'output'")

    # Get current connections
    connected_mcps = customer.connected_mcps or {"input": [], "output": []}

    # Check if already connected
    if request.mcp_name in connected_mcps.get(request.direction, []):
        return {
            "success": True,
            "message": f"MCP '{request.mcp_name}' already connected as {request.direction}",
            "connected_mcps": connected_mcps
        }

    # Add to connections
    if request.direction not in connected_mcps:
        connected_mcps[request.direction] = []

    connected_mcps[request.direction].append(request.mcp_name)
    customer.connected_mcps = connected_mcps

    db.commit()

    logger.info(f"Connected MCP '{request.mcp_name}' ({request.direction}) for customer {customer.id}")

    return {
        "success": True,
        "message": f"MCP '{request.mcp_name}' connected as {request.direction}",
        "connected_mcps": connected_mcps,
        "tools_available": True  # Tools are now available
    }


@router.post("/disconnect")
async def disconnect_mcp(
    request: EnableMCPRequest,  # Reuse - just needs mcp_name
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Disconnect (deactivate) an MCP for the customer.

    Removes MCP from connected state (but keeps subscription).
    Tools become unavailable.

    Args:
        request: Request with mcp_name

    Returns:
        Success message
    """
    # Get current connections
    connected_mcps = customer.connected_mcps or {"input": [], "output": []}

    # Remove from both directions
    removed = False
    for direction in ["input", "output"]:
        if request.mcp_name in connected_mcps.get(direction, []):
            connected_mcps[direction].remove(request.mcp_name)
            removed = True

    if not removed:
        return {
            "success": True,
            "message": f"MCP '{request.mcp_name}' was not connected"
        }

    customer.connected_mcps = connected_mcps
    db.commit()

    logger.info(f"Disconnected MCP '{request.mcp_name}' for customer {customer.id}")

    return {
        "success": True,
        "message": f"MCP '{request.mcp_name}' disconnected",
        "connected_mcps": connected_mcps
    }


@router.get("/connections")
async def list_connections(
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    List all MCP connections for the customer.

    Returns both subscribed and connected MCPs with their status.

    Returns:
        Detailed connection information
    """
    from api.models.mcp import MCP

    enabled_mcps = customer.enabled_mcps or {}
    connected_mcps = customer.connected_mcps or {"input": [], "output": []}

    # Get MCP details
    all_mcp_names = list(enabled_mcps.keys())
    mcps = db.query(MCP).filter(MCP.name.in_(all_mcp_names)).all() if all_mcp_names else []

    # Build response
    input_mcps = []
    output_mcps = []

    for mcp in mcps:
        mcp_info = {
            "id": str(mcp.id),
            "name": mcp.name,
            "display_name": mcp.display_name,
            "description": mcp.description,
            "icon": mcp.icon,
            "icon_color": mcp.icon_color,
            "direction": mcp.direction,
            "subscribed": enabled_mcps.get(mcp.name, False),
            "connected": False,
            "status": "subscribed_not_connected"
        }

        # Check if connected
        if mcp.name in connected_mcps.get("input", []):
            mcp_info["connected"] = True
            mcp_info["status"] = "connected"
            mcp_info["connected_direction"] = "input"
            input_mcps.append(mcp_info)
        elif mcp.name in connected_mcps.get("output", []):
            mcp_info["connected"] = True
            mcp_info["status"] = "connected"
            mcp_info["connected_direction"] = "output"
            output_mcps.append(mcp_info)
        else:
            # Subscribed but not connected - add to appropriate list by default direction
            if mcp.direction == "input":
                input_mcps.append(mcp_info)
            else:
                output_mcps.append(mcp_info)

    return {
        "success": True,
        "input": input_mcps,
        "output": output_mcps,
        "summary": {
            "total_subscribed": len(enabled_mcps),
            "total_connected": len(connected_mcps.get("input", [])) + len(connected_mcps.get("output", [])),
            "input_connected": len(connected_mcps.get("input", [])),
            "output_connected": len(connected_mcps.get("output", []))
        }
    }
