"""
Intelligent Extractor - Claude-powered data extraction using deployment context

Reads DEPLOYMENT.md to understand:
- Customer industry and use case
- Expected data format
- Field mapping rules (JSON path → SQL column)
- Transformation logic

Uses Claude Sonnet 4.5 to:
- Parse complex nested JSON/XML
- Extract fields per deployment rules
- Validate data quality
- Return structured records for standard tables
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None

logger = logging.getLogger(__name__)


class IntelligentExtractor:
    """
    Claude-powered data extraction using deployment context.

    Transforms any source format into standard lakehouse schemas by:
    1. Reading DEPLOYMENT.md for customer-specific transformation rules
    2. Using Claude to intelligently extract and map fields
    3. Validating against standard schemas
    4. Returning structured records ready for Delta Lake
    """

    def __init__(self, claude_api_key: Optional[str] = None):
        """
        Initialize intelligent extractor.

        Args:
            claude_api_key: Anthropic API key for Claude access
        """
        self.claude_api_key = claude_api_key
        self.client = None

        if claude_api_key and ANTHROPIC_AVAILABLE:
            self.client = anthropic.Anthropic(api_key=claude_api_key)
            logger.info("✅ Intelligent Extractor initialized with Claude Sonnet 4.5")
        else:
            if not ANTHROPIC_AVAILABLE:
                logger.warning("⚠️ anthropic package not installed - intelligent extraction disabled")
            else:
                logger.warning("⚠️ No Claude API key - intelligent extraction disabled")

    async def extract_to_standard_schema(
        self,
        file_content: str,
        deployment_context: Dict,
        classification: str,
        filename: str = "unknown"
    ) -> Dict[str, List[Dict]]:
        """
        Extract structured data using deployment-specific rules.

        Args:
            file_content: Raw file content (JSON/XML/CSV text)
            deployment_context: Parsed DEPLOYMENT.md context
            classification: MCP classification (products, tax, legal, etc.)
            filename: Original filename for logging

        Returns:
            {
                "products": [{gtin, brand, price, ...}],
                "syndication_products": [{...}],
                "data_quality": {...},
                "general_documents": [{...}]
            }
        """
        if not self.client:
            logger.warning(f"Claude not available - skipping intelligent extraction for {filename}")
            return self._fallback_extraction(file_content, classification, filename)

        # Only extract structured data for products classification
        if classification != "products":
            logger.debug(f"Skipping structured extraction for classification: {classification}")
            return {}

        try:
            # Build Claude prompt with deployment context
            prompt = self._build_extraction_prompt(
                file_content,
                deployment_context,
                classification,
                filename
            )

            # Call Claude to extract
            logger.debug(f"Calling Claude to extract structured data from {filename}")
            response = await self._call_claude(prompt)

            # Parse and validate response
            extracted = self._parse_extraction_result(response, filename)

            # Validate against expected schemas
            validated = self._validate_records(extracted, filename)

            logger.info(f"✓ Extracted {len(validated.get('products', []))} product records from {filename}")

            return validated

        except Exception as e:
            logger.error(f"Intelligent extraction failed for {filename}: {e}", exc_info=True)
            return self._fallback_extraction(file_content, classification, filename)

    def _build_extraction_prompt(
        self,
        file_content: str,
        deployment_context: Dict,
        classification: str,
        filename: str
    ) -> str:
        """
        Build Claude prompt with deployment context and extraction instructions.
        """
        company_name = deployment_context.get("company_name", "Unknown")
        industry = deployment_context.get("industry", "Unknown")
        source_format = deployment_context.get("source_format", "JSON")
        transformation_rules = deployment_context.get("transformation_rules", {})

        # Truncate file content to fit in prompt (keep first 8000 chars)
        content_preview = file_content[:8000]
        if len(file_content) > 8000:
            content_preview += f"\n\n... [TRUNCATED - {len(file_content) - 8000} chars omitted]"

        prompt = f"""You are processing data for: {company_name}
Industry: {industry}

TASK: Extract structured product data from the source file and map it to our standard database schema.

SOURCE FILE: {filename}
CLASSIFICATION: {classification}
EXPECTED FORMAT: {source_format}

TRANSFORMATION RULES (from DEPLOYMENT.md):
{json.dumps(transformation_rules, indent=2)}

SOURCE DATA:
{content_preview}

STANDARD SCHEMA TO POPULATE:

1. **products** table - Main product catalog:
   - gtin (STRING, PRIMARY KEY) - Global Trade Item Number
   - supplier_pid (STRING) - Supplier product ID
   - manufacturer_pid (STRING, optional) - Manufacturer product ID
   - brand (STRING) - Brand name
   - product_name (STRING) - Product name/title
   - short_description (TEXT, optional) - Short description
   - long_description (TEXT, optional) - Long description
   - price (DECIMAL, optional) - List price
   - currency (STRING, default "EUR") - Currency code
   - etim_class (STRING, optional) - ETIM classification code
   - eclass_id (STRING, optional) - ECLASS classification
   - manufacturer_name (STRING, optional) - Manufacturer name
   - product_type (STRING, optional) - Product type/category
   - status (STRING, default "active") - active, discontinued
   - metadata (JSON) - Store the complete source JSON here for reference

2. **syndication_products** table - Export-ready format:
   - id (STRING, PRIMARY KEY) - Usually same as GTIN
   - gtin (STRING)
   - supplier_pid (STRING)
   - product_name (STRING)
   - description (TEXT)
   - price (DECIMAL, optional)
   - currency (STRING)
   - etim_class (STRING, optional)
   - eclass_id (STRING, optional)
   - manufacturer (STRING)
   - brand (STRING)
   - images (JSON array) - Image URLs/metadata
   - cad_files (JSON array, optional) - CAD file URLs/metadata
   - technical_specs (JSON object) - Structured technical specifications
   - compliance_data (JSON object) - Certifications, regulations
   - bmecat_ready (BOOLEAN) - True if BMEcat export ready
   - etim_compliant (BOOLEAN) - True if ETIM format compliant

3. **data_quality_audit** table - Quality tracking:
   - completeness_percentage (INTEGER 0-100)
   - data_sources (JSON) - Breakdown by source (from_database, estimated, etc.)
   - confidence_levels (JSON) - Fields categorized by confidence (high, medium, low)
   - extraction_notes (JSON array) - Processing notes

INSTRUCTIONS:
1. Parse the source data according to the transformation rules
2. Extract ALL products found in the file (there may be multiple)
3. Map fields using the JSON paths specified in transformation rules
4. For missing optional fields, use null
5. Preserve the complete source JSON in metadata field
6. Extract data_quality information if present in source
7. Set bmecat_ready=true and etim_compliant=true if ETIM/ECLASS codes present

OUTPUT FORMAT (JSON only, no explanation):
{{
  "products": [
    {{
      "gtin": "extracted_gtin",
      "supplier_pid": "extracted_pid",
      "brand": "extracted_brand",
      "product_name": "extracted_name",
      "price": 43.0,
      "currency": "EUR",
      "etim_class": "EC001764",
      "eclass_id": "27-24-11-01",
      "manufacturer_name": "Manufacturer",
      "product_type": "Product Type",
      "status": "active",
      "metadata": {{original_json_object}}
    }}
  ],
  "syndication_products": [
    {{
      "id": "same_as_gtin",
      "gtin": "...",
      "supplier_pid": "...",
      "product_name": "...",
      "description": "long_description_here",
      "price": 43.0,
      "currency": "EUR",
      "etim_class": "EC001764",
      "eclass_id": "27-24-11-01",
      "manufacturer": "Manufacturer Name",
      "brand": "Brand",
      "images": [{{}}],
      "technical_specs": {{}},
      "compliance_data": {{}},
      "bmecat_ready": true,
      "etim_compliant": true
    }}
  ],
  "data_quality": {{
    "completeness_percentage": 75,
    "data_sources": {{"from_database": 25, "estimated": 12}},
    "confidence_levels": {{"high": ["gtin", "brand"], "medium": ["price"]}},
    "extraction_notes": ["Note 1", "Note 2"]
  }}
}}

Return ONLY valid JSON. No markdown, no explanation, just the JSON object.
"""

        return prompt

    async def _call_claude(self, prompt: str) -> str:
        """
        Call Claude API to extract structured data.

        Args:
            prompt: Extraction prompt

        Returns:
            Claude's response text
        """
        try:
            # Use synchronous client (anthropic SDK doesn't have async)
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",  # Claude Sonnet 4.5
                max_tokens=4096,
                temperature=0.0,  # Deterministic for data extraction
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            return message.content[0].text

        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            raise

    def _parse_extraction_result(self, response: str, filename: str) -> Dict[str, List[Dict]]:
        """
        Parse Claude's JSON response.

        Args:
            response: Claude's response text
            filename: Original filename for logging

        Returns:
            Parsed extraction result
        """
        try:
            # Claude should return pure JSON
            # Try to extract JSON if wrapped in markdown
            response = response.strip()

            # Remove markdown code blocks if present
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]

            response = response.strip()

            # Parse JSON
            result = json.loads(response)

            # Validate structure
            if not isinstance(result, dict):
                raise ValueError("Response is not a JSON object")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response for {filename}: {e}")
            logger.debug(f"Response was: {response[:500]}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error parsing response for {filename}: {e}")
            return {}

    def _validate_records(self, extracted: Dict[str, Any], filename: str) -> Dict[str, List[Dict]]:
        """
        Validate extracted records against expected schemas.

        Args:
            extracted: Extracted data from Claude
            filename: Original filename for logging

        Returns:
            Validated records
        """
        validated = {
            "products": [],
            "syndication_products": [],
            "data_quality": []
        }

        # Validate products
        if "products" in extracted and isinstance(extracted["products"], list):
            for i, product in enumerate(extracted["products"]):
                if not isinstance(product, dict):
                    logger.warning(f"Product {i} in {filename} is not a dict")
                    continue

                # Required fields
                if "gtin" not in product or "supplier_pid" not in product:
                    logger.warning(f"Product {i} in {filename} missing required fields (gtin or supplier_pid)")
                    continue

                validated["products"].append(product)

        # Validate syndication_products
        if "syndication_products" in extracted and isinstance(extracted["syndication_products"], list):
            for i, product in enumerate(extracted["syndication_products"]):
                if not isinstance(product, dict):
                    logger.warning(f"Syndication product {i} in {filename} is not a dict")
                    continue

                validated["syndication_products"].append(product)

        # Validate data_quality
        if "data_quality" in extracted and isinstance(extracted["data_quality"], dict):
            validated["data_quality"].append(extracted["data_quality"])

        logger.debug(f"Validated {len(validated['products'])} products, "
                    f"{len(validated['syndication_products'])} syndication products, "
                    f"{len(validated['data_quality'])} quality records from {filename}")

        return validated

    def _fallback_extraction(
        self,
        file_content: str,
        classification: str,
        filename: str
    ) -> Dict[str, List[Dict]]:
        """
        Fallback extraction when Claude is not available.

        Returns empty structure - data will be stored as text only.
        """
        logger.warning(f"Using fallback extraction (text-only) for {filename}")
        return {
            "products": [],
            "syndication_products": [],
            "data_quality": []
        }
