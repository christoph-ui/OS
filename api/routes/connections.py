"""
Connection Management API Routes
Handles MCP connections (OAuth, API keys, databases, service accounts)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from ..database import get_db
from ..models import ConnectionCredential, ConnectionType, ConnectionStatus, User
from ..services.connection_manager import ConnectionManager
from ..utils.security import get_current_user

router = APIRouter(prefix="/api/connections", tags=["connections"])


# ===== Request Models =====

class OAuthConnectionRequest(BaseModel):
    """Request to initiate OAuth connection"""
    mcp_id: str = Field(..., description="MCP UUID")
    provider_name: str = Field(..., description="OAuth provider (salesforce, google, etc.)")
    shop_domain: Optional[str] = Field(None, description="Shopify shop domain (only for Shopify)")


class APIKeyConnectionRequest(BaseModel):
    """Request to create API key connection"""
    mcp_id: str = Field(..., description="MCP UUID")
    api_key: str = Field(..., description="API key")
    api_secret: Optional[str] = Field(None, description="API secret (optional)")
    connection_name: Optional[str] = Field(None, description="Custom connection name")
    test_connection: bool = Field(True, description="Test connection before saving")


class DatabaseConnectionRequest(BaseModel):
    """Request to create database connection"""
    mcp_id: str = Field(..., description="MCP UUID")
    host: str = Field(..., description="Database host")
    port: int = Field(..., description="Database port")
    username: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")
    database: str = Field(..., description="Database name")
    ssl_mode: str = Field("prefer", description="SSL mode (prefer, require, disable)")
    connection_name: Optional[str] = Field(None, description="Custom connection name")
    test_connection: bool = Field(True, description="Test connection before saving")


class ServiceAccountConnectionRequest(BaseModel):
    """Request to create service account connection"""
    mcp_id: str = Field(..., description="MCP UUID")
    service_account_json: dict = Field(..., description="Service account JSON key")
    project_id: Optional[str] = Field(None, description="GCP project ID (optional)")
    connection_name: Optional[str] = Field(None, description="Custom connection name")


# ===== Response Models =====

class ConnectionResponse(BaseModel):
    """Connection credential response"""
    id: str
    customer_id: str
    mcp_id: str
    connection_type: str
    connection_name: str
    oauth_provider: Optional[str] = None
    oauth_scopes: Optional[List[str]] = None
    connection_metadata: Optional[dict] = None
    status: str
    health_status: str
    last_health_check: Optional[datetime] = None
    last_successful_use: Optional[datetime] = None
    error_count: int
    last_error_message: Optional[str] = None
    total_api_calls: int
    created_at: datetime
    token_expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OAuthConnectionResponse(BaseModel):
    """OAuth connection initiation response"""
    authorization_url: str
    state: str
    connection_id: str


class TestConnectionResponse(BaseModel):
    """Connection test response"""
    success: bool
    response_time_ms: Optional[int] = None
    error: Optional[str] = None


# ===== Endpoints =====

@router.post("/oauth/start", response_model=OAuthConnectionResponse)
async def initiate_oauth_connection(
    request_data: OAuthConnectionRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initiate OAuth2 connection flow

    Returns authorization URL for user to visit
    """
    manager = ConnectionManager(db)

    try:
        result = await manager.initiate_oauth_connection(
            customer_id=str(current_user.customer_id),
            mcp_id=request_data.mcp_id,
            provider_name=request_data.provider_name,
            user_id=str(current_user.id),
            shop_domain=request_data.shop_domain,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent")
        )

        # Store state_data in session or Redis for callback
        # For now, return it (in production, use Redis)
        request.session["oauth_state_data"] = result["state_data"]

        return OAuthConnectionResponse(
            authorization_url=result["authorization_url"],
            state=result["state"],
            connection_id=result["connection_id"]
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate OAuth flow: {str(e)}")


@router.get("/oauth/callback/{provider}")
async def oauth_callback(
    provider: str,
    code: str,
    state: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle OAuth2 callback

    This endpoint is called by the OAuth provider after user authorization
    """
    manager = ConnectionManager(db)

    try:
        # Retrieve state_data from session (in production, use Redis)
        state_data = request.session.get("oauth_state_data", {})

        if not state_data:
            raise HTTPException(status_code=400, detail="Invalid session or expired state")

        # Handle callback
        connection = await manager.handle_oauth_callback(
            provider_name=provider,
            code=code,
            state=state,
            state_data=state_data,
            shop_domain=state_data.get("shop_domain")
        )

        # Clear state from session
        request.session.pop("oauth_state_data", None)

        # Redirect to success page (frontend)
        return {
            "success": True,
            "message": "Connection successful",
            "connection_id": str(connection.id),
            "redirect_url": f"/connections?success=true&connection_id={connection.id}"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {str(e)}")


@router.post("/api-key", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key_connection(
    request_data: APIKeyConnectionRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create API key connection

    Tests the API key and stores encrypted credentials
    """
    manager = ConnectionManager(db)

    try:
        connection = await manager.create_api_key_connection(
            customer_id=str(current_user.customer_id),
            mcp_id=request_data.mcp_id,
            api_key=request_data.api_key,
            api_secret=request_data.api_secret,
            user_id=str(current_user.id),
            connection_name=request_data.connection_name,
            test_connection=request_data.test_connection,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent")
        )

        return ConnectionResponse.from_orm(connection)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create API key connection: {str(e)}")


@router.post("/database", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_database_connection(
    request_data: DatabaseConnectionRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create database connection

    Tests the database connection and stores encrypted credentials
    """
    manager = ConnectionManager(db)

    try:
        connection = await manager.create_database_connection(
            customer_id=str(current_user.customer_id),
            mcp_id=request_data.mcp_id,
            host=request_data.host,
            port=request_data.port,
            username=request_data.username,
            password=request_data.password,
            database=request_data.database,
            ssl_mode=request_data.ssl_mode,
            user_id=str(current_user.id),
            connection_name=request_data.connection_name,
            test_connection=request_data.test_connection,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent")
        )

        return ConnectionResponse.from_orm(connection)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create database connection: {str(e)}")


@router.get("/", response_model=List[ConnectionResponse])
async def list_connections(
    status_filter: Optional[str] = None,
    connection_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all connections for current customer

    Optional filters:
    - status: Filter by connection status (active, expired, invalid, etc.)
    - connection_type: Filter by connection type (oauth2, api_key, database, etc.)
    """
    manager = ConnectionManager(db)

    try:
        # Parse filters
        status_enum = ConnectionStatus(status_filter) if status_filter else None
        type_enum = ConnectionType(connection_type) if connection_type else None

        connections = manager.list_connections(
            customer_id=str(current_user.customer_id),
            status=status_enum,
            connection_type=type_enum
        )

        return [ConnectionResponse.from_orm(conn) for conn in connections]

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list connections: {str(e)}")


@router.get("/{connection_id}", response_model=ConnectionResponse)
async def get_connection(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get connection details

    Returns connection metadata (credentials are NOT returned for security)
    """
    connection = db.query(ConnectionCredential).filter(
        ConnectionCredential.id == connection_id,
        ConnectionCredential.customer_id == current_user.customer_id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    return ConnectionResponse.from_orm(connection)


@router.post("/{connection_id}/test", response_model=TestConnectionResponse)
async def test_connection(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Test connection health

    Makes a test API call to verify credentials are still valid
    """
    # Verify ownership
    connection = db.query(ConnectionCredential).filter(
        ConnectionCredential.id == connection_id,
        ConnectionCredential.customer_id == current_user.customer_id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    manager = ConnectionManager(db)

    try:
        result = await manager.test_connection(connection_id)
        return TestConnectionResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")


@router.patch("/{connection_id}/refresh", response_model=ConnectionResponse)
async def refresh_connection(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Refresh OAuth2 access token

    Only works for OAuth2 connections with refresh tokens
    """
    # Verify ownership
    connection = db.query(ConnectionCredential).filter(
        ConnectionCredential.id == connection_id,
        ConnectionCredential.customer_id == current_user.customer_id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    manager = ConnectionManager(db)

    try:
        updated_connection = await manager.refresh_oauth_token(connection_id)
        return ConnectionResponse.from_orm(updated_connection)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token refresh failed: {str(e)}")


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete connection and revoke credentials

    This is a soft delete - credentials are marked as REVOKED but not physically deleted
    """
    # Verify ownership
    connection = db.query(ConnectionCredential).filter(
        ConnectionCredential.id == connection_id,
        ConnectionCredential.customer_id == current_user.customer_id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    manager = ConnectionManager(db)

    try:
        manager.delete_connection(connection_id)
        return None

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete connection: {str(e)}")


@router.get("/providers/oauth", response_model=List[dict])
async def list_oauth_providers():
    """
    List all configured OAuth2 providers

    Returns provider names, display names, and whether they're configured
    """
    from ..services.oauth2_service import get_oauth2_service

    oauth_service = get_oauth2_service()
    providers = oauth_service.list_providers()

    return providers
