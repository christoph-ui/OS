"""
Test API Client

Wrapper around httpx.AsyncClient with convenience methods for testing.
"""

import httpx
from typing import Optional, Dict, Any


class TestAPIClient:
    """
    Test API client with authentication and convenience methods.

    Example:
        client = TestAPIClient("http://localhost:4080")
        await client.authenticate("test@example.com", "password")
        response = await client.get("/api/customers")
    """

    def __init__(self, base_url: str, timeout: float = 30.0):
        """
        Initialize test API client.

        Args:
            base_url: Base URL for API (e.g., "http://localhost:4080")
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self.client = httpx.AsyncClient(base_url=base_url, timeout=timeout)
        self.token: Optional[str] = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    def set_token(self, token: str):
        """
        Set authentication token.

        Args:
            token: JWT token
        """
        self.token = token
        self.client.headers.update({"Authorization": f"Bearer {token}"})

    async def authenticate(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login and set authentication token.

        Args:
            email: User email
            password: User password

        Returns:
            Login response dict with token

        Raises:
            httpx.HTTPStatusError: If login fails
        """
        response = await self.client.post("/api/auth/login", json={
            "email": email,
            "password": password
        })
        response.raise_for_status()

        data = response.json()
        token = data.get("token") or data.get("access_token")

        if token:
            self.set_token(token)

        return data

    async def signup(
        self,
        email: str,
        password: str,
        company_name: str,
        contact_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new customer account.

        Args:
            email: User email
            password: User password
            company_name: Company name
            contact_name: Contact person name

        Returns:
            Signup response dict
        """
        response = await self.client.post("/api/auth/signup", json={
            "email": email,
            "password": password,
            "company_name": company_name,
            "contact_name": contact_name or "Test User"
        })
        response.raise_for_status()
        return response.json()

    async def get(self, path: str, **kwargs) -> httpx.Response:
        """
        Send GET request.

        Args:
            path: API path (e.g., "/api/customers")
            **kwargs: Additional arguments for httpx.get()

        Returns:
            HTTP response
        """
        return await self.client.get(path, **kwargs)

    async def post(self, path: str, **kwargs) -> httpx.Response:
        """
        Send POST request.

        Args:
            path: API path
            **kwargs: Additional arguments for httpx.post()

        Returns:
            HTTP response
        """
        return await self.client.post(path, **kwargs)

    async def put(self, path: str, **kwargs) -> httpx.Response:
        """Send PUT request."""
        return await self.client.put(path, **kwargs)

    async def patch(self, path: str, **kwargs) -> httpx.Response:
        """Send PATCH request."""
        return await self.client.patch(path, **kwargs)

    async def delete(self, path: str, **kwargs) -> httpx.Response:
        """Send DELETE request."""
        return await self.client.delete(path, **kwargs)

    async def health_check(self) -> bool:
        """
        Check if API is healthy.

        Returns:
            True if API is responding, False otherwise
        """
        try:
            response = await self.client.get("/health", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False


class TestConsoleClient(TestAPIClient):
    """
    Test client for Console Backend API.

    Inherits from TestAPIClient with console-specific methods.
    """

    async def send_chat(
        self,
        message: str,
        mcp: Optional[str] = None,
        context: Optional[dict] = None
    ) -> Dict[str, Any]:
        """
        Send a chat message.

        Args:
            message: Chat message
            mcp: Specific MCP to use (None for auto-routing)
            context: Additional context

        Returns:
            Chat response dict
        """
        response = await self.post("/api/chat", json={
            "message": message,
            "mcp": mcp,
            "context": context
        })
        response.raise_for_status()
        return response.json()

    async def start_ingestion(
        self,
        path: str,
        mcp: Optional[str] = None,
        recursive: bool = True,
        file_types: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Start data ingestion.

        Args:
            path: Path to data folder
            mcp: Target MCP
            recursive: Scan recursively
            file_types: File extensions to include

        Returns:
            Ingestion job response
        """
        response = await self.post("/api/ingest", json={
            "path": path,
            "mcp": mcp,
            "recursive": recursive,
            "file_types": file_types
        })
        response.raise_for_status()
        return response.json()

    async def get_ingestion_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get ingestion job status.

        Args:
            job_id: Job ID

        Returns:
            Job status dict
        """
        response = await self.get(f"/api/ingest/{job_id}/status")
        response.raise_for_status()
        return response.json()

    async def list_mcps(self) -> Dict[str, Any]:
        """
        List available MCPs.

        Returns:
            MCPs list dict
        """
        response = await self.get("/api/mcps/list")
        response.raise_for_status()
        return response.json()

    async def search_data(
        self,
        query: str,
        limit: int = 10,
        mcp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search data in lakehouse.

        Args:
            query: Search query
            limit: Max results
            mcp: Filter by MCP

        Returns:
            Search results dict
        """
        response = await self.get("/api/data/search", params={
            "q": query,
            "limit": limit,
            "mcp": mcp
        })
        response.raise_for_status()
        return response.json()
