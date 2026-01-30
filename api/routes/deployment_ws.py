"""
WebSocket endpoint for real-time deployment updates
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
import asyncio
import json

logger = logging.getLogger(__name__)
router = APIRouter()

# Store active deployment status
deployment_status = {}


@router.websocket("/ws/deployment/{customer_id}")
async def deployment_websocket(websocket: WebSocket, customer_id: str):
    """
    WebSocket for streaming deployment progress to client
    """
    await websocket.accept()
    logger.info(f"WebSocket connected for customer: {customer_id}")

    try:
        # Send initial status
        await websocket.send_json({
            "type": "connected",
            "customer_id": customer_id,
            "message": "Connected to deployment stream"
        })

        # Stream deployment updates
        while True:
            # Check if there's status for this customer
            if customer_id in deployment_status:
                status = deployment_status[customer_id]
                await websocket.send_json(status)

                # If deployment complete or failed, close connection
                if status.get("status") in ["completed", "failed"]:
                    await websocket.send_json({
                        "type": "final",
                        "status": status["status"]
                    })
                    break

            # Wait before next update
            await asyncio.sleep(0.5)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for customer: {customer_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass


async def update_deployment_status(customer_id: str, status_update: dict):
    """
    Update deployment status (called by deployment orchestrator)
    """
    if customer_id not in deployment_status:
        deployment_status[customer_id] = {}

    deployment_status[customer_id].update(status_update)
    deployment_status[customer_id]["timestamp"] = asyncio.get_event_loop().time()

    logger.info(f"Deployment status updated for {customer_id}: {status_update.get('step')}")
