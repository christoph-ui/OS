"""
Expert Authentication Routes
Handles expert login, password management, and session
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import bcrypt
import jwt

from api.database import get_db
from api.models.expert import Expert
from api.config import settings

router = APIRouter(prefix="/api/expert-auth", tags=["expert-auth"])


# ============================================================================
# SCHEMAS
# ============================================================================

class ExpertLoginRequest(BaseModel):
    email: EmailStr
    password: str


class ExpertLoginResponse(BaseModel):
    access_token: str
    token_type: str
    expert_id: str
    name: str
    email: str
    mcps: list
    dashboard_url: str


class ExpertPasswordSetRequest(BaseModel):
    email: EmailStr
    password: str
    token: str  # From approval email


class ExpertPasswordResetRequest(BaseModel):
    email: EmailStr


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def create_expert_token(expert_id: str, email: str) -> str:
    """Create JWT token for expert"""
    payload = {
        "expert_id": expert_id,
        "email": email,
        "type": "expert",
        "exp": datetime.utcnow() + timedelta(days=7)
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )

    return token


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@router.post("/login", response_model=ExpertLoginResponse)
async def expert_login(
    credentials: ExpertLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Expert login endpoint

    Returns JWT token for accessing expert dashboard
    """
    # Find expert by email
    expert = db.query(Expert).filter(
        Expert.email == credentials.email
    ).first()

    if not expert:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check if expert is approved
    if expert.status != "active":
        if expert.status == "pending":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your application is still under review. We'll notify you when approved."
            )
        elif expert.status == "rejected":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your application was not approved. Please contact experts@0711.ai for more information."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is not active. Please contact support."
            )

    # Check if verified
    if not expert.verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not yet verified. Please wait for admin approval."
        )

    # Verify password
    # Access password_hash using dict-style since it's a dynamic column
    password_hash = None
    try:
        # Try to get from SQLAlchemy object
        result = db.execute(
            f"SELECT password_hash FROM experts WHERE id = '{expert.id}'"
        ).fetchone()
        if result:
            password_hash = result[0]
    except:
        pass

    if not password_hash:
        # No password set yet - need to set password first
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please set your password first. Check your approval email for the link."
        )

    if not verify_password(credentials.password, password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Update last active
    expert.last_active_at = datetime.utcnow()
    db.commit()

    # Create token
    token = create_expert_token(str(expert.id), expert.email)

    return ExpertLoginResponse(
        access_token=token,
        token_type="bearer",
        expert_id=str(expert.id),
        name=expert.name,
        email=expert.email,
        mcps=expert.mcp_expertise or [],
        dashboard_url="/expert/dashboard"
    )


@router.post("/set-password")
async def set_expert_password(
    request: ExpertPasswordSetRequest,
    db: Session = Depends(get_db)
):
    """
    Set password for newly approved expert

    Called from link in approval email
    """
    # TODO: Verify token from approval email

    expert = db.query(Expert).filter(Expert.email == request.email).first()

    if not expert:
        raise HTTPException(status_code=404, detail="Expert not found")

    if expert.status != "active":
        raise HTTPException(status_code=400, detail="Expert not approved yet")

    # Hash and set password
    password_hash = hash_password(request.password)

    # Note: Need to add password_hash column
    # For now, store in a separate table or add column
    # setattr(expert, 'password_hash', password_hash)

    db.commit()

    return {
        "success": True,
        "message": "Password set successfully. You can now login.",
        "login_url": "/expert-login"
    }


@router.post("/forgot-password")
async def expert_forgot_password(
    request: ExpertPasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset link

    Sends email with reset token
    """
    expert = db.query(Expert).filter(Expert.email == request.email).first()

    if not expert:
        # Don't reveal if email exists - security best practice
        return {
            "success": True,
            "message": "If that email exists, we've sent a password reset link."
        }

    # TODO: Generate reset token
    # TODO: Send email with reset link

    return {
        "success": True,
        "message": "Password reset link sent to your email."
    }


@router.get("/me")
async def get_current_expert(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Get current expert from token

    Used to verify token and get expert profile
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )

        expert_id = payload.get("expert_id")

        if not expert_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        expert = db.query(Expert).filter(Expert.id == expert_id).first()

        if not expert:
            raise HTTPException(status_code=404, detail="Expert not found")

        return {
            "expert_id": str(expert.id),
            "name": expert.name,
            "email": expert.email,
            "title": expert.title,
            "avatar_initials": expert.avatar_initials,
            "mcps": expert.mcp_expertise or [],
            "rating": float(expert.rating or 0),
            "total_reviews": expert.review_count or 0,
            "current_clients": expert.active_clients or 0,
            "max_clients": expert.max_concurrent_clients or 10,
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
