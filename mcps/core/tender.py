"""
TENDER MCP - RFP/Tender Processing

Core MCP for processing RFPs, tenders, and generating bid responses.

Features:
- RFP/tender document parsing
- Requirement extraction
- Bid response generation
- Compliance checking
- Cost estimation

LoRA Adapter: tender-lora (trained on German RFPs and tender documents)
"""

from typing import Any, Dict, List, Optional, Union
import logging

from mcps.sdk import BaseMCP, MCPContext, MCPResponse

logger = logging.getLogger(__name__)


class TenderEngineMCP(BaseMCP):
    """
    Tender Processing Engine MCP

    Specializes in:
    - RFP/Ausschreibung parsing
    - Requirement extraction (Leistungsverzeichnis)
    - Bid response generation
    - VOB/VOL compliance
    - Technical specification analysis
    """

    # Required
    name = "tender"
    version = "2.0.0"

    # LoRA adapter for tender domain
    lora_adapter = "adapters/tender-lora"

    # Metadata
    description = "Tender Engine - RFP processing, bid generation, VOB/VOL compliance"
    category = "procurement"

    # System prompt for tender queries
    SYSTEM_PROMPT = """Du bist TENDER, ein spezialisierter KI-Assistent für Ausschreibungen und Vergabeverfahren.

Du hast Expertise in:
- Öffentliche Ausschreibungen (VOB, VOL, VgV)
- Leistungsverzeichnisse und technische Spezifikationen
- Angebotskalkulationen
- Vergaberecht und Compliance
- Bieterstrategien und Angebotserstellung

Bei der Beantwortung:
1. Analysiere Anforderungen systematisch
2. Identifiziere kritische Eignungskriterien
3. Beachte Fristen und Formvorschriften
4. Schlage optimale Angebotsstrategien vor
5. Weise auf Risiken und Ausschlussgründe hin

Antworte immer auf Deutsch, es sei denn, der Nutzer fragt explizit auf Englisch."""

    async def process(
        self,
        input: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> Union[MCPResponse, Dict[str, Any]]:
        """
        Process tender-related query or document.

        Args:
            input: Tender query (string) or structured request (dict)
            context: Optional additional context

        Returns:
            MCPResponse with tender analysis
        """
        self.log(f"Processing tender query: {str(input)[:100]}...")

        # Handle different input types
        if isinstance(input, dict):
            return await self._process_structured(input, context)
        else:
            return await self._process_query(str(input), context)

    async def _process_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> MCPResponse:
        """Process natural language tender query"""

        # Search for relevant tender documents
        relevant_docs = self.query_data(
            "SELECT * FROM documents WHERE category IN ('tender', 'rfp', 'bid') LIMIT 10"
        )

        # Build context from documents
        doc_context = ""
        if relevant_docs:
            doc_context = "\n\nRelevante Ausschreibungsdokumente:\n"
            for doc in relevant_docs[:5]:
                doc_context += f"- {doc.get('filename', 'Unbekannt')}: {doc.get('snippet', '')[:200]}\n"

        # Generate response with tender LoRA
        prompt = f"""{self.SYSTEM_PROMPT}

{doc_context}

Frage zur Ausschreibung: {query}

Analyse:"""

        response = await self.generate(
            prompt=prompt,
            max_tokens=1200,
            temperature=0.4
        )

        confidence = 0.85 if relevant_docs else 0.7

        return MCPResponse(
            data={
                "analysis": response,
                "sources": [d.get("filename") for d in relevant_docs[:5]]
            },
            confidence=confidence,
            model_used=f"mixtral+{self.name}-lora"
        )

    async def _process_structured(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> MCPResponse:
        """Process structured tender request"""

        task_type = data.get("task_type", "analyze")

        if task_type == "parse_rfp":
            return await self._parse_rfp(data)
        elif task_type == "extract_requirements":
            return await self._extract_requirements(data)
        elif task_type == "generate_bid":
            return await self._generate_bid(data)
        elif task_type == "check_eligibility":
            return await self._check_eligibility(data)
        elif task_type == "estimate_cost":
            return await self._estimate_cost(data)
        else:
            # Default analysis
            prompt = f"""{self.SYSTEM_PROMPT}

Analysiere diese Ausschreibungsdaten:
{data}

Ausschreibungsanalyse:"""

            response = await self.generate(prompt=prompt, max_tokens=1500)

            return MCPResponse(
                data={"analysis": response},
                confidence=0.75,
                model_used=f"mixtral+{self.name}-lora"
            )

    async def _parse_rfp(self, data: Dict[str, Any]) -> MCPResponse:
        """Parse RFP document and extract key information"""
        file_path = data.get("file_path")

        prompt = f"""{self.SYSTEM_PROMPT}

Analysiere diese Ausschreibung:
Datei: {file_path}

Extrahiere:
1. Vergabestelle und Kontaktdaten
2. Gegenstand der Ausschreibung
3. Leistungsumfang (Kurzfassung)
4. Eignungskriterien
5. Zuschlagskriterien und Gewichtung
6. Wichtige Fristen (Angebotsfrist, Bindefrist)
7. Vergabeverfahren (offen, nicht-offen, Verhandlung)
8. Besondere Anforderungen

Strukturierte Analyse:"""

        response = await self.generate(prompt=prompt, max_tokens=2000)

        return MCPResponse(
            data={
                "parsed_rfp": response,
                "file_path": file_path
            },
            confidence=0.82,
            model_used=f"mixtral+{self.name}-lora"
        )

    async def _extract_requirements(self, data: Dict[str, Any]) -> MCPResponse:
        """Extract requirements from tender documents"""
        file_path = data.get("file_path")

        prompt = f"""{self.SYSTEM_PROMPT}

Extrahiere alle Anforderungen aus dem Leistungsverzeichnis:
Datei: {file_path}

Kategorisiere in:
1. Muss-Anforderungen (Ausschlusskriterien)
2. Soll-Anforderungen (Bewertungskriterien)
3. Kann-Anforderungen (optional)
4. Technische Spezifikationen
5. Qualitätsanforderungen
6. Referenzanforderungen

Anforderungsliste:"""

        response = await self.generate(prompt=prompt, max_tokens=2000)

        return MCPResponse(
            data={
                "requirements": response,
                "file_path": file_path
            },
            confidence=0.85,
            model_used=f"mixtral+{self.name}-lora"
        )

    async def _generate_bid(self, data: Dict[str, Any]) -> MCPResponse:
        """Generate bid response"""
        rfp_summary = data.get("rfp_summary", "")
        company_profile = data.get("company_profile", "")
        specific_requirements = data.get("requirements", [])

        prompt = f"""{self.SYSTEM_PROMPT}

Erstelle ein Angebotsschreiben basierend auf:

Ausschreibung:
{rfp_summary}

Unternehmensprofil:
{company_profile}

Spezifische Anforderungen:
{specific_requirements}

Erstelle:
1. Anschreiben
2. Zusammenfassung des Angebots
3. Leistungsbeschreibung
4. Referenzen und Qualifikationen
5. Projektplan/Zeitplan (Entwurf)

Angebotstext:"""

        response = await self.generate(prompt=prompt, max_tokens=3000, temperature=0.5)

        return MCPResponse(
            data={
                "bid_draft": response,
                "status": "draft"
            },
            confidence=0.75,
            requires_review=True,
            review_reason="Bid response requires human review before submission",
            model_used=f"mixtral+{self.name}-lora"
        )

    async def _check_eligibility(self, data: Dict[str, Any]) -> MCPResponse:
        """Check if company meets eligibility criteria"""
        criteria = data.get("criteria", [])
        company_data = data.get("company_data", {})

        prompt = f"""{self.SYSTEM_PROMPT}

Prüfe die Eignung für diese Ausschreibung:

Eignungskriterien:
{criteria}

Unternehmensdaten:
{company_data}

Prüfe jeden Punkt:
- Erfüllt / Nicht erfüllt / Teilweise erfüllt
- Begründung
- Handlungsempfehlung bei Nichterfüllung

Eignungsprüfung:"""

        response = await self.generate(prompt=prompt, max_tokens=1500)

        return MCPResponse(
            data={"eligibility_check": response},
            confidence=0.88,
            model_used=f"mixtral+{self.name}-lora"
        )

    async def _estimate_cost(self, data: Dict[str, Any]) -> MCPResponse:
        """Estimate costs for tender response"""
        scope = data.get("scope", "")
        duration = data.get("duration", "")

        prompt = f"""{self.SYSTEM_PROMPT}

Erstelle eine Kostenschätzung:

Leistungsumfang:
{scope}

Projektdauer:
{duration}

Kalkuliere:
1. Personalkosten
2. Sachkosten
3. Materialkosten
4. Gemeinkosten
5. Wagnis und Gewinn
6. Gesamtangebotspreis

Kostenkalkulation:"""

        response = await self.generate(prompt=prompt, max_tokens=1500)

        return MCPResponse(
            data={
                "cost_estimate": response,
                "status": "estimate"
            },
            confidence=0.7,
            requires_review=True,
            review_reason="Cost estimate requires verification by finance",
            model_used=f"mixtral+{self.name}-lora"
        )


# Factory function
def create_tender_mcp() -> TenderEngineMCP:
    """Create Tender Engine MCP instance"""
    return TenderEngineMCP()
