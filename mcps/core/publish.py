"""
PUBLISH MCP - Multi-Channel Content Publishing Engine

Flagship shared MCP for generating professional content across all B2B channels.

Capabilities:
- E-commerce listing optimization (Amazon, RS Components, Conrad)
- Technical documentation generation (datasheets, guides)
- Marketing content (LinkedIn, email, blog)
- Distributor feed generation (BMEcat, ETIM, ECLASS)
- SEO optimization
- Multi-channel content packs
"""

import logging
from typing import Any, Dict, Optional, List

from mcps.sdk import BaseMCP, MCPContext, MCPResponse

logger = logging.getLogger(__name__)


# Channel-specific prompt templates
CHANNEL_PROMPTS = {
    "amazon_business": """Generate Amazon Business product listing optimized for B2B procurement.

**Target Audience**: Procurement managers, facility managers buying bulk (50+ units)
**Goal**: Maximize conversion for commercial/industrial buyers

**Requirements**:
1. **Title** (200 chars max):
   - Format: [Brand] [Model] [Product Type] - [Key Features], [Specs], [Certifications]
   - Keywords: Technical terms, application areas, compliance
   - Example: "Eaton FRCDM-40 Circuit Breaker - 40A 4-Pole Type B+ AC/DC, IEC Certified, Industrial (-25°C to 60°C)"

2. **Bullet Points** (5 max, start with benefit):
   - Benefit-Feature-Spec pattern
   - Example: "• **Premium Protection**: Type B+ detects AC/DC fault currents (superior to Type B)"

3. **Description** (2000 chars):
   - Problem statement (why they need this)
   - Solution (how product solves it)
   - Technical details
   - Applications
   - Compliance & certifications
   - Scannable with headings

4. **Backend Keywords** (250 chars):
   - Technical + commercial terms
   - Comma-separated

**Output as JSON**:
```json
{
  "title": "...",
  "bullets": ["...", "..."],
  "description": "...",
  "keywords": "..."
}
```""",

    "linkedin_post": """Create LinkedIn post for B2B product announcement.

**Target**: Decision-makers, facility managers, electrical engineers
**Tone**: Thought leadership, not promotional
**Goal**: Engagement + brand awareness

**Structure**:
1. **Hook** (first line): Industry pain point or insight
2. **Context**: Why this matters now (regulation, trend, challenge)
3. **Solution**: How product addresses it (innovation angle)
4. **Value**: Business impact (safety, efficiency, cost)
5. **CTA**: Soft call-to-action (learn more, technical specs)
6. **Hashtags**: 3-5 industry-relevant

**Example Hook**:
"Industrial equipment failures cost EU manufacturers €4.2B annually. 73% trace back to inadequate current protection."

**Max Length**: 1300 characters (LinkedIn optimal)""",

    "datasheet_content": """Generate professional product datasheet content.

**Format**: Technical document for engineers/specifiers

**Sections**:
1. **Product Overview** (2-3 sentences)
2. **Key Features** (6-8 bullet points)
3. **Technical Specifications** (table format)
4. **Compliance & Certifications**
5. **Applications** (typical use cases)
6. **Dimensions & Physical** (with diagram notes)
7. **Ordering Information** (part numbers, variants)

**Tone**: Precise, technical, authoritative
**Style**: Engineers making spec decisions""",

    "bmecat_xml": """Generate BMEcat 2005 XML with ETIM 5.0 extensions.

**Structure**:
```xml
<BMECAT version="2005">
  <HEADER>
    <CATALOG>
      <LANGUAGE>eng</LANGUAGE>
      <CATALOG_ID>...</CATALOG_ID>
      <DATETIME type="generation_date">...</DATETIME>
    </CATALOG>
  </HEADER>
  <T_NEW_CATALOG>
    <FEATURE_SYSTEM>
      <FEATURE_SYSTEM_NAME>ETIM-5.0</FEATURE_SYSTEM_NAME>
    </FEATURE_SYSTEM>
    <ARTICLE>
      <SUPPLIER_AID>...</SUPPLIER_AID>
      <ARTICLE_DETAILS>...</ARTICLE_DETAILS>
      <ARTICLE_FEATURES>...</ARTICLE_FEATURES>
    </ARTICLE>
  </T_NEW_CATALOG>
</BMECAT>
```

**Validation**: Must be XSD-compliant with BMEcat 2005 schema"""
}


class PublishMCP(BaseMCP):
    """
    Multi-Channel Content Publishing Engine

    Generates optimized content for every B2B channel from product data.

    One source of truth → Perfect content for every channel.
    """

    # Required metadata
    name = "publish"
    version = "1.0.0"
    description = "Multi-Channel Content Publishing Engine"
    category = "content"

    async def process(
        self,
        input: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> MCPResponse:
        """
        Process content generation request.

        Args:
            input: Generation request (channel + product)
            context: Customer context

        Returns:
            MCPResponse with generated content
        """
        self.log(f"Processing content generation: {str(input)[:100]}...")

        # Handle different input types
        if isinstance(input, dict):
            task_type = input.get("task_type", "generate_listing")

            if task_type == "generate_listing":
                return await self._generate_listing(input, context)
            elif task_type == "generate_datasheet":
                return await self._generate_datasheet(input, context)
            elif task_type == "generate_content_pack":
                return await self._generate_content_pack(input, context)
            elif task_type == "generate_bmecat":
                return await self._generate_bmecat(input, context)
            else:
                return await self._general_generation(str(input), context)
        else:
            return await self._general_generation(str(input), context)

    async def _generate_listing(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> MCPResponse:
        """
        Generate e-commerce listing for specific platform.

        Args:
            data: {
                "product_code": "FRCDM-40/4/03-G/B+",
                "platform": "amazon_business",  # amazon, rs_components, conrad
            }
        """
        product_code = data.get("product_code", "")
        platform = data.get("platform", "amazon_business")

        # Get product data from lakehouse
        product_data = await self._get_product_data(product_code, context)

        # Get channel-specific prompt with markdown structure
        channel_prompt = CHANNEL_PROMPTS.get(platform, CHANNEL_PROMPTS["amazon_business"])

        # Enhanced prompt with markdown formatting
        prompt = f"""{channel_prompt}

**Product Data**:
{self._format_product_data(product_data)}

**OUTPUT IN MARKDOWN FORMAT**:

# {product_code} - Amazon Business Listing

## Product Title
[200 char optimized title here]

## Key Features (Bullet Points)
1. **[Benefit]**: [Feature] ([Spec])
2. **[Benefit]**: [Feature] ([Spec])
3. **[Benefit]**: [Feature] ([Spec])
4. **[Benefit]**: [Feature] ([Spec])
5. **[Benefit]**: [Feature] ([Spec])

## Product Description
[Full 2000 char description with headings]

### Applications
- [Use case 1]
- [Use case 2]

### Specifications
- [Key spec 1]
- [Key spec 2]

### Compliance & Certifications
- [Cert 1]
- [Cert 2]

## Backend Keywords
[Comma-separated technical + commercial terms]

---
**💡 Procurement Note**: [Why B2B buyers should choose this]

Generate now:"""

        listing = await self.generate(
            prompt=prompt,
            max_tokens=3000,  # Increased for full listing
            temperature=0.2  # Very low for consistency
        )

        return MCPResponse(
            data={
                "listing": listing,
                "platform": platform,
                "product_code": product_code,
                "format": "markdown"
            },
            confidence=0.9,
            model_used=f"publish-{platform}-v1.0"
        )

    async def _generate_datasheet(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> MCPResponse:
        """
        Generate professional product datasheet content with strict formatting.
        """
        product_code = data.get("product_code", "")

        # Get product data
        product_data = await self._get_product_data(product_code, context)

        # Enhanced prompt with markdown structure
        prompt = f"""{CHANNEL_PROMPTS["datasheet_content"]}

**Product Data**:
{self._format_product_data(product_data)}

**OUTPUT IN PROFESSIONAL MARKDOWN FORMAT**:

---
# PRODUCT DATASHEET
# {product_code}

## Product Overview
[2-3 sentence technical summary for engineers]

**Manufacturer**: [Name]
**Product Line**: [Series]
**Category**: [Type]

---

## Key Features
- ✓ **[Feature 1]**: [Technical detail]
- ✓ **[Feature 2]**: [Technical detail]
- ✓ **[Feature 3]**: [Technical detail]
- ✓ **[Feature 4]**: [Technical detail]
- ✓ **[Feature 5]**: [Technical detail]
- ✓ **[Feature 6]**: [Technical detail]

---

## Technical Specifications

| Parameter | Value | Unit |
|-----------|-------|------|
| [Param 1] | [Value] | [Unit] |
| [Param 2] | [Value] | [Unit] |
| [Param 3] | [Value] | [Unit] |

---

## Compliance & Certifications
- ✓ **[Standard 1]**: [Details]
- ✓ **[Standard 2]**: [Details]
- ✓ **[Certification 1]**
- ✓ **[Certification 2]**

---

## Typical Applications
1. **[Application 1]**: [Context where used]
2. **[Application 2]**: [Context where used]
3. **[Application 3]**: [Context where used]

---

## Ordering Information
**Part Number**: {product_code}
**EAN/UPC**: [Code]
**Available Variants**: [If applicable]

---

## Technical Support
For specifications, dimensions, and CAD files: [Contact/URL]

---
*Document generated: {product_code} Technical Datasheet*

Generate now:"""

        content = await self.generate(prompt=prompt, max_tokens=4000)

        return MCPResponse(
            data={
                "content": content,
                "format": "markdown",
                "product_code": product_code
            },
            confidence=0.95,
            model_used="publish-datasheet-v1.0"
        )

    async def _generate_content_pack(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> MCPResponse:
        """
        Generate complete content pack across all channels.
        """
        product_code = data.get("product_code", "")
        channels = data.get("channels", ["amazon", "linkedin", "datasheet"])

        # Get product data once
        product_data = await self._get_product_data(product_code, context)

        # Generate for each channel
        generated = {}
        for channel in channels:
            result = await self._generate_for_channel(
                channel, product_code, product_data
            )
            generated[channel] = result

        return MCPResponse(
            data={
                "content_pack": generated,
                "channels": channels,
                "product_code": product_code
            },
            confidence=0.85,
            model_used="publish-content-pack-v1.0"
        )

    async def _generate_bmecat(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> MCPResponse:
        """
        Generate BMEcat XML export for distributors.
        """
        products = data.get("products", [])

        prompt = f"""{CHANNEL_PROMPTS["bmecat_xml"]}

Generate BMEcat 2005 XML for {len(products)} products.

Product data: {products[:5]}  # Sample

Provide complete XML structure."""

        xml = await self.generate(prompt=prompt, max_tokens=4000)

        return MCPResponse(
            data={
                "xml": xml,
                "format": "bmecat_2005",
                "products_count": len(products)
            },
            confidence=0.85,
            model_used="publish-bmecat-v1.0"
        )

    async def _get_product_data(
        self,
        product_code: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Retrieve product data from customer lakehouse.
        """
        query = f"SELECT * FROM documents WHERE text LIKE '%{product_code}%' LIMIT 5"

        try:
            documents = self.query_data(query)
            return {
                "documents": documents,
                "product_code": product_code
            }
        except Exception as e:
            logger.error(f"Error getting product data: {e}")
            return {"documents": [], "product_code": product_code}

    def _format_product_data(self, data: Dict) -> str:
        """Format product data for prompt."""
        docs = data.get("documents", [])
        if not docs:
            return f"Product: {data.get('product_code', 'Unknown')}\nNo data available"

        formatted = f"Product: {data.get('product_code', 'Unknown')}\n\n"
        for doc in docs[:2]:
            formatted += f"From {doc.get('filename', 'Unknown')}:\n"
            formatted += f"{doc.get('text', '')[:1000]}\n\n"

        return formatted

    async def _generate_for_channel(
        self,
        channel: str,
        product_code: str,
        product_data: Dict
    ) -> str:
        """Generate content for specific channel."""
        prompt_template = CHANNEL_PROMPTS.get(channel, "Generate professional content")

        prompt = f"""{prompt_template}

Product: {product_code}
Data: {self._format_product_data(product_data)}

Generate now:"""

        return await self.generate(prompt=prompt, max_tokens=2000)

    async def _general_generation(
        self,
        query: str,
        context: Optional[Dict[str, Any]]
    ) -> MCPResponse:
        """
        Handle general content generation requests with markdown formatting.
        """
        prompt = f"""Content Generation Request: {query}

Generate professional B2B content following best practices.

**OUTPUT IN MARKDOWN FORMAT** with clear structure:

# [Content Title]

## Overview
[Brief introduction]

## Main Content
[Detailed content with headings, bullets, tables as needed]

## Call to Action
[Next steps or action items]

---
*Generated by 0711 PUBLISH Engine*

Generate now:"""

        content = await self.generate(prompt=prompt, max_tokens=3000)

        return MCPResponse(
            data={"content": content, "format": "markdown"},
            confidence=0.75,
            model_used=f"publish-{self.name}"
        )


# Factory function
def create_publish_mcp() -> PublishMCP:
    """Create PUBLISH MCP instance"""
    return PublishMCP()
