"""
AI-Powered Category Discovery Service

Dynamically discovers data categories for each customer using Claude.
No more static categories - adapts to what the customer actually has.
"""

import anthropic
from typing import List, Dict, Optional
from pathlib import Path
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class CategoryDiscoveryService:
    """
    Discovers natural data categories using Claude AI

    Instead of forcing tax/legal/contract categories,
    analyzes customer's actual data and suggests 3-7 relevant categories.
    """

    def __init__(self, anthropic_api_key: str):
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)

    async def discover_categories(
        self,
        customer_id: str,
        sample_files: List[Dict],
        existing_content_samples: List[str] = None
    ) -> List[Dict]:
        """
        Analyze customer data and discover natural categories

        Args:
            customer_id: Customer UUID
            sample_files: List of dicts with {filename, size, path}
            existing_content_samples: Optional text samples from documents

        Returns:
            List of discovered categories:
            [{
                "category_key": "product_management",
                "category_name": "Product Management",
                "description": "Product catalogs, ECLASS classifications...",
                "icon": "📦",
                "color": "#6a9bcc",
                "estimated_docs": 450,
                "confidence": 0.95
            }, ...]
        """

        # Build analysis prompt
        prompt = self._build_discovery_prompt(sample_files, existing_content_samples)

        try:
            # Call Claude
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Parse response
            response_text = message.content[0].text
            categories = self._parse_category_response(response_text)

            logger.info(f"Discovered {len(categories)} categories for customer {customer_id}")
            return categories

        except Exception as e:
            logger.error(f"Category discovery failed: {e}")
            # Fallback to generic category
            return [{
                "category_key": "general",
                "category_name": "General Documents",
                "description": "Uncategorized documents",
                "icon": "📄",
                "color": "#b0aea5",
                "estimated_docs": len(sample_files),
                "confidence": 1.0
            }]

    def _build_discovery_prompt(
        self,
        sample_files: List[Dict],
        content_samples: List[str] = None
    ) -> str:
        """Build prompt for Claude to discover categories"""

        # Group files by extension
        extensions = {}
        for file in sample_files[:100]:  # Sample first 100
            ext = Path(file['filename']).suffix.lower()
            extensions[ext] = extensions.get(ext, 0) + 1

        # Sample filenames
        filenames = [f['filename'] for f in sample_files[:50]]

        prompt = f"""Analyze this customer's data and discover 3-7 natural categories that represent how their business is organized.

FILE STATISTICS:
- Total files: {len(sample_files)}
- File types: {json.dumps(extensions, indent=2)}

SAMPLE FILENAMES:
{chr(10).join(f'- {name}' for name in filenames[:30])}

"""

        if content_samples:
            prompt += f"""
CONTENT SAMPLES (first 500 chars each):
{chr(10).join(f'--- Sample {i+1} ---{chr(10)}{sample[:500]}...' for i, sample in enumerate(content_samples[:5]))}
"""

        prompt += """

TASK:
Discover 3-7 natural categories that reflect how this business actually organizes their data.

GUIDELINES:
1. Categories should match business departments or functions (Product, Engineering, Sales, Finance, Legal, HR, Operations, Marketing, etc.)
2. Each category should have at least 5% of total documents (avoid tiny categories)
3. Use clear, business-friendly names (not technical jargon)
4. Suggest an appropriate emoji icon for each
5. Provide a 1-sentence description

OUTPUT FORMAT (JSON only, no markdown):
{
  "categories": [
    {
      "category_key": "product_management",
      "category_name": "Product Management",
      "description": "Product catalogs, ECLASS classifications, SKU management, and product specifications",
      "icon": "📦",
      "color": "#6a9bcc",
      "estimated_percentage": 65,
      "confidence": 0.95,
      "reasoning": "Majority of files are ECLASS XML catalogs and product-related"
    },
    {
      "category_key": "engineering",
      "category_name": "Engineering",
      "description": "3D CAD models, technical drawings, and product specifications",
      "icon": "⚙️",
      "color": "#788c5d",
      "estimated_percentage": 20,
      "confidence": 0.90,
      "reasoning": ".stp files are 3D CAD models used by engineering teams"
    }
  ]
}

Return ONLY valid JSON, no explanation text."""

        return prompt

    def _parse_category_response(self, response: str) -> List[Dict]:
        """Parse Claude's JSON response into category list"""
        try:
            # Extract JSON from response (in case Claude adds explanation)
            json_start = response.find('{')
            json_end = response.rfind('}') + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                return data.get('categories', [])
            else:
                logger.error(f"No JSON found in response: {response}")
                return []

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse category JSON: {e}")
            logger.error(f"Response was: {response}")
            return []

    async def classify_document_dynamic(
        self,
        filename: str,
        content_sample: str,
        existing_categories: List[Dict],
        customer_id: str
    ) -> Dict:
        """
        Classify a single document into one of the discovered categories

        Args:
            filename: Document filename
            content_sample: First 2KB of content
            existing_categories: List of discovered categories
            customer_id: Customer UUID

        Returns:
            {
                "category_key": "product_management",
                "confidence": 0.92,
                "reasoning": "Contains ECLASS product data"
            }
        """

        category_list = "\n".join([
            f"- {cat['category_key']}: {cat['description']}"
            for cat in existing_categories
        ])

        prompt = f"""Classify this document into one of the predefined categories.

FILENAME: {filename}

CONTENT SAMPLE (first 2000 chars):
{content_sample[:2000]}

AVAILABLE CATEGORIES:
{category_list}

TASK:
Determine which category this document belongs to. If it doesn't fit any category well, suggest "general" or propose a new category.

OUTPUT FORMAT (JSON only):
{{
  "category_key": "product_management",
  "confidence": 0.92,
  "reasoning": "Contains ECLASS product classification data",
  "new_category_suggestion": null
}}

If the document fits an existing category poorly (confidence < 0.6), suggest a new category in "new_category_suggestion".

Return ONLY valid JSON."""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text

            # Parse JSON
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start >= 0:
                result = json.loads(response_text[json_start:json_end])
                return result
            else:
                logger.error(f"No JSON in classification response")
                return {"category_key": "general", "confidence": 0.5, "reasoning": "Parse error"}

        except Exception as e:
            logger.error(f"Document classification failed: {e}")
            return {"category_key": "general", "confidence": 0.5, "reasoning": str(e)}

    async def suggest_new_category(
        self,
        problematic_files: List[Dict],
        existing_categories: List[Dict]
    ) -> Optional[Dict]:
        """
        When documents don't fit existing categories, suggest a new one

        Args:
            problematic_files: Files that didn't match well
            existing_categories: Current categories

        Returns:
            New category suggestion or None
        """

        if len(problematic_files) < 3:
            return None  # Need at least 3 files to justify new category

        filenames = [f['filename'] for f in problematic_files[:20]]

        prompt = f"""These {len(problematic_files)} documents don't fit well into existing categories.

EXISTING CATEGORIES:
{json.dumps([c['category_name'] for c in existing_categories], indent=2)}

UNCATEGORIZED FILES:
{chr(10).join(f'- {name}' for name in filenames)}

TASK:
Should we create a new category for these files? If yes, suggest the category.

OUTPUT FORMAT (JSON only):
{{
  "create_new": true,
  "category_key": "suggested_key",
  "category_name": "Suggested Name",
  "description": "What this category contains",
  "icon": "📊",
  "color": "#colorhex",
  "reasoning": "Why this category is needed"
}}

If these files should just go into "general", return {{"create_new": false}}.

Return ONLY valid JSON."""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start >= 0:
                suggestion = json.loads(response_text[json_start:json_end])
                if suggestion.get('create_new'):
                    return suggestion

            return None

        except Exception as e:
            logger.error(f"New category suggestion failed: {e}")
            return None


# Singleton instance (will be initialized with API key from settings)
category_discovery_service = None

def get_category_discovery_service(api_key: str = None) -> CategoryDiscoveryService:
    """Get or create category discovery service"""
    global category_discovery_service

    if category_discovery_service is None and api_key:
        category_discovery_service = CategoryDiscoveryService(api_key)

    return category_discovery_service
