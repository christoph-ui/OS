"""
Medusa download routes
Handles registration and download for 0711 Medusa app
"""

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid
from datetime import datetime
import os

from ..database import get_db
from ..models.medusa_registration import MedusaRegistration
from ..services.email_service import EmailService
from ..config import settings

router = APIRouter()


class MedusaRegistrationRequest(BaseModel):
    """Medusa registration request"""
    email: EmailStr
    full_name: str
    company: Optional[str] = None
    phone: str
    address: str
    city: str
    postal_code: str
    country: str


class MedusaRegistrationResponse(BaseModel):
    """Medusa registration response"""
    success: bool
    message: str
    download_token: str


async def send_download_notification(email: str, full_name: str, company: Optional[str]):
    """Send email notification to christoph@0711.io about download"""
    try:
        email_service = EmailService()
        await email_service.send_email(
            to_email="christoph@0711.io",
            subject=f"🎉 New Medusa Download: {full_name}",
            html_content=f"""
            <h2>New Medusa Download</h2>
            <p><strong>Name:</strong> {full_name}</p>
            <p><strong>Email:</strong> {email}</p>
            <p><strong>Company:</strong> {company or 'N/A'}</p>
            <p><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
            """
        )
    except Exception as e:
        # Don't fail the registration if email fails
        print(f"Failed to send download notification: {e}")


@router.post("/register", response_model=MedusaRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_for_download(
    registration: MedusaRegistrationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Register for Medusa download

    Creates a registration record and returns a download token
    """

    # Check if email already registered
    existing = db.query(MedusaRegistration).filter(
        MedusaRegistration.email == registration.email
    ).first()

    if existing:
        # Return existing token
        return MedusaRegistrationResponse(
            success=True,
            message="You're already registered! Use the link below to download.",
            download_token=existing.id
        )

    # Create new registration
    new_registration = MedusaRegistration(
        id=str(uuid.uuid4()),
        email=registration.email,
        full_name=registration.full_name,
        company=registration.company,
        phone=registration.phone,
        address=registration.address,
        city=registration.city,
        postal_code=registration.postal_code,
        country=registration.country,
        download_count=0
    )

    db.add(new_registration)
    db.commit()
    db.refresh(new_registration)

    # Send notification email in background
    background_tasks.add_task(
        send_download_notification,
        registration.email,
        registration.full_name,
        registration.company
    )

    return MedusaRegistrationResponse(
        success=True,
        message="Registration successful! You can now download Medusa.",
        download_token=new_registration.id
    )


@router.get("/download/{token}")
async def download_medusa(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Download Medusa app with valid token

    Increments download count and returns the Mac app file
    """

    # Verify token exists
    registration = db.query(MedusaRegistration).filter(
        MedusaRegistration.id == token
    ).first()

    if not registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid download token"
        )

    # Increment download count
    registration.download_count += 1
    registration.updated_at = datetime.utcnow()
    db.commit()

    # Path to the Mac app (zip file)
    app_path = "/home/christoph.bertsch/0711/0711-OS/apps/website/public/medusa/0711-Medusa-mac-arm64.zip"

    if not os.path.exists(app_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download file not available"
        )

    return FileResponse(
        app_path,
        media_type="application/zip",
        filename="0711-Medusa-mac-arm64.zip"
    )
