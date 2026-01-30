"""
Document Classifier - Determines which MCP should handle a document

Two-stage classification:
1. Rule-based (fast, pattern matching on path/filename)
2. LLM-based (for uncertain cases, uses content)
"""

import asyncio
from pathlib import Path
from typing import Optional
import logging
import httpx

from .rules import RuleBasedClassifier
from .prompts import build_classification_prompt

logger = logging.getLogger(__name__)


class DocumentClassifier:
    """
    Classifies documents to determine target MCP.

    Strategy:
    1. Try rule-based classification (fast, free)
    2. If uncertain, use Claude classification (accurate, costs tokens)
    3. Fall back to 'general' if all else fails
    """

    MCP_CATEGORIES = ['tax', 'legal', 'products', 'hr', 'correspondence', 'general']

    def __init__(
        self,
        vllm_url: str = "http://localhost:8001",
        confidence_threshold: float = 0.6,
        claude_api_key: Optional[str] = None
    ):
        """
        Args:
            vllm_url: URL of vLLM inference server (fallback)
            confidence_threshold: Minimum confidence for rule-based classification
            claude_api_key: Anthropic API key for Claude classification
        """
        self.vllm_url = vllm_url
        self.confidence_threshold = confidence_threshold
        self.rule_classifier = RuleBasedClassifier()
        self._client = httpx.AsyncClient(timeout=30.0)

        # Initialize Claude client if API key provided
        self.claude_client = None
        if claude_api_key:
            import anthropic
            self.claude_client = anthropic.Anthropic(api_key=claude_api_key)
            logger.info("Claude classifier initialized")

    async def classify(
        self,
        file_path: Path,
        content_sample: Optional[str] = None,
        assigned_mcp: Optional[str] = None
    ) -> str:
        """
        Classify a document using Claude-first strategy.

        Args:
            file_path: Path to the document
            content_sample: Optional text sample for LLM classification
            assigned_mcp: Optional pre-assigned MCP (from user)

        Returns:
            MCP category: 'tax', 'legal', 'products', 'hr', 'correspondence', or 'general'
        """
        # If user pre-assigned, use that
        if assigned_mcp and assigned_mcp in self.MCP_CATEGORIES:
            logger.debug(f"Using pre-assigned MCP for {file_path.name}: {assigned_mcp}")
            return assigned_mcp

        # CLAUDE-FIRST: Use AI classification if we have content and Claude available
        if content_sample and self.claude_client:
            logger.debug(f"🤖 Using Claude to classify: {file_path.name}")
            category = await self._llm_classify(file_path.name, content_sample)
            if category:
                return category

        # Fallback to rule-based classification
        category, confidence = self.rule_classifier.classify_with_confidence(file_path)

        if category and confidence >= self.confidence_threshold:
            logger.debug(
                f"Rule-based classification: {file_path.name} → {category} "
                f"(confidence: {confidence:.2f})"
            )
            return category

        # Final fallback to general
        logger.debug(f"Defaulting to 'general' for {file_path.name}")
        return 'general'

    async def _llm_classify(self, filename: str, content: str) -> Optional[str]:
        """
        Use Claude or vLLM to classify document based on content.

        Args:
            filename: Name of the file
            content: Text content sample

        Returns:
            Category name, or None if classification fails
        """
        # Try Claude first if available (better accuracy)
        if self.claude_client:
            return await self._claude_classify(filename, content)

        # Fall back to vLLM
        try:
            # Truncate content for classification
            sample = content[:1500]  # First 1.5K chars

            prompt = build_classification_prompt(filename, sample)

            # Call vLLM
            response = await self._client.post(
                f"{self.vllm_url}/v1/completions",
                json={
                    "prompt": prompt,
                    "max_tokens": 20,
                    "temperature": 0.0,  # Deterministic
                    "stop": ["\n"]  # Stop at first newline
                }
            )
            response.raise_for_status()

            result = response.json()
            classification = result["choices"][0]["text"].strip().lower()

            # Validate result
            if classification in self.MCP_CATEGORIES:
                logger.debug(f"vLLM classification: {filename} → {classification}")
                return classification

            logger.warning(f"Invalid vLLM classification result: {classification}")
            return None

        except httpx.HTTPError as e:
            logger.error(f"vLLM classification HTTP error: {e}")
            return None
        except Exception as e:
            logger.error(f"vLLM classification failed: {e}")
            return None

    async def _claude_classify(self, filename: str, content: str) -> Optional[str]:
        """
        Use Claude to classify document based on content with enhanced metadata extraction.

        Args:
            filename: Name of the file
            content: Text content sample

        Returns:
            Category name, or None if classification fails
        """
        try:
            sample = content[:3000]  # First 3K chars for better context

            prompt = f"""Analyze this business document and provide classification + metadata.

**Document:**
Filename: {filename}
Content (first 3000 chars):
```
{sample}
```

**Task:** Classify and extract key information.

**Categories:** {', '.join(self.MCP_CATEGORIES)}

**Output (JSON only):**
{{
  "category": "tax|legal|products|hr|correspondence|general",
  "sub_categories": ["specific", "types"],
  "entities": {{
    "companies": ["Company Name GmbH"],
    "dates": ["2024-Q4", "2024-12-31"],
    "amounts": ["€125,000"],
    "product_codes": ["SKU-123"],
    "people": ["Max Müller"]
  }},
  "confidence": "high|medium|low",
  "summary": "One-sentence description"
}}

**Important:** Respond with ONLY valid JSON, no markdown, no explanation."""

            response = self.claude_client.messages.create(
                model="claude-haiku-3-5-20250514",  # Fast and cheap for classification
                max_tokens=500,  # More tokens for JSON response
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse JSON response
            import json
            response_text = response.content[0].text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            try:
                metadata = json.loads(response_text)
                category = metadata.get("category", "general").lower()

                if category in self.MCP_CATEGORIES:
                    logger.info(f"Claude classification: {filename} → {category} (confidence: {metadata.get('confidence', 'unknown')})")
                    logger.debug(f"  Sub-categories: {metadata.get('sub_categories', [])}")
                    logger.debug(f"  Summary: {metadata.get('summary', '')}")

                    # Store metadata for later use (could save to database)
                    # For now, just return the category
                    return category

                logger.warning(f"Invalid category from Claude: {category}")
                return None

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Claude JSON response: {e}")
                logger.debug(f"Response was: {response_text[:200]}")
                # Fallback: try to extract category from raw text
                for cat in self.MCP_CATEGORIES:
                    if cat in response_text.lower():
                        return cat
            return None

        except Exception as e:
            logger.error(f"Claude classification failed: {e}")
            return None

    async def classify_batch(
        self,
        documents: list[tuple[Path, Optional[str]]]
    ) -> dict[Path, str]:
        """
        Classify multiple documents.

        Args:
            documents: List of (file_path, content_sample) tuples

        Returns:
            Dictionary mapping file path to category
        """
        classifications = {}

        # Try rule-based for all first
        uncertain_docs = []

        for file_path, content in documents:
            category, confidence = self.rule_classifier.classify_with_confidence(
                file_path
            )

            if category and confidence >= self.confidence_threshold:
                classifications[file_path] = category
            else:
                uncertain_docs.append((file_path, content))

        # For uncertain docs with content, use LLM
        if uncertain_docs:
            logger.info(
                f"Using LLM classification for {len(uncertain_docs)} uncertain documents"
            )

            for file_path, content in uncertain_docs:
                if content:
                    category = await self._llm_classify(file_path.name, content)
                    classifications[file_path] = category or 'general'
                else:
                    classifications[file_path] = 'general'

        return classifications

    def get_category_description(self, category: str) -> str:
        """Get human-readable description of a category"""
        descriptions = {
            'tax': 'Tax & Accounting - DATEV exports, financial statements, tax returns',
            'legal': 'Legal & Contracts - Agreements, compliance, invoices',
            'products': 'Products & Catalog - ETIM/ECLASS, specifications, inventory',
            'hr': 'Human Resources - Employee records, payroll, applications',
            'correspondence': 'Correspondence - Emails, letters, communications',
            'general': 'General Documents - Uncategorized documents'
        }
        return descriptions.get(category, category)

    async def close(self):
        """Close HTTP client"""
        await self._client.aclose()
