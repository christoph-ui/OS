"""
Unified Progress WebSocket
Streams real-time updates for Upload, Ingestion, and Deployment
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
import asyncio
from typing import Dict, List

logger = logging.getLogger(__name__)
router = APIRouter()

# Store active WebSocket connections per customer
active_connections: Dict[str, List[WebSocket]] = {}

# Store progress state per customer
progress_state: Dict[str, Dict] = {}


@router.websocket("/ws/progress/{customer_id}")
async def progress_websocket(websocket: WebSocket, customer_id: str):
    """
    WebSocket for streaming unified progress updates

    Sends updates for:
    - Upload progress
    - Ingestion progress
    - Deployment progress
    """
    await websocket.accept()

    # Track connection
    if customer_id not in active_connections:
        active_connections[customer_id] = []
    active_connections[customer_id].append(websocket)

    logger.info(f"Progress WebSocket connected for customer: {customer_id} (total: {len(active_connections[customer_id])})")

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "customer_id": customer_id,
            "message": "Connected to progress stream"
        })

        # Send current state if exists
        if customer_id in progress_state:
            await websocket.send_json(progress_state[customer_id])

        # Keep connection alive and stream updates
        while True:
            # Wait for client ping or just keep alive
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # Send keepalive
                await websocket.send_json({"type": "ping"})

    except WebSocketDisconnect:
        logger.info(f"Progress WebSocket disconnected for customer: {customer_id}")
    except Exception as e:
        logger.error(f"Progress WebSocket error: {e}")
    finally:
        # Remove from active connections
        if customer_id in active_connections and websocket in active_connections[customer_id]:
            active_connections[customer_id].remove(websocket)
            if not active_connections[customer_id]:
                del active_connections[customer_id]


async def send_progress_update(customer_id: str, update: dict):
    """
    Send progress update to all connected clients for this customer

    Args:
        customer_id: Customer ID
        update: Progress update dict with keys:
                - type: "upload" | "ingestion" | "deployment"
                - progress: 0-100
                - message: Human-readable status
                - phase: (optional) Current phase
                - details: (optional) Additional info
    """
    # Store state
    if customer_id not in progress_state:
        progress_state[customer_id] = {}

    progress_state[customer_id].update(update)
    progress_state[customer_id]["timestamp"] = asyncio.get_event_loop().time()

    # Broadcast to all connected clients
    if customer_id in active_connections:
        dead_connections = []

        for websocket in active_connections[customer_id]:
            try:
                await websocket.send_json(update)
            except Exception as e:
                logger.error(f"Failed to send to client: {e}")
                dead_connections.append(websocket)

        # Clean up dead connections
        for ws in dead_connections:
            active_connections[customer_id].remove(ws)

    logger.info(f"Progress update sent for {customer_id}: {update.get('type')} - {update.get('message')}")


def clear_progress_state(customer_id: str):
    """Clear progress state after completion"""
    if customer_id in progress_state:
        del progress_state[customer_id]
