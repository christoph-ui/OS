"""
Image Handler with OpenAI Vision API

Extracts:
- Product orientation (front, top, side, perspective view) - ENGLISH
- SEO-optimized descriptions - ENGLISH
- ETIM/BMEcat relevant metadata - ENGLISH
- Technical specifications visible in image
- All output in English for international catalogs

Uses OpenAI GPT-4 Vision for analysis.
"""

import logging
from pathlib import Path
from typing import Optional, Dict
import base64
import json
import os

from .base import BaseHandler

logger = logging.getLogger(__name__)


class ImageVisionHandler(BaseHandler):
    """
    Extract metadata from product images using OpenAI Vision API.

    Optimized for ETIM/BMEcat product catalogs.
    All metadata extracted in English.
    """

    @classmethod
    def supported_extensions(cls) -> set[str]:
        return {'.jpg', '.jpeg', '.png', '.webp'}

    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set - image analysis will be skipped")

    async def extract(self, path: Path) -> Optional[str]:
        """
        Extract metadata from product image using Vision API.

        Returns structured text suitable for RAG:
        - SEO description (English)
        - Product orientation (English: front_view, top_view, etc.)
        - Visible specifications
        - ETIM-relevant attributes
        """
        if not self.api_key:
            logger.debug(f"Skipping vision analysis for {path.name} (no API key)")
            return None

        try:
            # Read and encode image
            with open(path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()

            # Call OpenAI Vision API
            import httpx

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4o",
                        "messages": [{
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": self._build_analysis_prompt(path.name)
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_data}"
                                    }
                                }
                            ]
                        }],
                        "max_tokens": 500
                    }
                )

            if response.status_code != 200:
                logger.error(f"OpenAI Vision API failed: {response.status_code} - {response.text}")
                return None

            result = response.json()
            analysis_text = result['choices'][0]['message']['content']

            # Parse JSON response
            metadata = self._parse_vision_response(analysis_text, path.name)

            # Format as searchable text
            return self._format_for_rag(metadata, path.name)

        except Exception as e:
            logger.error(f"Vision analysis failed for {path.name}: {e}")
            return None

    def _build_analysis_prompt(self, filename: str) -> str:
        """Build prompt for OpenAI Vision API - ALL IN ENGLISH"""

        return f"""Analyze this product image for an electrical/industrial catalog (ETIM/BMEcat standard).

FILENAME: {filename}

Extract the following metadata IN ENGLISH:

1. PRODUCT VIEW (required):
   - Orientation: front_view, top_view, side_view, perspective_view, back_view, detail_view, bottom_view
   - Perspective: center, left, right, angled
   - Example: "front_view" + "center" OR "top_view" + "angled"

2. PRODUCT IDENTIFICATION (if visible):
   - Product type in English (e.g., "circuit breaker", "UPS", "switch", "connector")
   - Model/part number visible on product
   - Brand/manufacturer markings

3. TECHNICAL SPECS (if visible on product):
   - Voltage rating (e.g., "230V", "400V")
   - Current rating (e.g., "16A", "40A")
   - Pole count (e.g., "4-pole", "1-pole")
   - Any text/labels visible on product

4. SEO DESCRIPTION (1-2 sentences in English):
   - Professional description for product catalog
   - Include key specifications visible
   - Format: "Professional [view] of [product type] showing [key features]"
   - Example: "Professional front view of 4-pole circuit breaker showing 40A rating and Eaton branding"

5. ETIM/BMEcat ATTRIBUTES:
   - image_purpose: product_photo, detail_shot, application_photo
   - quality: high, medium, low
   - background: white, gray, contextual
   - lighting: studio, natural, mixed

OUTPUT FORMAT (JSON only, no markdown, no explanation):
{{
  "view_orientation": "front_view",
  "view_perspective": "center",
  "product_type": "circuit breaker",
  "model_number": "FRCDM-40/4/03",
  "visible_specs": {{
    "current_rating": "40A",
    "pole_count": "4",
    "voltage": "400V",
    "visible_text": ["FRCDM-40", "Eaton", "400V"]
  }},
  "seo_description": "Professional front center view of 4-pole circuit breaker showing 40A rating, 400V specification, and Eaton branding with clear product identification",
  "etim_attributes": {{
    "image_purpose": "product_photo",
    "quality": "high",
    "background": "white",
    "lighting": "studio"
  }}
}}

IMPORTANT: All text must be in English. German terms like "Ansicht" should be "view", "Ausrichtung" should be "orientation".

Return ONLY valid JSON with no markdown code blocks."""

    def _parse_vision_response(self, response_text: str, filename: str) -> Dict:
        """Parse OpenAI Vision response"""
        try:
            # Remove markdown code blocks if present
            text = response_text.strip()
            if text.startswith("```"):
                lines = text.split('\n')
                text = '\n'.join(lines[1:-1])
                if text.startswith("json"):
                    text = text[4:]

            # Extract JSON
            json_start = text.find('{')
            json_end = text.rfind('}') + 1

            if json_start >= 0 and json_end > json_start:
                json_str = text[json_start:json_end]
                return json.loads(json_str)
            else:
                logger.warning(f"No JSON in vision response for {filename}")
                return {}

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse vision JSON for {filename}: {e}")
            logger.error(f"Response was: {response_text[:500]}")
            return {}

    def _format_for_rag(self, metadata: Dict, filename: str) -> str:
        """
        Format extracted metadata as searchable text for RAG.

        This text will be embedded and searchable via semantic search.
        All in English for international use.
        """
        if not metadata:
            return f"Product Image: {filename}"

        parts = [
            f"PRODUCT IMAGE: {filename}",
            "",
            f"VIEW ORIENTATION: {metadata.get('view_orientation', 'unknown').replace('_', ' ').title()}",
            f"VIEW PERSPECTIVE: {metadata.get('view_perspective', 'center').title()}",
            f"PRODUCT TYPE: {metadata.get('product_type', 'unknown').title()}",
            ""
        ]

        # Add model number if found
        if metadata.get('model_number'):
            parts.append(f"MODEL NUMBER: {metadata['model_number']}")
            parts.append("")

        # Add SEO description
        parts.append(f"DESCRIPTION: {metadata.get('seo_description', 'Product image')}")
        parts.append("")

        # Add visible specs
        visible_specs = metadata.get('visible_specs', {})
        if visible_specs:
            parts.append("VISIBLE SPECIFICATIONS:")
            for key, value in visible_specs.items():
                if isinstance(value, list):
                    if value:  # Only show if not empty
                        parts.append(f"  {key.replace('_', ' ').title()}: {', '.join(str(v) for v in value)}")
                elif value:  # Only show if not empty/None
                    parts.append(f"  {key.replace('_', ' ').title()}: {value}")
            parts.append("")

        # Add ETIM attributes
        etim_attrs = metadata.get('etim_attributes', {})
        if etim_attrs:
            parts.append("ETIM/BMEcat ATTRIBUTES:")
            for key, value in etim_attrs.items():
                parts.append(f"  {key.replace('_', ' ').title()}: {value}")
            parts.append("")

        # Add searchable keywords
        keywords = []
        if metadata.get('view_orientation'):
            keywords.append(metadata['view_orientation'].replace('_', ' '))
        if metadata.get('product_type'):
            keywords.append(metadata['product_type'])
        if visible_specs.get('current_rating'):
            keywords.append(f"{visible_specs['current_rating']} current rating")
        if visible_specs.get('pole_count'):
            keywords.append(f"{visible_specs['pole_count']}-pole")

        if keywords:
            parts.append(f"SEARCH KEYWORDS: {', '.join(keywords)}")

        return "\n".join(parts)
