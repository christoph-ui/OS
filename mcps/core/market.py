"""
MARKET MCP - Market Intelligence & Competitive Analysis Engine

Flagship shared MCP providing 360° market intelligence by combining:
- Internal customer data (lakehouse)
- External web intelligence (Anthropic web search)
- Claude-powered synthesis and recommendations

Capabilities:
- Competitive product analysis
- Pricing intelligence across distributors
- Market coverage and gap analysis
- Strategic positioning recommendations
"""

import logging
import os
from typing import Any, Dict, Optional, List
from pathlib import Path
import anthropic

from mcps.sdk import BaseMCP, MCPContext, MCPResponse

logger = logging.getLogger(__name__)


class MarketMCP(BaseMCP):
    """
    Market Intelligence Engine

    Provides competitive intelligence, pricing analysis, and market insights
    by combining customer data with real-time web research.

    Features:
    - Multi-source intelligence (internal + web)
    - Competitive product comparison
    - Pricing analysis and recommendations
    - Market coverage gap analysis
    - Strategic positioning advice
    """

    # Required metadata
    name = "market"
    version = "1.0.0"
    description = "Market Intelligence & Competitive Analysis Engine"
    category = "intelligence"

    # Anthropic client for web search
    def __init__(self):
        super().__init__()
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not set - web search will be unavailable")
            self.anthropic = None
        else:
            self.anthropic = anthropic.Anthropic(api_key=api_key)

    async def process(
        self,
        input: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> MCPResponse:
        """
        Process market intelligence query.

        Args:
            input: Query string or structured request
            context: Customer context with lakehouse access

        Returns:
            MCPResponse with market analysis
        """
        self.log(f"Processing market intelligence query: {str(input)[:100]}...")

        # Handle different input types
        if isinstance(input, dict):
            task_type = input.get("task_type", "analyze_product")

            if task_type == "analyze_product":
                return await self._analyze_product(input, context)
            elif task_type == "pricing_intelligence":
                return await self._pricing_intelligence(input, context)
            elif task_type == "market_coverage":
                return await self._market_coverage(input, context)
            else:
                return await self._general_analysis(str(input), context)
        else:
            # Natural language query
            return await self._general_analysis(str(input), context)

    async def _analyze_product(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> MCPResponse:
        """
        360° product analysis combining internal data + web intelligence.

        Args:
            data: {
                "product_code": "FRCDM-40/4/03-G/B+",
                "include_web": true,
                "include_competitors": true
            }
        """
        product_code = data.get("product_code", "")
        include_web = data.get("include_web", True)
        include_competitors = data.get("include_competitors", True)

        # 1. Get internal data from customer lakehouse
        internal_data = await self._get_internal_data(product_code, context)

        # 2. Get external web intelligence
        web_data = {}
        if include_web and self.anthropic:
            web_data = await self._search_web(product_code, context)

        # 3. Get competitor data
        competitor_data = {}
        if include_competitors and self.anthropic:
            competitor_data = await self._get_competitor_intel(product_code, context)

        # 4. Synthesize with Claude
        analysis = await self._synthesize_analysis(
            product_code=product_code,
            internal=internal_data,
            web=web_data,
            competitors=competitor_data,
            context=context
        )

        return MCPResponse(
            data={
                "analysis": analysis,
                "sources": {
                    "internal": len(internal_data.get("documents", [])),
                    "web": len(web_data.get("results", [])),
                    "competitors": len(competitor_data.get("products", []))
                }
            },
            confidence=0.85,
            model_used="market-mcp-v1.0"
        )

    async def _get_internal_data(
        self,
        product_code: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Query customer's lakehouse for internal product data.
        """
        # Query lakehouse via context
        query = f"SELECT * FROM documents WHERE text LIKE '%{product_code}%' LIMIT 10"

        try:
            documents = self.query_data(query)
            return {
                "documents": documents,
                "count": len(documents)
            }
        except Exception as e:
            logger.error(f"Error querying internal data: {e}")
            return {"documents": [], "count": 0}

    async def _search_web(
        self,
        product_code: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Search web for product information using Anthropic web search.
        """
        if not self.anthropic:
            return {"results": [], "enabled": False}

        try:
            # Construct search query
            manufacturer = self._extract_manufacturer(context)
            search_query = f"{manufacturer} {product_code} specifications datasheet pricing"

            # Use Claude with web search tool
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": f"""Search the web for information about: {search_query}

Find:
1. Official product datasheet or technical specs
2. Pricing from major distributors (RS Components, Conrad, etc.)
3. Availability and lead times
4. Customer reviews or ratings
5. Technical documentation

Summarize findings in structured format."""
                }],
                tools=[{
                    "type": "web_search_20241111",
                    "name": "web_search"
                }]
            )

            # Extract web search results
            web_results = self._parse_web_results(response)

            return {
                "results": web_results,
                "enabled": True,
                "query": search_query
            }

        except Exception as e:
            logger.error(f"Web search error: {e}", exc_info=True)
            return {"results": [], "enabled": False, "error": str(e)}

    async def _get_competitor_intel(
        self,
        product_code: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get competitor product information via web search.
        """
        if not self.anthropic:
            return {"products": [], "enabled": False}

        try:
            # Search for alternatives
            search_query = f"{product_code} alternatives competitors equivalent products ABB Siemens Schneider"

            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": f"""Find competitor products similar to: {product_code}

Search for:
1. Direct competitors (ABB, Siemens, Schneider Electric, etc.)
2. Equivalent or alternative products
3. Pricing comparison
4. Feature/specification comparison
5. Market share or positioning

Return structured data with competitor products and key differentiators."""
                }],
                tools=[{
                    "type": "web_search_20241111",
                    "name": "web_search"
                }]
            )

            competitors = self._parse_competitor_results(response)

            return {
                "products": competitors,
                "enabled": True
            }

        except Exception as e:
            logger.error(f"Competitor intel error: {e}", exc_info=True)
            return {"products": [], "enabled": False, "error": str(e)}

    async def _synthesize_analysis(
        self,
        product_code: str,
        internal: Dict,
        web: Dict,
        competitors: Dict,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """
        Use Claude with web search to synthesize comprehensive analysis.
        """
        # Build comprehensive prompt with markdown enforcement
        synthesis_prompt = f"""You are a market intelligence analyst. Provide a comprehensive 360° competitive analysis of: **{product_code}**

**Available Data**:
- Internal customer data: {internal.get('count', 0)} documents
- Web intelligence: {web.get('enabled', False)}
- Competitor intel: {competitors.get('enabled', False)}

{self._format_internal_data(internal)}

**REQUIRED OUTPUT FORMAT** (strict markdown):

## 📊 Product Overview
Brief 2-3 sentence summary of the product and its market position.

## 🔍 Technical Specifications
### From Internal Data
- **Specification 1**: Value
- **Specification 2**: Value

### Verified via Web Search
- **Market Standard**: [From web research]
- **Compliance**: [Certifications found online]

## 🏆 Competitive Landscape
| Competitor | Product Model | Price Range | Key Differentiator |
|------------|---------------|-------------|-------------------|
| ABB | [Model] | €XXX-€XXX | [Feature] |
| Siemens | [Model] | €XXX-€XXX | [Feature] |
| Schneider | [Model] | €XXX-€XXX | [Feature] |

**Your Positioning**: [Premium/Value/Mid-market with rationale]

## 💰 Pricing Intelligence
- **Estimated List Price**: €XXX (based on web search)
- **Typical Distributor Price**: €XXX (RS Components, Conrad, etc.)
- **Market Average**: €XXX
- **Price Sensitivity**: [High/Medium/Low]

## 🌍 Market Insights
- **Primary Distributors**: [RS Components, Conrad, Farnell, etc.]
- **Availability**: [In stock / Lead time / Hard to source]
- **Customer Reviews**: [Summary of feedback if found]
- **Market Trends**: [Growing/Stable/Declining demand]

## 🎯 Strategic Recommendations

1. **Pricing Strategy**: [Specific action with €XX impact]
2. **Positioning**: [How to differentiate vs competitors]
3. **Distribution**: [Channels to prioritize or add]
4. **Product Enhancement**: [Feature gaps vs competitors]

## 🔗 Sources
- Internal: {internal.get('count', 0)} customer documents
- Web: [List key sources found via search]
- Competitor data: [Sources for competitive intel]

---
**💡 Next Steps**: [1-2 immediate actions to take]"""

        # Use Claude with web search
        if self.anthropic:
            try:
                logger.info("🌐 Synthesizing analysis with Claude web search")
                response = self.anthropic.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4000,
                    temperature=0.3,  # Lower for consistency
                    messages=[{
                        "role": "user",
                        "content": synthesis_prompt
                    }],
                    tools=[{
                        "type": "web_search_20241111",
                        "name": "web_search"
                    }]
                )

                # Extract all text blocks
                analysis = ""
                for block in response.content:
                    if hasattr(block, 'text'):
                        analysis += block.text

                return analysis

            except Exception as e:
                logger.error(f"Claude synthesis failed: {e}", exc_info=True)

        # Fallback to basic generation (without web search)
        logger.warning("Falling back to basic generation (no web search)")
        response = await self.generate(prompt=synthesis_prompt, max_tokens=3000)
        return response

    def _extract_manufacturer(self, context: Optional[Dict[str, Any]]) -> str:
        """Extract manufacturer from context or default to common."""
        # Could be enhanced to detect from data
        return "Eaton"  # Default for now

    def _format_internal_data(self, internal: Dict) -> str:
        """Format internal data for prompt."""
        docs = internal.get("documents", [])
        if not docs:
            return "No internal data available"

        formatted = ""
        for i, doc in enumerate(docs[:3], 1):
            filename = doc.get("filename", "Unknown")
            text = doc.get("text", "")[:500]
            formatted += f"\nDocument {i} ({filename}):\n{text}\n"

        return formatted

    def _format_web_data(self, web: Dict) -> str:
        """Format web search results for prompt."""
        if not web.get("enabled"):
            return "Web search not available"

        results = web.get("results", [])
        if not results:
            return "No web results found"

        return f"Found {len(results)} web sources with product information"

    def _format_competitor_data(self, competitors: Dict) -> str:
        """Format competitor data for prompt."""
        if not competitors.get("enabled"):
            return "Competitor intel not available"

        products = competitors.get("products", [])
        if not products:
            return "No competitor products found"

        return f"Found {len(products)} competing products"

    def _parse_web_results(self, response) -> List[Dict]:
        """Parse Anthropic API response for web search results."""
        # Extract tool use results from Claude response
        results = []

        for content_block in response.content:
            if hasattr(content_block, 'type') and content_block.type == 'tool_use':
                # Web search tool was used
                if hasattr(content_block, 'name') and content_block.name == 'web_search':
                    # Parse search results
                    results.append({
                        "type": "web_search",
                        "data": content_block.input if hasattr(content_block, 'input') else {}
                    })

        return results

    def _parse_competitor_results(self, response) -> List[Dict]:
        """Parse competitor products from web search."""
        # Similar to web results parsing
        return self._parse_web_results(response)

    async def _pricing_intelligence(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> MCPResponse:
        """
        Analyze pricing across market.
        """
        category = data.get("category", "")

        prompt = f"""Analyze pricing intelligence for product category: {category}

Provide:
1. Market price ranges
2. Pricing tiers (budget, mid, premium)
3. Your positioning
4. Pricing recommendations"""

        analysis = await self.generate(prompt=prompt, max_tokens=1500)

        return MCPResponse(
            data={"pricing_analysis": analysis},
            confidence=0.8,
            model_used="market-pricing-v1.0"
        )

    async def _market_coverage(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> MCPResponse:
        """
        Analyze market coverage and distribution gaps.
        """
        region = data.get("region", "Europe")

        prompt = f"""Analyze market coverage for region: {region}

Identify:
1. Key distributors in region
2. Coverage gaps
3. Competitor distribution strength
4. Expansion opportunities"""

        analysis = await self.generate(prompt=prompt, max_tokens=1500)

        return MCPResponse(
            data={"coverage_analysis": analysis},
            confidence=0.75,
            model_used="market-coverage-v1.0"
        )

    async def _general_analysis(
        self,
        query: str,
        context: Optional[Dict[str, Any]]
    ) -> MCPResponse:
        """
        Handle general market intelligence queries with web search enabled.
        """
        query_lower = query.lower()

        # Detect query types
        pricing_keywords = ["pricing", "price", "cost", "market pricing", "distributor"]
        competitor_keywords = ["competitor", "alternative", "vs", "compare", "versus", "abb", "siemens", "schneider"]
        product_keywords = ["analyze", "analysis", "360"]

        is_pricing_query = any(kw in query_lower for kw in pricing_keywords)
        is_competitor_query = any(kw in query_lower for kw in competitor_keywords)
        is_product_query = any(kw in query_lower for kw in product_keywords)

        # Extract product code (alphanumeric with hyphens)
        import re
        product_code_match = re.search(r'[A-Z0-9]{3,}[\-A-Z0-9]*', query)
        product_code = product_code_match.group(0) if product_code_match else None

        # For competitor/pricing queries, ALWAYS use web search
        if product_code and (is_competitor_query or is_pricing_query or is_product_query):
            logger.info(f"🌐 Routing to web-enabled analysis for: {product_code}")
            return await self._analyze_product(
                {
                    "product_code": product_code,
                    "include_web": True,
                    "include_competitors": True  # Always get competitors
                },
                context
            )

        # Fallback: Use Claude with web search (no product code)
        if not self.anthropic:
            # No Claude API - use basic analysis
            prompt = f"""Market Intelligence Query: {query}

Provide strategic market analysis with actionable recommendations.

Use markdown formatting:
## Overview
## Key Insights
## Recommendations"""

            response = await self.generate(prompt=prompt, max_tokens=2000)

            return MCPResponse(
                data={"analysis": response},
                confidence=0.6,
                model_used="market-basic"
            )

        # Use Claude with web search for general queries
        logger.info("🌐 Using Claude web search for general market query")

        try:
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=3000,
                temperature=0.4,
                messages=[{
                    "role": "user",
                    "content": f"""Market intelligence query: {query}

Use web search to find current market information, competitor data, and industry insights.

Format your response in markdown with these sections:
## Market Overview
## Key Findings
## Competitive Landscape
## Strategic Recommendations
## Sources

Be specific and actionable."""
                }],
                tools=[{
                    "type": "web_search_20241111",
                    "name": "web_search"
                }]
            )

            # Extract text response
            analysis = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    analysis += block.text

            return MCPResponse(
                data={"analysis": analysis},
                confidence=0.85,
                model_used="market-web-enabled"
            )

        except Exception as e:
            logger.error(f"Claude web search failed: {e}", exc_info=True)

            # Fallback to basic generation
            prompt = f"Provide market analysis for: {query}"
            response = await self.generate(prompt=prompt, max_tokens=2000)

            return MCPResponse(
                data={"analysis": response},
                confidence=0.6,
                model_used="market-fallback"
            )


# Factory function
def create_market_mcp() -> MarketMCP:
    """Create MARKET MCP instance"""
    return MarketMCP()
