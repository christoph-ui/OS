"""
Onboarding Wizard - The UI/Conversation Layer

This is the wizard interface that guides users through onboarding.
Can be used in:
- Console Frontend (React component talks to this)
- Chat interface (streaming responses)
- API (step-by-step endpoints)
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from .agent import ConciergeAgent, OnboardingStage, UploadedFile

logger = logging.getLogger(__name__)


@dataclass
class WizardStep:
    """A step in the wizard"""
    id: str
    title: str
    description: str
    stage: OnboardingStage
    is_current: bool = False
    is_complete: bool = False
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WizardState:
    """Current state of the wizard"""
    session_id: UUID
    customer_id: Optional[UUID]
    current_step: int
    steps: List[WizardStep]
    uploaded_files: List[UploadedFile]
    suggestions: List[Dict[str, Any]]
    import_job_id: Optional[UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": str(self.session_id),
            "customer_id": str(self.customer_id) if self.customer_id else None,
            "current_step": self.current_step,
            "steps": [
                {
                    "id": s.id,
                    "title": s.title,
                    "description": s.description,
                    "is_current": s.is_current,
                    "is_complete": s.is_complete,
                }
                for s in self.steps
            ],
            "files": [
                {
                    "filename": f.filename,
                    "type": f.file_type.value,
                    "size": f.size_bytes,
                    "records": f.record_count,
                    "quality": f.quality_score,
                    "issues": f.issues,
                }
                for f in self.uploaded_files
            ],
            "suggestions": self.suggestions,
            "import_job_id": str(self.import_job_id) if self.import_job_id else None,
        }


class OnboardingWizard:
    """
    The Wizard Interface
    
    Manages the step-by-step onboarding flow and coordinates with
    the Concierge Agent for intelligence.
    """
    
    WIZARD_STEPS = [
        WizardStep(
            id="welcome",
            title="Willkommen",
            description="Lassen Sie uns loslegen!",
            stage=OnboardingStage.WELCOME,
        ),
        WizardStep(
            id="company",
            title="Ihr Unternehmen",
            description="Erzählen Sie uns von Ihrem Geschäft",
            stage=OnboardingStage.COMPANY_PROFILE,
        ),
        WizardStep(
            id="upload",
            title="Daten hochladen",
            description="Laden Sie Ihre Produktdaten hoch",
            stage=OnboardingStage.DATA_UPLOAD,
        ),
        WizardStep(
            id="analysis",
            title="Analyse",
            description="Wir analysieren Ihre Daten",
            stage=OnboardingStage.DATA_ANALYSIS,
        ),
        WizardStep(
            id="connectors",
            title="Kanäle",
            description="Wählen Sie Ihre Vertriebskanäle",
            stage=OnboardingStage.CONNECTOR_SUGGESTIONS,
        ),
        WizardStep(
            id="credentials",
            title="Zugangsdaten",
            description="Verbinden Sie Ihre Accounts",
            stage=OnboardingStage.CREDENTIALS,
        ),
        WizardStep(
            id="import",
            title="Import",
            description="Ihre Daten werden verarbeitet",
            stage=OnboardingStage.IMPORT_HANDOFF,
        ),
        WizardStep(
            id="complete",
            title="Fertig!",
            description="Alles eingerichtet",
            stage=OnboardingStage.COMPLETE,
        ),
    ]
    
    def __init__(self, customer_id: Optional[UUID] = None):
        self.session_id = uuid4()
        self.customer_id = customer_id
        self.current_step = 0
        self.steps = [WizardStep(**{**step.__dict__}) for step in self.WIZARD_STEPS]
        self.steps[0].is_current = True
        
        self.agent = ConciergeAgent(customer_id or uuid4())
        self.uploaded_files: List[UploadedFile] = []
        self.suggestions: List[Dict[str, Any]] = []
        
    def get_state(self) -> WizardState:
        """Get current wizard state"""
        return WizardState(
            session_id=self.session_id,
            customer_id=self.customer_id,
            current_step=self.current_step,
            steps=self.steps,
            uploaded_files=self.uploaded_files,
            suggestions=self.suggestions,
        )
    
    async def next_step(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Move to next step"""
        if self.current_step >= len(self.steps) - 1:
            return {"error": "Already at last step"}
        
        # Mark current as complete
        self.steps[self.current_step].is_complete = True
        self.steps[self.current_step].is_current = False
        
        if data:
            self.steps[self.current_step].data = data
        
        # Move to next
        self.current_step += 1
        self.steps[self.current_step].is_current = True
        
        # Get step content from agent
        content = await self._get_step_content()
        
        return {
            "state": self.get_state().to_dict(),
            "content": content,
        }
    
    async def previous_step(self) -> Dict[str, Any]:
        """Move to previous step"""
        if self.current_step <= 0:
            return {"error": "Already at first step"}
        
        self.steps[self.current_step].is_current = False
        self.current_step -= 1
        self.steps[self.current_step].is_current = True
        self.steps[self.current_step].is_complete = False
        
        content = await self._get_step_content()
        
        return {
            "state": self.get_state().to_dict(),
            "content": content,
        }
    
    async def submit_step(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit data for current step"""
        step = self.steps[self.current_step]
        step.data = data
        
        # Process based on step
        if step.id == "company":
            # Extract company profile
            self.agent.company_profile = data
            
        elif step.id == "upload":
            # Files were already processed via upload_file
            pass
            
        elif step.id == "connectors":
            # Store selected connectors
            selected = data.get("selected_connectors", [])
            self.suggestions = [s for s in self.suggestions if s["id"] in selected]
            
        elif step.id == "credentials":
            # Store credentials (encrypted in production)
            for connector_id, creds in data.get("credentials", {}).items():
                self.agent.credentials[connector_id] = creds
        
        return await self.next_step()
    
    async def upload_file(self, filename: str, content: bytes) -> Dict[str, Any]:
        """Handle file upload"""
        analysis = await self.agent.analyze_file(filename, content)
        self.uploaded_files.append(analysis)
        
        # After file upload, generate suggestions
        self.suggestions = await self._generate_suggestions()
        
        return {
            "file": {
                "filename": analysis.filename,
                "type": analysis.file_type.value,
                "size": analysis.size_bytes,
                "records": analysis.record_count,
                "quality": analysis.quality_score,
                "issues": analysis.issues,
                "suggestions": analysis.suggestions,
            },
            "total_files": len(self.uploaded_files),
            "connector_suggestions": self.suggestions,
        }
    
    async def chat(self, message: str) -> str:
        """Send a chat message to the agent"""
        return await self.agent.process_message(message)
    
    async def start_import(self) -> Dict[str, Any]:
        """Start the import process"""
        # This would dispatch to Import Agent
        import_job_id = uuid4()
        
        # Create context brief
        brief = self.agent._create_context_brief()
        
        # In production: send to queue
        # await queue.publish("import_jobs", brief.to_dict())
        
        return {
            "import_job_id": str(import_job_id),
            "status": "started",
            "message": "Import gestartet! Sie werden benachrichtigt, wenn er fertig ist.",
        }
    
    async def _get_step_content(self) -> Dict[str, Any]:
        """Get content for current step"""
        step = self.steps[self.current_step]
        
        content = {
            "title": step.title,
            "description": step.description,
        }
        
        if step.id == "welcome":
            content["message"] = """
Willkommen bei 0711 Intelligence!

Ich begleite Sie durch die Einrichtung Ihrer Produktdaten. 
In wenigen Minuten sind Sie bereit für:

✨ **Automatisierte Produktbeschreibungen**
🔗 **Marktplatz-Integration** (Amazon, Google Shopping)
📊 **DATANORM & BMECat Export**
🎯 **Ausschreibungen finden** (TENDER)

Lassen Sie uns loslegen!
"""
            
        elif step.id == "company":
            content["fields"] = [
                {"name": "company_name", "label": "Firmenname", "type": "text", "required": True},
                {"name": "business_type", "label": "Geschäftsmodell", "type": "select", "options": [
                    {"value": "b2b_distributor", "label": "B2B Distributor"},
                    {"value": "b2b_manufacturer", "label": "Hersteller"},
                    {"value": "b2c_retailer", "label": "B2C Einzelhandel"},
                ]},
                {"name": "industry", "label": "Branche", "type": "select", "options": [
                    {"value": "elektro", "label": "Elektrotechnik"},
                    {"value": "sanitaer", "label": "Sanitär & Heizung"},
                    {"value": "automotive", "label": "Automotive"},
                    {"value": "industrie", "label": "Industriebedarf"},
                ]},
                {"name": "product_count", "label": "Anzahl Produkte (ca.)", "type": "number"},
            ]
            
        elif step.id == "upload":
            content["dropzone"] = True
            content["accepted_formats"] = [
                ".xml", ".csv", ".xlsx", ".xls", ".pdf", ".zip"
            ]
            content["message"] = """
Laden Sie Ihre Produktdaten hoch. Ich erkenne automatisch:

📄 **BMECat XML** - Alle Versionen
📊 **CSV / Excel** - Produktlisten
🏷️ **ETIM Preislisten** - XML oder Excel
📁 **DATANORM** - 4.0 und 5.0
📸 **Bilder** - ZIP-Archiv

Sie können mehrere Dateien hochladen!
"""
            content["uploaded_files"] = [
                {
                    "filename": f.filename,
                    "type": f.file_type.value,
                    "records": f.record_count,
                    "quality": f.quality_score,
                }
                for f in self.uploaded_files
            ]
            
        elif step.id == "analysis":
            content["analysis"] = await self._get_analysis_content()
            
        elif step.id == "connectors":
            content["suggestions"] = self.suggestions
            content["message"] = "Basierend auf Ihren Daten empfehle ich folgende Kanäle:"
            
        elif step.id == "credentials":
            content["required_credentials"] = self._get_required_credentials()
            
        elif step.id == "import":
            content["progress"] = {
                "status": "running",
                "percent": 0,
                "message": "Import wird vorbereitet...",
            }
            
        elif step.id == "complete":
            content["message"] = """
🎉 **Alles eingerichtet!**

Ihre Produktdaten wurden erfolgreich importiert und sind bereit für:

✅ Automatische Produktbeschreibungen
✅ Marktplatz-Synchronisation
✅ DATANORM-Export

**Nächste Schritte:**
- Produkte im Data Browser ansehen
- Erste Synchronisation starten
- Qualitätsprüfung der KI-Vorschläge
"""
        
        return content
    
    async def _generate_suggestions(self) -> List[Dict[str, Any]]:
        """Generate connector suggestions based on uploaded files"""
        suggestions = []
        
        has_etim = any(f.file_type.value == "etim_pricelist" for f in self.uploaded_files)
        has_images = any(f.file_type.value == "images_zip" for f in self.uploaded_files)
        has_products = any(f.record_count and f.record_count > 0 for f in self.uploaded_files)
        
        total_products = sum(f.record_count or 0 for f in self.uploaded_files)
        
        if has_products:
            suggestions.append({
                "id": "datanorm",
                "name": "DATANORM Export",
                "description": "B2B-Standard für den Elektrohandel",
                "ready": True,
                "setup_required": False,
                "estimated_setup": "Sofort",
                "products_supported": total_products,
            })
        
        if has_etim:
            suggestions.append({
                "id": "etim",
                "name": "ETIM Enrichment",
                "description": "Automatische Klassifikations-Updates",
                "ready": True,
                "setup_required": False,
                "estimated_setup": "Sofort",
            })
        
        if has_images:
            suggestions.append({
                "id": "amazon",
                "name": "Amazon SP-API",
                "description": "Verkaufen auf Amazon",
                "ready": False,
                "setup_required": True,
                "credentials_needed": ["seller_id", "client_id", "client_secret"],
                "estimated_setup": "10 Minuten",
            })
            
            suggestions.append({
                "id": "google_shopping",
                "name": "Google Shopping",
                "description": "Product Listings auf Google",
                "ready": False,
                "setup_required": True,
                "credentials_needed": ["merchant_id"],
                "estimated_setup": "5 Minuten",
            })
        
        suggestions.append({
            "id": "tender",
            "name": "TENDER",
            "description": "Öffentliche Ausschreibungen finden",
            "ready": True,
            "setup_required": False,
            "estimated_setup": "Sofort",
        })
        
        return suggestions
    
    async def _get_analysis_content(self) -> Dict[str, Any]:
        """Get analysis content for the analysis step"""
        total_products = sum(f.record_count or 0 for f in self.uploaded_files)
        avg_quality = sum(f.quality_score for f in self.uploaded_files) / len(self.uploaded_files) if self.uploaded_files else 0
        
        all_issues = []
        for f in self.uploaded_files:
            all_issues.extend(f.issues)
        
        return {
            "summary": {
                "total_files": len(self.uploaded_files),
                "total_products": total_products,
                "average_quality": avg_quality,
            },
            "files": [
                {
                    "filename": f.filename,
                    "type": f.file_type.value,
                    "records": f.record_count,
                    "quality": f.quality_score,
                    "issues": f.issues,
                }
                for f in self.uploaded_files
            ],
            "issues": all_issues,
            "recommendations": [
                "ETIM-Codes für nicht klassifizierte Produkte vorschlagen",
                "Fehlende Beschreibungen mit KI generieren",
                "Bilder aus PDF-Katalog extrahieren",
            ],
        }
    
    def _get_required_credentials(self) -> List[Dict[str, Any]]:
        """Get list of required credentials based on selected connectors"""
        credentials = []
        
        for suggestion in self.suggestions:
            if suggestion.get("setup_required") and suggestion.get("credentials_needed"):
                credentials.append({
                    "connector_id": suggestion["id"],
                    "connector_name": suggestion["name"],
                    "fields": suggestion["credentials_needed"],
                })
        
        return credentials
