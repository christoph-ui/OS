"""
LAW MCP - Legal & Contract Analysis

Core MCP for legal document analysis, contract review, and compliance.

Features:
- Contract analysis and interpretation
- Legal document search
- Compliance checking (GDPR, etc.)
- Terms & conditions review

LoRA Adapter: law-lora (trained on German law and contracts)
"""

from typing import Any, Dict, List, Optional, Union
import logging

from mcps.sdk import BaseMCP, MCPContext, MCPResponse

logger = logging.getLogger(__name__)


class LAWMCP(BaseMCP):
    """
    Legal Analysis MCP

    Specializes in:
    - German contract law (BGB, HGB)
    - GDPR/DSGVO compliance
    - Contract analysis and interpretation
    - Legal document review
    - Commercial agreements
    """

    # Required
    name = "law"
    version = "2.0.0"

    # LoRA adapter for legal domain
    lora_adapter = "adapters/law-lora"

    # Metadata
    description = "Legal & Contract Analysis - German law, GDPR, contracts"
    category = "legal"

    # System prompt for legal queries
    SYSTEM_PROMPT = """Du bist LAW, ein spezialisierter KI-Assistent für deutsches Recht und Vertragsanalyse.

Du hast Expertise in:
- Deutsches Vertragsrecht (BGB, HGB)
- Handelsrecht und AGB-Recht
- Datenschutz (DSGVO/GDPR)
- Arbeitsrecht
- Compliance und Regulierung

Bei der Beantwortung:
1. Zitiere relevante Paragraphen (z.B. § 433 BGB)
2. Sei präzise bei rechtlichen Interpretationen
3. Gib die Quellen deiner Aussagen an
4. Weise darauf hin, wenn anwaltliche Beratung empfohlen wird
5. Nutze korrekte juristische Terminologie

Hinweis: Du bist ein KI-Assistent und ersetzt keine Rechtsberatung.

Antworte immer auf Deutsch, es sei denn, der Nutzer fragt explizit auf Englisch."""

    LEGAL_DISCLAIMER = "\n\n**Hinweis:** Dies ist eine KI-gestützte Analyse und stellt keine Rechtsberatung dar. Für verbindliche Auskünfte konsultieren Sie bitte einen Rechtsanwalt."

    async def process(
        self,
        input: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> Union[MCPResponse, Dict[str, Any]]:
        """
        Process legal query or document.

        Args:
            input: Legal query (string) or structured request (dict)
            context: Optional additional context

        Returns:
            MCPResponse with legal analysis
        """
        self.log(f"Processing legal query: {str(input)[:100]}...")

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
        """Process natural language legal query"""

        # Search for relevant legal documents
        relevant_docs = self.query_data(
            "SELECT * FROM documents WHERE category IN ('legal', 'contract') LIMIT 10"
        )

        # Build context from documents
        doc_context = ""
        if relevant_docs:
            doc_context = "\n\nRelevante Rechtsdokumente:\n"
            for doc in relevant_docs[:5]:
                doc_context += f"- {doc.get('filename', 'Unbekannt')}: {doc.get('snippet', '')[:200]}\n"

        # Generate response with law LoRA
        prompt = f"""{self.SYSTEM_PROMPT}

{doc_context}

Rechtliche Frage: {query}

Rechtliche Analyse:"""

        response = await self.generate(
            prompt=prompt,
            max_tokens=1200,
            temperature=0.2  # Very low temperature for legal accuracy
        )

        # Add disclaimer if needed
        if self._needs_disclaimer(query):
            response += self.LEGAL_DISCLAIMER

        # Determine confidence
        confidence = 0.82 if relevant_docs else 0.65

        return MCPResponse(
            data={
                "analysis": response,
                "sources": [d.get("filename") for d in relevant_docs[:5]]
            },
            confidence=confidence,
            requires_review=self._needs_review(query),
            review_reason="Legal analysis may require expert verification" if self._needs_review(query) else None,
            model_used=f"mixtral+{self.name}-lora"
        )

    async def _process_structured(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> MCPResponse:
        """Process structured legal request"""

        task_type = data.get("task_type", "analyze")

        if task_type == "analyze_contract":
            return await self._analyze_contract(data)
        elif task_type == "check_gdpr":
            return await self._check_gdpr_compliance(data)
        elif task_type == "find_contracts":
            return await self._find_contracts(data)
        else:
            # Default analysis
            prompt = f"""{self.SYSTEM_PROMPT}

Analysiere die folgenden rechtlichen Daten:
{data}

Rechtliche Analyse:"""

            response = await self.generate(prompt=prompt, max_tokens=1500)

            return MCPResponse(
                data={"analysis": response + self.LEGAL_DISCLAIMER},
                confidence=0.75,
                requires_review=True,
                model_used=f"mixtral+{self.name}-lora"
            )

    async def _analyze_contract(self, data: Dict[str, Any]) -> MCPResponse:
        """Analyze a contract document"""
        file_path = data.get("file_path")
        contract_type = data.get("contract_type", "general")

        prompt = f"""{self.SYSTEM_PROMPT}

Analysiere diesen Vertrag:
Typ: {contract_type}
Datei: {file_path}

Prüfe:
1. Wesentliche Vertragsbestandteile
2. Rechte und Pflichten der Parteien
3. Kündigungsklauseln und Laufzeit
4. Haftungsregelungen
5. Potenzielle Risiken oder problematische Klauseln
6. AGB-Konformität (§§ 305-310 BGB)

Vertragsanalyse:"""

        response = await self.generate(prompt=prompt, max_tokens=1500)

        return MCPResponse(
            data={
                "analysis": response + self.LEGAL_DISCLAIMER,
                "contract_type": contract_type
            },
            confidence=0.78,
            requires_review=True,
            review_reason="Contract analysis should be verified by legal counsel",
            model_used=f"mixtral+{self.name}-lora"
        )

    async def _check_gdpr_compliance(self, data: Dict[str, Any]) -> MCPResponse:
        """Check GDPR/DSGVO compliance"""
        scope = data.get("scope", "general")

        prompt = f"""{self.SYSTEM_PROMPT}

Prüfe die DSGVO-Compliance für: {scope}

Zu prüfen:
1. Rechtsgrundlage der Verarbeitung (Art. 6 DSGVO)
2. Informationspflichten (Art. 13, 14 DSGVO)
3. Betroffenenrechte gewährleistet?
4. Verzeichnis von Verarbeitungstätigkeiten?
5. Technische und organisatorische Maßnahmen
6. Auftragsverarbeitung korrekt geregelt?

DSGVO-Compliance-Bericht:"""

        response = await self.generate(prompt=prompt, max_tokens=1200)

        return MCPResponse(
            data={"compliance_report": response},
            confidence=0.8,
            model_used=f"mixtral+{self.name}-lora"
        )

    async def _find_contracts(self, data: Dict[str, Any]) -> MCPResponse:
        """Find contracts in lakehouse"""
        party_name = data.get("party_name")
        contract_type = data.get("contract_type")

        # Build query
        conditions = ["category = 'contract'"]
        if party_name:
            conditions.append(f"content LIKE '%{party_name}%'")
        if contract_type:
            conditions.append(f"contract_type = '{contract_type}'")

        query = f"SELECT * FROM documents WHERE {' AND '.join(conditions)} LIMIT 20"

        contracts = self.query_data(query)

        return MCPResponse(
            data={
                "contracts": contracts,
                "count": len(contracts)
            },
            confidence=0.95,
            model_used="lakehouse_query"
        )

    def _needs_disclaimer(self, query: str) -> bool:
        """Check if query needs legal disclaimer"""
        disclaimer_keywords = [
            "rechtsverbindlich", "garantie", "haftung", "klage",
            "rechtssicher", "gericht", "anwalt", "verbindlich",
            "rechtsfolge", "schadensersatz"
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in disclaimer_keywords)

    def _needs_review(self, query: str) -> bool:
        """Check if query result needs expert review"""
        high_risk_keywords = [
            "klage", "gericht", "haftung", "kündigung",
            "vertrag aufheben", "schadensersatz", "strafbar"
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in high_risk_keywords)


# Factory function
def create_law_mcp() -> LAWMCP:
    """Create LAW MCP instance"""
    return LAWMCP()
