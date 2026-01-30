"""
Onboarding Wizard API Routes

Provides endpoints for the wizard UI and file uploads.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Form
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel
import logging

from ..utils.security import get_current_user, get_current_customer
from ..models.user import User
from ..models.customer import Customer

# Import the wizard
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.concierge.wizard import OnboardingWizard

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/onboarding-wizard", tags=["onboarding-wizard"])

# In-memory wizard sessions (would be Redis in production)
wizard_sessions: dict[str, OnboardingWizard] = {}


class WizardStartRequest(BaseModel):
    """Start a new wizard session"""
    pass


class WizardStepSubmitRequest(BaseModel):
    """Submit data for current step"""
    data: dict


class WizardChatRequest(BaseModel):
    """Send a chat message"""
    message: str


def get_or_create_wizard(session_id: str, customer_id: Optional[UUID] = None) -> OnboardingWizard:
    """Get existing wizard or create new one"""
    if session_id not in wizard_sessions:
        wizard_sessions[session_id] = OnboardingWizard(customer_id)
    return wizard_sessions[session_id]


@router.post("/start")
async def start_wizard(
    user: User = Depends(get_current_user),
):
    """
    Start a new onboarding wizard session
    
    Returns the wizard state and first step content.
    """
    wizard = OnboardingWizard(user.customer_id)
    session_id = str(wizard.session_id)
    wizard_sessions[session_id] = wizard
    
    # Get first step content
    state = wizard.get_state()
    content = await wizard._get_step_content()
    
    return {
        "session_id": session_id,
        "state": state.to_dict(),
        "content": content,
    }


@router.get("/{session_id}/state")
async def get_wizard_state(
    session_id: str,
    user: User = Depends(get_current_user),
):
    """Get current wizard state"""
    if session_id not in wizard_sessions:
        raise HTTPException(status_code=404, detail="Wizard session not found")
    
    wizard = wizard_sessions[session_id]
    state = wizard.get_state()
    content = await wizard._get_step_content()
    
    return {
        "state": state.to_dict(),
        "content": content,
    }


@router.post("/{session_id}/next")
async def wizard_next_step(
    session_id: str,
    request: Optional[WizardStepSubmitRequest] = None,
    user: User = Depends(get_current_user),
):
    """Move to next wizard step"""
    if session_id not in wizard_sessions:
        raise HTTPException(status_code=404, detail="Wizard session not found")
    
    wizard = wizard_sessions[session_id]
    result = await wizard.next_step(request.data if request else None)
    
    return result


@router.post("/{session_id}/previous")
async def wizard_previous_step(
    session_id: str,
    user: User = Depends(get_current_user),
):
    """Move to previous wizard step"""
    if session_id not in wizard_sessions:
        raise HTTPException(status_code=404, detail="Wizard session not found")
    
    wizard = wizard_sessions[session_id]
    result = await wizard.previous_step()
    
    return result


@router.post("/{session_id}/submit")
async def wizard_submit_step(
    session_id: str,
    request: WizardStepSubmitRequest,
    user: User = Depends(get_current_user),
):
    """Submit data for current step and advance"""
    if session_id not in wizard_sessions:
        raise HTTPException(status_code=404, detail="Wizard session not found")
    
    wizard = wizard_sessions[session_id]
    result = await wizard.submit_step(request.data)
    
    return result


@router.post("/{session_id}/upload")
async def wizard_upload_file(
    session_id: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """
    Upload a file during onboarding
    
    Accepts: XML (BMECat), CSV, Excel, PDF, ZIP (images)
    Returns analysis results and connector suggestions.
    """
    if session_id not in wizard_sessions:
        raise HTTPException(status_code=404, detail="Wizard session not found")
    
    wizard = wizard_sessions[session_id]
    
    # Read file content
    content = await file.read()
    
    # Analyze file
    result = await wizard.upload_file(file.filename, content)
    
    logger.info(f"Uploaded file {file.filename} ({len(content)} bytes) for session {session_id}")
    
    return result


@router.post("/{session_id}/chat")
async def wizard_chat(
    session_id: str,
    request: WizardChatRequest,
    user: User = Depends(get_current_user),
):
    """
    Send a chat message to the onboarding assistant
    
    The assistant can answer questions and provide guidance.
    """
    if session_id not in wizard_sessions:
        raise HTTPException(status_code=404, detail="Wizard session not found")
    
    wizard = wizard_sessions[session_id]
    response = await wizard.chat(request.message)
    
    return {
        "message": request.message,
        "response": response,
    }


@router.post("/{session_id}/start-import")
async def wizard_start_import(
    session_id: str,
    user: User = Depends(get_current_user),
):
    """
    Start the import process
    
    Hands off to the Import Agent and begins processing.
    """
    if session_id not in wizard_sessions:
        raise HTTPException(status_code=404, detail="Wizard session not found")
    
    wizard = wizard_sessions[session_id]
    result = await wizard.start_import()
    
    return result


@router.get("/{session_id}/import-status")
async def wizard_import_status(
    session_id: str,
    user: User = Depends(get_current_user),
):
    """Get import job status"""
    if session_id not in wizard_sessions:
        raise HTTPException(status_code=404, detail="Wizard session not found")
    
    wizard = wizard_sessions[session_id]
    
    # Would get real status from Import Agent
    return {
        "status": "running",
        "progress": {
            "percent": 45,
            "current_file": "catalog.xml",
            "processed": 5600,
            "total": 12450,
        },
        "results": {
            "successful": 5500,
            "needs_review": 100,
            "failed": 0,
        }
    }


@router.delete("/{session_id}")
async def wizard_cancel(
    session_id: str,
    user: User = Depends(get_current_user),
):
    """Cancel and delete wizard session"""
    if session_id in wizard_sessions:
        del wizard_sessions[session_id]
    
    return {"message": "Wizard session cancelled"}


# Public endpoint for demo/testing
@router.post("/demo/start")
async def start_demo_wizard():
    """Start a demo wizard without authentication"""
    wizard = OnboardingWizard(None)
    session_id = str(wizard.session_id)
    wizard_sessions[session_id] = wizard
    
    state = wizard.get_state()
    content = await wizard._get_step_content()
    
    return {
        "session_id": session_id,
        "state": state.to_dict(),
        "content": content,
    }
