"""
CTAX MCP - German Tax Processing

Core MCP for German tax calculations, VAT processing, and compliance.

Features:
- VAT calculation and validation
- ELSTER filing preparation
- Tax document analysis
- Compliance checking

LoRA Adapter: ctax-lora (trained on German tax law and regulations)
"""

from typing import Any, Dict, Optional, Union
from pathlib import Path
import logging

from mcps.sdk import BaseMCP, MCPContext, MCPResponse

logger = logging.getLogger(__name__)


class CTAXMCP(BaseMCP):
    """
    German Tax Engine MCP

    Specializes in:
    - German corporate tax (Körperschaftsteuer)
    - VAT/Umsatzsteuer calculations
    - Trade tax (Gewerbesteuer)
    - ELSTER filing
    - Tax document analysis
    """

    # Required
    name = "ctax"
    version = "2.0.0"

    # LoRA adapter for tax domain
    lora_adapter = "adapters/ctax-lora"

    # Metadata
    description = "German Tax Engine - VAT, corporate tax, ELSTER, compliance"
    category = "finance"

    # System prompt for tax queries
    SYSTEM_PROMPT = """Du bist CTAX, ein spezialisierter KI-Assistent für deutsches Steuerrecht.

Du hast Expertise in:
- Umsatzsteuer (UStG) und Vorsteuerabzug
- Körperschaftsteuer (KStG)
- Gewerbesteuer (GewStG)
- Einkommensteuer (EStG)
- ELSTER-Anmeldungen
- Steuerliche Compliance

Bei der Beantwortung:
1. Zitiere relevante Paragraphen (z.B. § 15 UStG)
2. Sei präzise bei Berechnungen
3. Weise auf Fristen und Compliance-Anforderungen hin
4. Nutze korrekte steuerrechtliche Terminologie

Antworte immer auf Deutsch, es sei denn, der Nutzer fragt explizit auf Englisch."""

    async def process(
        self,
        input: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> Union[MCPResponse, Dict[str, Any]]:
        """
        Process tax-related query.

        Args:
            input: Tax query (string) or structured tax data (dict)
            context: Optional additional context

        Returns:
            MCPResponse with tax analysis/calculation
        """
        self.log(f"Processing tax query: {str(input)[:100]}...")

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
        """Process natural language tax query"""

        # Search for relevant tax documents in lakehouse
        relevant_docs = self.query_data(
            f"SELECT * FROM documents WHERE category = 'tax' LIMIT 10"
        )

        # Build context from documents
        doc_context = ""
        if relevant_docs:
            doc_context = "\n\nRelevante Dokumente:\n"
            for doc in relevant_docs[:5]:
                doc_context += f"- {doc.get('filename', 'Unbekannt')}: {doc.get('snippet', '')[:200]}\n"

        # Generate response with markdown formatting
        prompt = f"""{self.SYSTEM_PROMPT}

{doc_context}

Frage: {query}

**AUSGABE IN MARKDOWN-FORMAT**:

## 📊 Zusammenfassung
[2-3 Sätze Kurzantwort]

## 🔍 Detaillierte Analyse
[Ausführliche steuerrechtliche Erläuterung]

## 💰 Berechnungen (falls relevant)
| Position | Betrag | Steuersatz | USt |
|----------|--------|------------|-----|
| [Pos] | €XXX | 19% | €XX |

## 📋 Rechtsgrundlagen
- **§ [XX] [Gesetz]**: [Relevanz für diesen Fall]

## ✅ Handlungsempfehlungen
1. [Konkrete Maßnahme]
2. [Weiterer Schritt]

---
*⚠️ Steuerrechtliche Hinweise ohne Gewähr*

Antwort:"""

        response = await self.generate(
            prompt=prompt,
            max_tokens=2000,  # Increased for formatted output
            temperature=0.3
        )

        # Determine confidence based on document matches
        confidence = 0.85 if relevant_docs else 0.7

        return MCPResponse(
            data={
                "answer": response,
                "sources": [d.get("filename") for d in relevant_docs[:5]],
                "format": "markdown"
            },
            confidence=confidence,
            model_used=f"mixtral+{self.name}-lora"
        )

    async def _process_structured(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> MCPResponse:
        """Process structured tax data (invoices, calculations, etc.)"""

        task_type = data.get("task_type", "analyze")

        if task_type == "calculate_vat":
            return await self._calculate_vat(data)
        elif task_type == "analyze_invoice":
            return await self._analyze_invoice(data)
        elif task_type == "check_compliance":
            return await self._check_compliance(data)
        else:
            # Default to general analysis
            prompt = f"""{self.SYSTEM_PROMPT}

Analysiere die folgenden Steuerdaten:
{data}

Analyse:"""

            response = await self.generate(prompt=prompt, max_tokens=1500)

            return MCPResponse(
                data={"analysis": response},
                confidence=0.8,
                model_used=f"mixtral+{self.name}-lora"
            )

    async def _calculate_vat(self, data: Dict[str, Any]) -> MCPResponse:
        """Calculate VAT/Umsatzsteuer"""
        net_amount = data.get("net_amount", 0)
        vat_rate = data.get("vat_rate", 0.19)  # Default 19%

        vat_amount = net_amount * vat_rate
        gross_amount = net_amount + vat_amount

        return MCPResponse(
            data={
                "net_amount": round(net_amount, 2),
                "vat_rate": vat_rate,
                "vat_amount": round(vat_amount, 2),
                "gross_amount": round(gross_amount, 2),
                "vat_rate_percent": f"{vat_rate * 100}%"
            },
            confidence=0.99,
            model_used="calculation"
        )

    async def _analyze_invoice(self, data: Dict[str, Any]) -> MCPResponse:
        """Analyze invoice for tax compliance"""
        file_path = data.get("file_path")

        if not file_path:
            return MCPResponse(
                data={"error": "file_path required"},
                confidence=0,
                requires_review=True
            )

        # Query invoice data from lakehouse
        invoices = self.query_data(
            f"SELECT * FROM invoices WHERE file_path = '{file_path}' LIMIT 1"
        )

        if not invoices:
            prompt = f"""{self.SYSTEM_PROMPT}

Analysiere diese Rechnung auf steuerliche Korrektheit:
Dateipfad: {file_path}

Prüfe:
1. Pflichtangaben gemäß § 14 UStG
2. Korrekte USt-Berechnung
3. USt-IdNr. Format
4. Vorsteuerabzugsberechtigung

Analyse:"""

            response = await self.generate(prompt=prompt, max_tokens=1000)

            return MCPResponse(
                data={"analysis": response},
                confidence=0.75,
                requires_review=True,
                review_reason="Invoice not found in lakehouse, analysis based on file path only"
            )

        invoice = invoices[0]
        return MCPResponse(
            data={
                "invoice": invoice,
                "analysis": "Invoice found and processed"
            },
            confidence=0.9
        )

    async def _check_compliance(self, data: Dict[str, Any]) -> MCPResponse:
        """Check tax compliance status"""
        period = data.get("period", "current")

        prompt = f"""{self.SYSTEM_PROMPT}

Prüfe die steuerliche Compliance für den Zeitraum: {period}

Zu prüfen:
1. USt-Voranmeldung fristgerecht?
2. Zusammenfassende Meldung?
3. Intrastat-Meldung?
4. Dokumentationspflichten erfüllt?

Compliance-Bericht:"""

        response = await self.generate(prompt=prompt, max_tokens=1000)

        return MCPResponse(
            data={"compliance_report": response},
            confidence=0.8,
            model_used=f"mixtral+{self.name}-lora"
        )


# Factory function for backwards compatibility
def create_ctax_mcp() -> CTAXMCP:
    """Create CTAX MCP instance"""
    return CTAXMCP()
