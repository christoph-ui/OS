"""
Chat Routes

Real-time chat with MCPs via WebSocket and REST.
"""

import logging
import json
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Request, Depends, Query
from pydantic import BaseModel

from ..websocket.manager import ConnectionManager
from ..auth.dependencies import require_auth, get_current_user
from ..auth.models import CustomerContext, TokenData
from ..auth.jwt import verify_token

logger = logging.getLogger(__name__)
router = APIRouter()

# WebSocket connection manager
manager = ConnectionManager()


class ChatMessage(BaseModel):
    """Chat message request"""
    message: str
    mcp: Optional[str] = None  # Specific MCP, or auto-route
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    """Chat response"""
    answer: str
    mcp_used: str
    confidence: float
    sources: list
    suggested_questions: list = []
    metadata: dict = {}
    timestamp: str


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: Request,
    message: ChatMessage,
    ctx: Optional[CustomerContext] = Depends(get_current_user)
):
    """
    Send a chat message and get a response.

    Requires authentication in production. Dev mode allows unauthenticated access.

    The platform automatically routes to the appropriate MCP
    based on the message content, or uses the specified MCP.

    Example:
        POST /api/chat
        Headers: Authorization: Bearer <token>
        {
            "message": "What's our Q4 tax liability?",
            "mcp": null  // Auto-route to CTAX
        }
    """
    # Get platform (may be None if initialization failed)
    platform = getattr(request.app.state, 'platform', None)

    # Dev mode: Allow unauthenticated access with default customer
    if not ctx:
        from ..config import config
        if config.debug:
            # Use Eaton as default customer in dev mode
            from ..auth.models import CustomerContext
            ctx = CustomerContext(
                customer_id="eaton",
                user_id="dev-user",
                user_email="dev@0711.io",
                is_admin=True
            )
        else:
            raise HTTPException(status_code=401, detail="Authentication required")

    # Check MCP access permission
    if message.mcp and hasattr(ctx, 'can_access_mcp') and not ctx.can_access_mcp(message.mcp):
        raise HTTPException(
            status_code=403,
            detail=f"Access denied to MCP: {message.mcp}"
        )

    try:
        # Build context with customer isolation
        query_context = {
            "customer_id": ctx.customer_id,
            "user_id": ctx.user_id if hasattr(ctx, 'user_id') else "dev-user",
            **(message.context or {})
        }

        # Query platform with customer context
        # Platform automatically routes to customer-specific containers
        if not platform:
            raise HTTPException(status_code=500, detail="Platform not initialized")

        result = await platform.query(
            question=message.message,
            mcp=message.mcp,
            context=query_context
        )

        # Store in chat history
        if ctx.customer_id not in _chat_history:
            _chat_history[ctx.customer_id] = []

        _chat_history[ctx.customer_id].append({
            "role": "user",
            "content": message.message,
            "timestamp": datetime.utcnow().isoformat()
        })
        _chat_history[ctx.customer_id].append({
            "role": "assistant",
            "content": result.answer,
            "mcp": result.mcp_used,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Keep only last 100 messages per customer
        if len(_chat_history[ctx.customer_id]) > 100:
            _chat_history[ctx.customer_id] = _chat_history[ctx.customer_id][-100:]

        # Extract enhanced response fields (from Platform query result)
        suggested_questions = []
        metadata_dict = {}

        # Platform returns QueryResult with metadata
        if hasattr(result, 'metadata') and result.metadata:
            suggested_questions = result.metadata.get("suggested_questions", [])
            metadata_dict = result.metadata

        return ChatResponse(
            answer=result.answer,
            mcp_used=result.mcp_used,
            confidence=result.confidence,
            sources=result.sources if result.sources else [],
            suggested_questions=suggested_questions,
            metadata=metadata_dict,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/chat")
async def websocket_chat(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time chat.

    Authentication: Pass token as query parameter: /ws/chat?token=<jwt>

    Protocol:
        Client -> Server (authenticate first):
        {
            "type": "auth",
            "token": "jwt_token_here"
        }

        Client -> Server:
        {
            "type": "message",
            "content": "What's our Q4 tax?",
            "mcp": "ctax"  // optional
        }

        Server -> Client:
        {
            "type": "response",
            "content": "Based on your documents...",
            "mcp_used": "ctax",
            "confidence": 0.92,
            "sources": ["tax_2024.pdf"]
        }

        Server -> Client (streaming):
        {
            "type": "stream",
            "content": "partial response...",
            "done": false
        }
    """
    # Authenticate via query param or first message
    customer_id = None
    user_id = None

    if token:
        token_data = verify_token(token)
        if token_data:
            customer_id = token_data.customer_id
            user_id = token_data.user_id

    await manager.connect(websocket)

    try:
        # Get platform from app state
        platform = websocket.app.state.platform

        while True:
            # Receive message
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                msg_type = message.get("type", "message")

                if msg_type == "ping":
                    # Heartbeat
                    await websocket.send_json({"type": "pong"})
                    continue

                if msg_type == "auth":
                    # Authenticate via message
                    auth_token = message.get("token")
                    if auth_token:
                        token_data = verify_token(auth_token)
                        if token_data:
                            customer_id = token_data.customer_id
                            user_id = token_data.user_id
                            await websocket.send_json({
                                "type": "auth_success",
                                "customer_id": customer_id
                            })
                        else:
                            await websocket.send_json({
                                "type": "auth_error",
                                "content": "Invalid token"
                            })
                    continue

                if msg_type == "message":
                    # Require authentication for messages
                    if not customer_id:
                        await websocket.send_json({
                            "type": "error",
                            "content": "Authentication required. Send auth message first."
                        })
                        continue

                    content = message.get("content", "")
                    mcp = message.get("mcp")

                    if not content:
                        await websocket.send_json({
                            "type": "error",
                            "content": "Message content required"
                        })
                        continue

                    # Send "thinking" status
                    await websocket.send_json({
                        "type": "status",
                        "content": "Processing...",
                        "mcp": mcp or "auto"
                    })

                    # Query platform with customer context
                    result = await platform.query(
                        question=content,
                        mcp=mcp,
                        context={
                            "customer_id": customer_id,
                            "user_id": user_id
                        }
                    )

                    # Send response
                    await websocket.send_json({
                        "type": "response",
                        "content": result.answer,
                        "mcp_used": result.mcp_used,
                        "confidence": result.confidence,
                        "sources": result.sources,
                        "timestamp": datetime.utcnow().isoformat()
                    })

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "content": "Invalid JSON"
                })

            except Exception as e:
                logger.error(f"WebSocket error: {e}", exc_info=True)
                await websocket.send_json({
                    "type": "error",
                    "content": str(e)
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected")


# In-memory chat history (for testing)
# In production, use Redis or database
_chat_history = {}


@router.get("/chat/history")
async def get_chat_history(
    limit: int = 50,
    offset: int = 0,
    ctx: CustomerContext = Depends(require_auth)
):
    """
    Get chat history for current customer.

    Requires authentication. Returns only messages for this customer.
    """
    customer_id = ctx.customer_id

    # Get messages for this customer
    messages = _chat_history.get(customer_id, [])

    # Apply pagination
    total = len(messages)
    paginated = messages[offset:offset + limit]

    return {
        "messages": paginated,
        "total": total,
        "limit": limit,
        "offset": offset
    }
