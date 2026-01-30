"""
MCP Marketplace Routes (Console Backend)

Proxy for marketplace operations using console auth (in-memory users)
"""

import logging
import httpx
from fastapi import APIRouter, HTTPException, Depends
from typing import List

from ..auth.dependencies import require_auth, CustomerContext

logger = logging.getLogger(__name__)
router = APIRouter()

# Control Plane API URL
CONTROL_PLANE_URL = "http://localhost:4080"


@router.get("/marketplace")
async def list_marketplace_mcps(ctx: CustomerContext = Depends(require_auth)):
    """
    List all MCPs in marketplace

    Proxies to Control Plane API
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{CONTROL_PLANE_URL}/api/mcps/")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Failed to load marketplace: {e}")
        raise HTTPException(status_code=500, detail="Failed to load marketplace")


@router.post("/marketplace/subscribe/{mcp_name}")
async def subscribe_to_mcp(
    mcp_name: str,
    ctx: CustomerContext = Depends(require_auth)
):
    """
    Subscribe to an MCP

    Writes to database Customer.enabled_mcps for persistence
    """
    from api.database import SessionLocal
    from api.models.customer import Customer

    db = SessionLocal()
    try:
        # Get customer from database
        customer = db.query(Customer).filter(Customer.contact_email == ctx.user_email).first()

        if not customer:
            logger.warning(f"Customer not found for {ctx.user_email}, creating...")
            # Create customer if doesn't exist
            import uuid
            customer = Customer(
                id=uuid.uuid4(),
                company_name=f"Customer {ctx.customer_id}",
                contact_name=ctx.user_email.split('@')[0],
                contact_email=ctx.user_email,
                tier="starter",
                status="active",
                enabled_mcps={},
                connected_mcps={"input": [], "output": []}
            )
            db.add(customer)
            db.flush()

        # Add MCP to enabled_mcps
        # IMPORTANT: Create new dict to trigger SQLAlchemy change detection for JSONB
        enabled_mcps = dict(customer.enabled_mcps or {})
        enabled_mcps[mcp_name] = True
        customer.enabled_mcps = enabled_mcps

        # Mark as modified (for JSONB columns)
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(customer, "enabled_mcps")

        db.commit()

        logger.info(f"User {ctx.user_email} subscribed to MCP '{mcp_name}' (persisted to database)")

        return {
            "success": True,
            "message": f"Successfully subscribed to {mcp_name}",
            "mcp_name": mcp_name,
            "customer_id": ctx.customer_id
        }

    except Exception as e:
        logger.error(f"Failed to subscribe to {mcp_name}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/marketplace/subscriptions")
async def list_subscriptions(ctx: CustomerContext = Depends(require_auth)):
    """
    List customer's MCP subscriptions

    Reads from database Customer.enabled_mcps
    """
    from api.database import SessionLocal
    from api.models.customer import Customer

    db = SessionLocal()
    try:
        # Get customer from database
        customer = db.query(Customer).filter(Customer.contact_email == ctx.user_email).first()

        if not customer:
            return {
                "success": True,
                "subscriptions": [],
                "customer_id": ctx.customer_id
            }

        # Get enabled MCPs
        enabled_mcps = customer.enabled_mcps or {}
        subscribed = [mcp_name for mcp_name, enabled in enabled_mcps.items() if enabled]

        return {
            "success": True,
            "subscriptions": subscribed,
            "customer_id": ctx.customer_id
        }

    except Exception as e:
        logger.error(f"Failed to load subscriptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/marketplace/connections")
async def list_connections(ctx: CustomerContext = Depends(require_auth)):
    """
    List all MCP connections for the customer

    Returns both subscribed and connected MCPs with status
    """
    from api.database import SessionLocal
    from api.models.customer import Customer
    from api.models.mcp import MCP

    db = SessionLocal()
    try:
        # Get customer from database
        customer = db.query(Customer).filter(Customer.contact_email == ctx.user_email).first()

        if not customer:
            return {
                "success": True,
                "input": [],
                "output": [],
                "summary": {
                    "total_subscribed": 0,
                    "total_connected": 0,
                    "input_connected": 0,
                    "output_connected": 0
                }
            }

        enabled_mcps = customer.enabled_mcps or {}
        connected_mcps = customer.connected_mcps or {"input": [], "output": []}

        # Get MCP details from database
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
                # Subscribed but not connected
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

    except Exception as e:
        logger.error(f"Failed to load connections: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/marketplace/connect")
async def connect_mcp(
    mcp_name: str,
    direction: str,
    ctx: CustomerContext = Depends(require_auth)
):
    """
    Connect an MCP (after subscription)

    Writes to database Customer.connected_mcps for persistence
    """
    from api.database import SessionLocal
    from api.models.customer import Customer

    db = SessionLocal()
    try:
        # Get customer from database
        customer = db.query(Customer).filter(Customer.contact_email == ctx.user_email).first()

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Add to connected_mcps
        # IMPORTANT: Create new dict to trigger SQLAlchemy change detection for JSONB
        connected_mcps = {
            "input": list(customer.connected_mcps.get("input", []) if customer.connected_mcps else []),
            "output": list(customer.connected_mcps.get("output", []) if customer.connected_mcps else [])
        }

        if direction not in connected_mcps:
            connected_mcps[direction] = []

        if mcp_name not in connected_mcps[direction]:
            connected_mcps[direction].append(mcp_name)

        customer.connected_mcps = connected_mcps

        # Mark as modified (for JSONB columns)
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(customer, "connected_mcps")

        db.commit()

        logger.info(f"User {ctx.user_email} connected MCP '{mcp_name}' as {direction} (persisted to database)")

        return {
            "success": True,
            "message": f"MCP '{mcp_name}' connected as {direction}",
            "mcp_name": mcp_name,
            "direction": direction,
            "connected_mcps": connected_mcps
        }

    except Exception as e:
        logger.error(f"Failed to connect {mcp_name}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
