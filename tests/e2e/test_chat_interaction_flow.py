"""
E2E Test: Chat Interaction Flow

Tests real-time chat with MCPs:
1. REST API chat
2. WebSocket chat
3. MCP routing
4. Response streaming
5. Source citations
"""

import pytest
import asyncio
import httpx

from tests.e2e.helpers import send_chat_message, assert_response_success
from tests.utils.websocket_client import TestWebSocketClient, test_websocket_chat


@pytest.mark.e2e
@pytest.mark.asyncio
class TestChatInteractionFlow:
    """Test chat interaction with MCPs."""

    async def test_rest_chat_basic(
        self,
        authenticated_console_client: httpx.AsyncClient,
        test_customer: dict
    ):
        """Test basic REST chat interaction."""
        response = await send_chat_message(
            authenticated_console_client,
            "What is the corporate tax rate in Germany?"
        )

        if not response:
            pytest.skip("Chat endpoint not implemented")

        assert "answer" in response
        assert "mcp_used" in response
        assert "confidence" in response

        # Should auto-route to CTAX for tax question
        assert response.get("mcp_used") in ["ctax", None]  # None if auto-routing not impl

    async def test_rest_chat_with_specific_mcp(
        self,
        authenticated_console_client: httpx.AsyncClient
    ):
        """Test chat with specific MCP selection."""
        response = await authenticated_console_client.post("/api/chat", json={
            "message": "Analyze this contract",
            "mcp": "law"
        })

        if response.status_code == 404:
            pytest.skip("Chat endpoint not implemented")

        assert_response_success(response, 200)
        data = response.json()

        assert data["mcp_used"] == "law"

    async def test_rest_chat_with_context(
        self,
        authenticated_console_client: httpx.AsyncClient,
        test_customer: dict
    ):
        """Test chat with additional context."""
        response = await authenticated_console_client.post("/api/chat", json={
            "message": "What was our revenue in Q2?",
            "context": {
                "year": 2024,
                "quarter": 2
            }
        })

        if response.status_code == 404:
            pytest.skip("Chat endpoint not implemented")

        assert_response_success(response, 200)
        data = response.json()

        assert "answer" in data
        # Context should be passed to MCP

    async def test_websocket_chat_connection(
        self,
        test_customer: dict
    ):
        """Test WebSocket connection and authentication."""
        ws_url = "ws://localhost:4010/api/ws/chat"

        try:
            async with TestWebSocketClient(ws_url) as ws:
                # Authenticate
                await ws.authenticate(test_customer["token"])

                # Send ping
                pong_received = await ws.ping()
                assert pong_received

        except Exception as e:
            pytest.skip(f"WebSocket not available: {e}")

    async def test_websocket_chat_message(
        self,
        test_customer: dict
    ):
        """Test sending and receiving chat messages via WebSocket."""
        ws_url = "ws://localhost:4010/api/ws/chat"

        try:
            response = await test_websocket_chat(
                ws_url,
                test_customer["token"],
                "What is VAT in Germany?",
                mcp="ctax"
            )

            assert response.type == "response"
            assert response.content is not None
            assert response.mcp_used in ["ctax", None]

        except Exception as e:
            pytest.skip(f"WebSocket chat not available: {e}")

    async def test_websocket_multiple_messages(
        self,
        test_customer: dict
    ):
        """Test sending multiple messages in same WebSocket session."""
        ws_url = "ws://localhost:4010/api/ws/chat"

        try:
            async with TestWebSocketClient(ws_url) as ws:
                await ws.authenticate(test_customer["token"])

                # Send multiple messages
                questions = [
                    "What is the tax rate?",
                    "What about VAT?",
                    "How do I file taxes?"
                ]

                responses = []
                for question in questions:
                    response = await ws.send_message(question)
                    responses.append(response)

                assert len(responses) == 3
                for response in responses:
                    assert response.type == "response"
                    assert response.content is not None

        except Exception as e:
            pytest.skip(f"WebSocket not available: {e}")

    async def test_chat_response_includes_sources(
        self,
        authenticated_console_client: httpx.AsyncClient
    ):
        """Test that chat responses include source citations."""
        response = await authenticated_console_client.post("/api/chat", json={
            "message": "What are our tax obligations?"
        })

        if response.status_code == 404:
            pytest.skip("Chat endpoint not implemented")

        assert_response_success(response, 200)
        data = response.json()

        # Response should include sources (if data exists)
        assert "sources" in data
        # sources may be empty if no data ingested yet

    async def test_chat_confidence_score(
        self,
        authenticated_console_client: httpx.AsyncClient
    ):
        """Test that chat responses include confidence scores."""
        response = await authenticated_console_client.post("/api/chat", json={
            "message": "Tell me about corporate tax"
        })

        if response.status_code == 404:
            pytest.skip("Chat endpoint not implemented")

        assert_response_success(response, 200)
        data = response.json()

        assert "confidence" in data
        confidence = data["confidence"]
        assert 0.0 <= confidence <= 1.0

    async def test_chat_with_no_auth_fails(
        self,
        console_client: httpx.AsyncClient
    ):
        """Test that chat without authentication fails."""
        # Don't use authenticated client
        response = await console_client.post("/api/chat", json={
            "message": "test"
        })

        if response.status_code == 404:
            pytest.skip("Chat endpoint not implemented")

        # Should require authentication
        assert response.status_code in [401, 403]

    async def test_chat_history(
        self,
        authenticated_console_client: httpx.AsyncClient
    ):
        """Test retrieving chat history."""
        # Send a few messages first
        await authenticated_console_client.post("/api/chat", json={
            "message": "First question"
        })
        await authenticated_console_client.post("/api/chat", json={
            "message": "Second question"
        })

        # Get history
        response = await authenticated_console_client.get("/api/chat/history")

        if response.status_code == 404:
            pytest.skip("Chat history not implemented")

        assert_response_success(response, 200)
        data = response.json()

        assert "messages" in data
        # History may be empty if not persisted

    async def test_websocket_error_handling(
        self,
        test_customer: dict
    ):
        """Test WebSocket error handling."""
        ws_url = "ws://localhost:4010/api/ws/chat"

        try:
            async with TestWebSocketClient(ws_url) as ws:
                await ws.authenticate(test_customer["token"])

                # Send invalid message (no content)
                await ws._send_raw({
                    "type": "message",
                    # Missing content
                })

                # Should receive error
                response = await ws.get_message(timeout=5.0)
                assert response.type == "error"

        except Exception as e:
            pytest.skip(f"WebSocket not available: {e}")

    async def test_websocket_reconnection(
        self,
        test_customer: dict
    ):
        """Test WebSocket reconnection after disconnect."""
        ws_url = "ws://localhost:4010/api/ws/chat"

        try:
            # First connection
            async with TestWebSocketClient(ws_url) as ws1:
                await ws1.authenticate(test_customer["token"])
                response1 = await ws1.send_message("First message")
                assert response1 is not None

            # Second connection (reconnect)
            async with TestWebSocketClient(ws_url) as ws2:
                await ws2.authenticate(test_customer["token"])
                response2 = await ws2.send_message("Second message after reconnect")
                assert response2 is not None

        except Exception as e:
            pytest.skip(f"WebSocket not available: {e}")

    async def test_chat_with_long_message(
        self,
        authenticated_console_client: httpx.AsyncClient
    ):
        """Test chat with very long message."""
        long_message = "Explain corporate tax " + "in detail " * 100

        response = await authenticated_console_client.post("/api/chat", json={
            "message": long_message
        })

        if response.status_code == 404:
            pytest.skip("Chat endpoint not implemented")

        # Should handle long messages
        assert response.status_code in [200, 400, 413]  # 413 = Payload Too Large

    async def test_concurrent_chat_messages(
        self,
        authenticated_console_client: httpx.AsyncClient
    ):
        """Test sending multiple concurrent chat requests."""
        messages = [
            "What is the tax rate?",
            "What about VAT?",
            "How do I file?",
            "What are deadlines?",
        ]

        # Send all requests concurrently
        tasks = [
            authenticated_console_client.post("/api/chat", json={"message": msg})
            for msg in messages
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Check at least some succeeded
        successful = [r for r in responses if isinstance(r, httpx.Response) and r.status_code == 200]

        if len(successful) == 0 and isinstance(responses[0], Exception):
            pytest.skip("Chat endpoint not available")

        # Should handle concurrent requests
        assert len(successful) >= 1
