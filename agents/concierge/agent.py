"""
Concierge Agent - The Onboarding Wizard

Responsibilities:
1. Guide customer through data upload
2. Analyze uploaded files and explain what they contain
3. Suggest which connectors/MCPs make sense
4. Collect and securely store credentials
5. Create a "Context Brief" for the Import Agent
6. Monitor import progress and explain results to customer

The Concierge is the friendly face - speaks business language, not tech.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import httpx

logger = logging.getLogger(__name__)


class OnboardingStage(str, Enum):
    """Stages of the onboarding wizard"""
    WELCOME = "welcome"
    COMPANY_PROFILE = "company_profile"
    DATA_UPLOAD = "data_upload"
    DATA_ANALYSIS = "data_analysis"
    CONNECTOR_SUGGESTIONS = "connector_suggestions"
    CREDENTIALS = "credentials"
    IMPORT_HANDOFF = "import_handoff"
    MONITORING = "monitoring"
    COMPLETE = "complete"


class FileType(str, Enum):
    """Recognized file types"""
    BMECAT_XML = "bmecat_xml"
    ETIM_PRICELIST = "etim_pricelist"
    DATANORM = "datanorm"
    CSV_PRODUCTS = "csv_products"
    EXCEL_PRODUCTS = "excel_products"
    PDF_CATALOG = "pdf_catalog"
    IMAGES_ZIP = "images_zip"
    UNKNOWN = "unknown"


class BusinessType(str, Enum):
    """Business model types"""
    B2B_DISTRIBUTOR = "b2b_distributor"  # Sells products from multiple manufacturers
    B2B_MANUFACTURER = "b2b_manufacturer"  # Produces own products
    B2C_RETAILER = "b2c_retailer"  # Sells to consumers
    HYBRID = "hybrid"


@dataclass
class UploadedFile:
    """Represents an uploaded file with analysis"""
    filename: str
    file_type: FileType
    size_bytes: int
    detected_format: Optional[str] = None
    record_count: Optional[int] = None
    sample_fields: List[str] = field(default_factory=list)
    quality_score: float = 0.0
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class ContextBrief:
    """
    The handoff document from Concierge to Import Agent
    
    Contains everything the Import Agent needs to know about:
    - Who this customer is
    - What files they uploaded
    - What the data looks like
    - What they want to achieve
    - Any special considerations
    """
    brief_id: UUID
    customer_id: UUID
    created_at: datetime
    
    # Customer context
    company_name: str
    business_type: BusinessType
    industry: str
    product_count_estimate: int
    
    # Data context
    files: List[UploadedFile]
    primary_language: str = "de"
    has_etim_codes: bool = False
    has_eclass_codes: bool = False
    has_gtin: bool = False
    has_images: bool = False
    
    # Detected schemas
    detected_category_system: Optional[str] = None  # ETIM, ECLASS, custom
    field_mapping_hints: Dict[str, str] = field(default_factory=dict)
    
    # Business goals
    target_channels: List[str] = field(default_factory=list)  # marketplace, datanorm, etc.
    priority_connectors: List[str] = field(default_factory=list)
    
    # Special instructions (from Concierge to Import Agent)
    notes: str = ""
    
    def to_prompt(self) -> str:
        """Generate a prompt for the Import Agent"""
        return f"""
## Customer Context Brief

**Company:** {self.company_name}
**Business Type:** {self.business_type.value}
**Industry:** {self.industry}
**Estimated Products:** {self.product_count_estimate:,}

### Uploaded Files
{self._format_files()}

### Data Quality Assessment
- ETIM Codes: {"✅ Present" if self.has_etim_codes else "❌ Missing - needs classification"}
- ECLASS Codes: {"✅ Present" if self.has_eclass_codes else "❌ Missing"}
- GTIN/EAN: {"✅ Present" if self.has_gtin else "⚠️ Partially missing"}
- Product Images: {"✅ Present" if self.has_images else "❌ Missing"}

### Detected Schema
Category System: {self.detected_category_system or "Custom/Unknown"}

### Field Mapping Hints
{json.dumps(self.field_mapping_hints, indent=2, ensure_ascii=False)}

### Target Channels
{', '.join(self.target_channels)}

### Priority Connectors
{', '.join(self.priority_connectors)}

### Special Notes from Concierge
{self.notes}

---
**INSTRUCTION:** Map all products to the 0711 unified category schema.
Preserve original codes (ETIM, ECLASS) as metadata.
Flag any products that cannot be confidently categorized.
"""

    def _format_files(self) -> str:
        lines = []
        for f in self.files:
            lines.append(f"- **{f.filename}** ({f.file_type.value})")
            if f.record_count:
                lines.append(f"  - Records: {f.record_count:,}")
            if f.issues:
                lines.append(f"  - Issues: {', '.join(f.issues)}")
        return "\n".join(lines)


class ConciergeAgent:
    """
    The Onboarding Concierge Agent
    
    Guides customers through the onboarding process with a friendly,
    wizard-like interface. Collects information, analyzes uploads,
    and creates a Context Brief for the Import Agent.
    """
    
    def __init__(
        self,
        customer_id: UUID,
        llm_client: Optional[httpx.AsyncClient] = None,
        minio_client: Optional[Any] = None,
    ):
        self.customer_id = customer_id
        self.llm_client = llm_client
        self.minio_client = minio_client
        
        self.stage = OnboardingStage.WELCOME
        self.uploaded_files: List[UploadedFile] = []
        self.company_profile: Dict[str, Any] = {}
        self.credentials: Dict[str, Dict[str, str]] = {}  # connector -> creds
        self.conversation_history: List[Dict[str, str]] = []
        
    async def process_message(self, message: str) -> str:
        """
        Process a message from the customer and return a response
        
        This is the main entry point for the wizard conversation.
        """
        self.conversation_history.append({"role": "user", "content": message})
        
        # Route based on current stage
        if self.stage == OnboardingStage.WELCOME:
            response = await self._handle_welcome(message)
        elif self.stage == OnboardingStage.COMPANY_PROFILE:
            response = await self._handle_company_profile(message)
        elif self.stage == OnboardingStage.DATA_UPLOAD:
            response = await self._handle_data_upload(message)
        elif self.stage == OnboardingStage.DATA_ANALYSIS:
            response = await self._handle_data_analysis(message)
        elif self.stage == OnboardingStage.CONNECTOR_SUGGESTIONS:
            response = await self._handle_connector_suggestions(message)
        elif self.stage == OnboardingStage.CREDENTIALS:
            response = await self._handle_credentials(message)
        elif self.stage == OnboardingStage.IMPORT_HANDOFF:
            response = await self._handle_import_handoff(message)
        elif self.stage == OnboardingStage.MONITORING:
            response = await self._handle_monitoring(message)
        else:
            response = "Onboarding ist abgeschlossen! Wie kann ich Ihnen weiter helfen?"
        
        self.conversation_history.append({"role": "assistant", "content": response})
        return response
    
    async def _handle_welcome(self, message: str) -> str:
        """Welcome stage - introduce the wizard"""
        self.stage = OnboardingStage.COMPANY_PROFILE
        return """
👋 **Willkommen bei 0711 Intelligence!**

Ich bin Ihr persönlicher Onboarding-Assistent und begleite Sie durch die Einrichtung.

In den nächsten Minuten werden wir:
1. 📊 Ihre Produktdaten hochladen
2. 🔍 Die Daten analysieren und optimieren
3. 🔗 Die richtigen Kanäle für Sie einrichten

**Erzählen Sie mir kurz von Ihrem Unternehmen:**
- Was für Produkte vertreiben Sie?
- Sind Sie Hersteller oder Distributor?
- Welche Branchen bedienen Sie? (Elektro, Automotive, Industrie...)
"""
    
    async def _handle_company_profile(self, message: str) -> str:
        """Collect company profile information"""
        # Use LLM to extract company info from free text
        profile = await self._extract_company_profile(message)
        self.company_profile.update(profile)
        
        self.stage = OnboardingStage.DATA_UPLOAD
        
        business_type = profile.get("business_type", "distributor")
        industry = profile.get("industry", "Elektro")
        
        return f"""
Verstanden! Sie sind also ein **{business_type}** im Bereich **{industry}**.

Jetzt zu Ihren Produktdaten. Laden Sie Ihre Dateien hoch - ich erkenne automatisch:

📄 **Unterstützte Formate:**
- BMECat XML (alle Versionen)
- ETIM Preislisten
- DATANORM (4.0, 5.0)
- CSV / Excel mit Produktdaten
- PDF-Kataloge (werden OCR-verarbeitet)
- Produktbilder (ZIP)

💡 **Tipp:** Je vollständiger Ihre Daten, desto mehr können wir automatisch für Sie tun!

**Ziehen Sie Ihre Dateien hierher oder klicken Sie zum Hochladen.**
"""
    
    async def _handle_data_upload(self, message: str) -> str:
        """Handle file uploads and initial analysis"""
        # This would be triggered by actual file uploads
        # For now, we'll simulate the analysis
        
        if "hochgeladen" in message.lower() or "upload" in message.lower():
            self.stage = OnboardingStage.DATA_ANALYSIS
            return await self._analyze_uploads()
        
        return """
Ich warte auf Ihre Dateien. Sie können mehrere Dateien gleichzeitig hochladen.

Wenn Sie fertig sind, sagen Sie mir Bescheid!
"""
    
    async def _analyze_uploads(self) -> str:
        """Analyze uploaded files and provide feedback"""
        # This would actually analyze files in MinIO
        # For now, return a template response
        
        self.stage = OnboardingStage.CONNECTOR_SUGGESTIONS
        
        return """
🔍 **Analyse abgeschlossen!**

Ich habe Ihre Daten analysiert:

| Datei | Format | Produkte | Qualität |
|-------|--------|----------|----------|
| catalog.xml | BMECat 2005 | 12.450 | ⭐⭐⭐⭐ |
| prices.xlsx | ETIM Preisliste | 12.450 | ⭐⭐⭐⭐⭐ |
| images.zip | Produktbilder | 8.320 | ⭐⭐⭐ |

**Was mir aufgefallen ist:**

✅ **Gut:**
- ETIM 9.0 Klassifikation vorhanden
- Alle Pflichtfelder gefüllt
- Preise in EUR, netto

⚠️ **Verbesserungspotential:**
- 4.130 Produkte ohne Bilder
- 2.100 Produkte ohne GTIN
- Beschreibungen teilweise zu kurz (<50 Zeichen)

**Soll ich diese Lücken automatisch mit KI füllen?**
- Fehlende Beschreibungen generieren
- ETIM-Codes für nicht klassifizierte Produkte vorschlagen
- Bilder aus PDF-Katalog extrahieren
"""
    
    async def _handle_data_analysis(self, message: str) -> str:
        """Discuss analysis results"""
        self.stage = OnboardingStage.CONNECTOR_SUGGESTIONS
        return await self._suggest_connectors()
    
    async def _suggest_connectors(self) -> str:
        """Suggest relevant connectors based on data and business type"""
        self.stage = OnboardingStage.CREDENTIALS
        
        return """
🔗 **Empfohlene Kanäle für Sie:**

Basierend auf Ihren Daten und Ihrer Branche empfehle ich:

### Sofort einsatzbereit:
1. **📤 DATANORM Export** - Ihre Daten sind DATANORM-ready!
   - Ihre B2B-Kunden können direkt bestellen
   
2. **🏷️ ETIM Enrichment** - Sie haben bereits ETIM 9.0
   - Automatische Updates auf neue ETIM-Versionen

### Mit minimaler Einrichtung:
3. **🛒 Amazon SP-API** - 8.320 Produkte mit Bildern
   - Benötigt: Amazon Seller Account Credentials
   
4. **📊 Google Shopping** - Sofort exportierbar
   - Benötigt: Google Merchant Center ID

### Für später:
5. **📝 TENDER** - Ausschreibungen finden
   - Spart Zeit bei öffentlichen Aufträgen
   
6. **🔍 WETTBEWERB** - Konkurrenzpreise monitoren
   - Benötigt: Liste der Wettbewerber

**Welche Kanäle möchten Sie einrichten?**
"""
    
    async def _handle_connector_suggestions(self, message: str) -> str:
        """Handle connector selection"""
        self.stage = OnboardingStage.CREDENTIALS
        return """
Gute Wahl! Für **Amazon** und **Google Shopping** brauche ich noch Ihre Zugangsdaten.

🔒 **Ihre Credentials sind sicher:**
- Verschlüsselt gespeichert
- Nur für die gewählten Kanäle
- Jederzeit widerrufbar

**Amazon SP-API:**
- Seller ID: _________________
- Client ID: _________________
- Client Secret: _________________

Oder verbinden Sie sich direkt über OAuth →
"""
    
    async def _handle_credentials(self, message: str) -> str:
        """Collect and store credentials"""
        self.stage = OnboardingStage.IMPORT_HANDOFF
        
        return """
✅ **Credentials gespeichert!**

Jetzt starte ich den Import Ihrer Daten. Das übernimmt unser spezialisierter Import-Agent.

**Was jetzt passiert:**
1. Ihre Produkte werden in unser einheitliches Schema überführt
2. Fehlende ETIM-Codes werden KI-gestützt ergänzt
3. Beschreibungen werden optimiert
4. Bilder werden zugeordnet

⏱️ **Geschätzte Dauer:** 15-20 Minuten für 12.450 Produkte

Ich halte Sie auf dem Laufenden!
"""
    
    async def _handle_import_handoff(self, message: str) -> str:
        """Hand off to Import Agent"""
        # Create the Context Brief
        brief = self._create_context_brief()
        
        # Send to Import Agent (would be async message queue)
        await self._dispatch_to_import_agent(brief)
        
        self.stage = OnboardingStage.MONITORING
        
        return """
🚀 **Import gestartet!**

Ich habe dem Import-Agent folgende Informationen übergeben:
- Ihr Unternehmensprofil
- Die analysierten Dateien
- Die Zielkanäle
- Besondere Hinweise zu Ihren Daten

**Live-Status:**
```
[████████░░░░░░░░░░░░] 40%
Verarbeite: catalog.xml
Produkte: 4.980 / 12.450
```

Sie können dieses Fenster schließen - ich informiere Sie per E-Mail, wenn alles fertig ist.
"""
    
    async def _handle_monitoring(self, message: str) -> str:
        """Monitor import progress"""
        return """
**Import läuft noch...**

```
[████████████████░░░░] 80%
Verarbeite: Bilderzuordnung
Produkte: 9.960 / 12.450
```

Bisherige Ergebnisse:
- ✅ 9.800 Produkte erfolgreich importiert
- ⚠️ 160 Produkte zur manuellen Prüfung
- ❌ 0 Fehler

Noch ca. 5 Minuten...
"""
    
    def _create_context_brief(self) -> ContextBrief:
        """Create the handoff document for Import Agent"""
        return ContextBrief(
            brief_id=uuid4(),
            customer_id=self.customer_id,
            created_at=datetime.utcnow(),
            company_name=self.company_profile.get("company_name", "Unknown"),
            business_type=BusinessType(self.company_profile.get("business_type", "b2b_distributor")),
            industry=self.company_profile.get("industry", "Elektro"),
            product_count_estimate=self.company_profile.get("product_count", 0),
            files=self.uploaded_files,
            has_etim_codes=True,  # From analysis
            has_gtin=False,  # From analysis
            target_channels=["datanorm", "amazon", "google_shopping"],
            priority_connectors=["DATANORM", "ETIM", "AMAZON"],
            notes="Customer hat bereits ETIM 9.0, möchte auf Marktplätze expandieren. "
                  "4.130 Produkte ohne Bilder - aus PDF extrahieren wenn möglich."
        )
    
    async def _dispatch_to_import_agent(self, brief: ContextBrief) -> None:
        """Send Context Brief to Import Agent"""
        # Would use message queue (Redis, RabbitMQ, etc.)
        logger.info(f"Dispatching Context Brief {brief.brief_id} to Import Agent")
        logger.info(f"Brief prompt:\n{brief.to_prompt()}")
        
        # In production: publish to queue
        # await self.queue.publish("import_agent", brief.to_dict())
    
    async def _extract_company_profile(self, text: str) -> Dict[str, Any]:
        """Use LLM to extract company profile from free text"""
        # Would call LLM API
        # For now, return mock data
        return {
            "company_name": "Example GmbH",
            "business_type": "b2b_distributor",
            "industry": "Elektro",
            "product_count": 12450,
        }
    
    async def analyze_file(self, filename: str, content: bytes) -> UploadedFile:
        """Analyze an uploaded file"""
        file_type = self._detect_file_type(filename, content)
        
        analysis = UploadedFile(
            filename=filename,
            file_type=file_type,
            size_bytes=len(content),
        )
        
        if file_type == FileType.BMECAT_XML:
            analysis = await self._analyze_bmecat(analysis, content)
        elif file_type == FileType.CSV_PRODUCTS:
            analysis = await self._analyze_csv(analysis, content)
        elif file_type == FileType.EXCEL_PRODUCTS:
            analysis = await self._analyze_excel(analysis, content)
        
        self.uploaded_files.append(analysis)
        return analysis
    
    def _detect_file_type(self, filename: str, content: bytes) -> FileType:
        """Detect the type of uploaded file"""
        filename_lower = filename.lower()
        
        if filename_lower.endswith(".xml"):
            # Check for BMECat
            if b"BMECAT" in content[:1000] or b"bmecat" in content[:1000]:
                return FileType.BMECAT_XML
            return FileType.UNKNOWN
        elif filename_lower.endswith(".csv"):
            return FileType.CSV_PRODUCTS
        elif filename_lower.endswith((".xlsx", ".xls")):
            return FileType.EXCEL_PRODUCTS
        elif filename_lower.endswith(".pdf"):
            return FileType.PDF_CATALOG
        elif filename_lower.endswith(".zip"):
            return FileType.IMAGES_ZIP
        
        return FileType.UNKNOWN
    
    async def _analyze_bmecat(self, analysis: UploadedFile, content: bytes) -> UploadedFile:
        """Analyze BMECat XML file"""
        # Would parse XML and extract info
        analysis.detected_format = "BMECat 2005"
        analysis.record_count = 12450
        analysis.sample_fields = ["SUPPLIER_AID", "DESCRIPTION_SHORT", "PRICE_AMOUNT", "MIME_INFO"]
        analysis.quality_score = 0.85
        return analysis
    
    async def _analyze_csv(self, analysis: UploadedFile, content: bytes) -> UploadedFile:
        """Analyze CSV file"""
        # Would parse CSV and extract info
        import csv
        import io
        
        try:
            text = content.decode("utf-8")
            reader = csv.reader(io.StringIO(text))
            headers = next(reader)
            row_count = sum(1 for _ in reader)
            
            analysis.sample_fields = headers[:10]
            analysis.record_count = row_count
            analysis.quality_score = 0.7
        except Exception as e:
            analysis.issues.append(f"CSV parse error: {e}")
        
        return analysis
    
    async def _analyze_excel(self, analysis: UploadedFile, content: bytes) -> UploadedFile:
        """Analyze Excel file"""
        # Would use openpyxl or pandas
        analysis.detected_format = "Excel (xlsx)"
        analysis.quality_score = 0.75
        return analysis
