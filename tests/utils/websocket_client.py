"""
Test WebSocket Client

WebSocket client for testing real-time chat.
"""

import json
import asyncio
from typing import Optional, Callable, Any, List
from dataclasses import dataclass
import websockets
from websockets.client import WebSocketClientProtocol


@dataclass
class WebSocketMessage:
    """Received WebSocket message."""
    type: str
    content: Optional[str] = None
    mcp_used: Optional[str] = None
    confidence: Optional[float] = None
    sources: Optional[List[str]] = None
    timestamp: Optional[str] = None
    raw: Optional[dict] = None


class TestWebSocketClient:
    """
    WebSocket client for testing chat.

    Example:
        async with TestWebSocketClient("ws://localhost:4010/api/ws/chat") as ws:
            await ws.authenticate(token)
            response = await ws.send_message("What's our tax liability?")
            print(response.content)
    """

    def __init__(
        self,
        url: str,
        timeout: float = 30.0,
        on_message: Optional[Callable[[WebSocketMessage], None]] = None
    ):
        """
        Initialize WebSocket client.

        Args:
            url: WebSocket URL (e.g., "ws://localhost:4010/api/ws/chat")
            timeout: Connection timeout
            on_message: Optional callback for received messages
        """
        self.url = url
        self.timeout = timeout
        self.on_message = on_message
        self.ws: Optional[WebSocketClientProtocol] = None
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._listener_task: Optional[asyncio.Task] = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def connect(self, token: Optional[str] = None):
        """
        Connect to WebSocket.

        Args:
            token: Optional JWT token (can also authenticate later)
        """
        url = self.url
        if token:
            url = f"{url}?token={token}"

        self.ws = await websockets.connect(url, ping_interval=20)
        self._listener_task = asyncio.create_task(self._listen())

    async def close(self):
        """Close WebSocket connection."""
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass

        if self.ws:
            await self.ws.close()

    async def _listen(self):
        """Listen for incoming messages (background task)."""
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    msg = self._parse_message(data)

                    # Put in queue for get_message()
                    await self._message_queue.put(msg)

                    # Call callback if provided
                    if self.on_message:
                        self.on_message(msg)

                except json.JSONDecodeError:
                    print(f"Failed to parse message: {message}")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Listener error: {e}")

    def _parse_message(self, data: dict) -> WebSocketMessage:
        """Parse raw message dict into WebSocketMessage."""
        return WebSocketMessage(
            type=data.get("type", "unknown"),
            content=data.get("content"),
            mcp_used=data.get("mcp_used"),
            confidence=data.get("confidence"),
            sources=data.get("sources"),
            timestamp=data.get("timestamp"),
            raw=data
        )

    async def authenticate(self, token: str):
        """
        Authenticate with JWT token.

        Args:
            token: JWT token
        """
        await self._send_raw({
            "type": "auth",
            "token": token
        })

        # Wait for auth response
        response = await self.get_message(timeout=5.0)
        if response.type != "auth_success":
            raise RuntimeError(f"Authentication failed: {response.content}")

    async def _send_raw(self, data: dict):
        """Send raw JSON message."""
        await self.ws.send(json.dumps(data))

    async def send_message(
        self,
        message: str,
        mcp: Optional[str] = None,
        wait_for_response: bool = True,
        timeout: float = 30.0
    ) -> Optional[WebSocketMessage]:
        """
        Send a chat message.

        Args:
            message: Chat message
            mcp: Specific MCP to use
            wait_for_response: Wait for response
            timeout: Response timeout

        Returns:
            Response message if wait_for_response=True
        """
        await self._send_raw({
            "type": "message",
            "content": message,
            "mcp": mcp
        })

        if wait_for_response:
            # Skip "status" messages, wait for "response"
            while True:
                msg = await self.get_message(timeout=timeout)
                if msg.type == "response":
                    return msg
                elif msg.type == "error":
                    raise RuntimeError(f"Chat error: {msg.content}")

        return None

    async def get_message(self, timeout: float = 30.0) -> WebSocketMessage:
        """
        Get next message from queue.

        Args:
            timeout: Timeout in seconds

        Returns:
            Next message

        Raises:
            asyncio.TimeoutError: If no message within timeout
        """
        return await asyncio.wait_for(
            self._message_queue.get(),
            timeout=timeout
        )

    async def ping(self) -> bool:
        """
        Send ping and wait for pong.

        Returns:
            True if pong received
        """
        await self._send_raw({"type": "ping"})

        try:
            response = await self.get_message(timeout=5.0)
            return response.type == "pong"
        except asyncio.TimeoutError:
            return False


async def test_websocket_chat(
    url: str,
    token: str,
    message: str,
    mcp: Optional[str] = None
) -> WebSocketMessage:
    """
    Convenience function for quick WebSocket chat test.

    Args:
        url: WebSocket URL
        token: JWT token
        message: Chat message
        mcp: Optional MCP

    Returns:
        Response message

    Example:
        response = await test_websocket_chat(
            "ws://localhost:4010/api/ws/chat",
            token,
            "What's our tax liability?"
        )
        print(response.content)
    """
    async with TestWebSocketClient(url) as ws:
        await ws.authenticate(token)
        return await ws.send_message(message, mcp=mcp)
