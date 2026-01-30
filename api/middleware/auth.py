"""
Authentication middleware for API access
"""

from fastapi import HTTPException, Security, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from ..config import settings

security = HTTPBearer(auto_error=False)


async def verify_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> bool:
    """
    Verify API key from Next.js or other clients

    Usage:
        @router.post("/tasks")
        async def create_task(
            task: TaskCreate,
            authenticated: bool = Depends(verify_api_key),
            db: Session = Depends(get_db)
        ):
            ...

    Headers:
        Authorization: Bearer <FASTAPI_API_KEY>
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials.credentials != settings.fastapi_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return True


async def optional_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> bool:
    """Optional API key verification (doesn't raise error if missing)"""
    if not credentials:
        return False

    return credentials.credentials == settings.fastapi_api_key
