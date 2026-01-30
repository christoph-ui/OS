"""
Claude-powered chat for Platform

Uses Claude Sonnet 4.5 for chat until vLLM is fully integrated.
"""

import logging
import os
from typing import List, Dict, Any, Optional
import anthropic

logger = logging.getLogger(__name__)


class ClaudeChat:
    """
    Claude Sonnet 4.5 chat integration.

    Provides intelligent chat with RAG context from customer lakehouse.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude client.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"

    async def chat(
        self,
        message: str,
        context_documents: List[Dict[str, Any]] = None,
        customer_id: str = None,
        system_prompt: str = None
    ) -> Dict[str, Any]:
        """
        Send a chat message with optional RAG context.

        Args:
            message: User's question
            context_documents: Relevant documents from lakehouse
            customer_id: Customer ID (for personalization)
            system_prompt: Optional custom system prompt

        Returns:
            Dict with answer, confidence, sources
        """
        # Build RAG context from documents
        rag_context = ""
        sources = []

        if context_documents:
            rag_context = "\n\n<documents>\n"
            for i, doc in enumerate(context_documents[:5], 1):
                filename = doc.get("filename", f"Document {i}")
                text = doc.get("text", doc.get("snippet", ""))[:2000]  # Limit per doc

                rag_context += f"\n<document id=\"{i}\" filename=\"{filename}\">\n"
                rag_context += text
                rag_context += f"\n</document>\n"

                sources.append(filename)

            rag_context += "\n</documents>\n"

        # Default system prompt (Product Manager optimized)
        if not system_prompt:
            system_prompt = f"""You are a strategic AI assistant for {customer_id or 'the company'}'s product management team.

**Response Format Rules**:

1. **Always start with a brief summary** (1-2 sentences) under "## Overview" or "## Executive Summary"

2. **Use professional markdown structure**:
   - Level 2 headings (##) for main sections
   - Level 3 headings (###) for subsections
   - Bold (**) for emphasis and labels
   - Bullet points (-) for lists
   - Tables for specifications/data
   - Code blocks for technical data

3. **Organize information logically**:
   - Start with high-level summary
   - Then key facts/findings
   - Then detailed technical information
   - End with context or recommendations

4. **MANDATORY: Always end with "## Related Questions You Might Ask"**:
   - List 3-5 specific, relevant follow-up questions
   - Make them actionable and data-driven
   - Format as bullet points starting with "-"

5. **Citation style**:
   - Reference documents explicitly: "[Document 1: filename.xml]"
   - Be precise with numbers, product codes, standards

**Example of good structure**:

## Overview
[1-2 sentence answer to the main question]

## [Relevant Section Title]
**[Key Point 1]**: [Data from documents]
**[Key Point 2]**: [Another fact]

### [Subsection if needed]
[Details with citations]

## [Another Section]
[More organized information]

## Related Questions You Might Ask
- [Specific question 1 they could ask next]
- [Specific question 2 related to this topic]
- [Specific question 3 for deeper analysis]

**Your goal**: Provide clear, structured, professional responses that are easy to scan and act upon. Think like a senior product strategist, not a generic chatbot."""

        # Build user message with RAG context
        user_message = message
        if rag_context:
            user_message = f"""{rag_context}

Question: {message}

Answer the question using professional markdown formatting.

MANDATORY: Your response MUST end with a "## Related Questions You Might Ask" section containing 3-5 specific follow-up questions.

Format:
## Related Questions You Might Ask
- [Question 1 related to this topic]
- [Question 2 for deeper analysis]
- [Question 3 exploring related area]

Provide your answer now:"""

        try:
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,  # Lower temperature for factual accuracy
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )

            # Extract answer
            answer = response.content[0].text

            # Parse structured response (extract suggested questions if present)
            suggested_questions = self._extract_suggested_questions(answer)

            # Fallback: Generate questions if Claude didn't include them
            if not suggested_questions and context_documents:
                suggested_questions = self._generate_fallback_questions(
                    message, answer, context_documents
                )

            # Estimate confidence based on whether we had context
            confidence = 0.9 if context_documents else 0.7

            return {
                "answer": answer,
                "confidence": confidence,
                "sources": sources,
                "suggested_questions": suggested_questions,
                "model": self.model,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                },
                "metadata": {
                    "customer_id": customer_id,
                    "documents_used": len(context_documents) if context_documents else 0,
                    "response_type": self._detect_response_type(answer)
                }
            }

        except Exception as e:
            logger.error(f"Claude API error: {e}", exc_info=True)
            return {
                "answer": f"Sorry, I encountered an error: {str(e)}",
                "confidence": 0.0,
                "sources": [],
                "model": self.model,
                "error": str(e)
            }

    async def chat_streaming(
        self,
        message: str,
        context_documents: List[Dict[str, Any]] = None,
        customer_id: str = None,
        system_prompt: str = None
    ):
        """
        Stream chat response (for WebSocket).

        Yields text chunks as they arrive from Claude.
        """
        # Build context (same as chat())
        rag_context = ""
        sources = []

        if context_documents:
            rag_context = "\n\n<documents>\n"
            for i, doc in enumerate(context_documents[:5], 1):
                filename = doc.get("filename", f"Document {i}")
                text = doc.get("text", doc.get("snippet", ""))[:2000]

                rag_context += f"\n<document id=\"{i}\" filename=\"{filename}\">\n{text}\n</document>\n"
                sources.append(filename)

            rag_context += "\n</documents>\n"

        if not system_prompt:
            system_prompt = f"""You are an AI assistant for {customer_id or 'a customer'}'s business data.

Answer questions based on the provided documents. Be precise and cite sources."""

        user_message = message
        if rag_context:
            user_message = f"{rag_context}\n\n<question>\n{message}\n</question>\n\nAnswer:"

        try:
            # Stream from Claude
            with self.client.messages.stream(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            ) as stream:
                for text in stream.text_stream:
                    yield text

        except Exception as e:
            logger.error(f"Claude streaming error: {e}", exc_info=True)
            yield f"\n\nError: {str(e)}"

    def _extract_suggested_questions(self, answer: str) -> List[str]:
        """
        Extract suggested questions from the answer.

        Looks for section like "## Related Questions You Might Ask"
        """
        import re

        # Pattern to match suggested questions section
        pattern = r'## Related Questions You Might Ask\s*\n((?:[-•]\s*.+\n?)+)'
        match = re.search(pattern, answer, re.MULTILINE)

        if match:
            questions_text = match.group(1)
            # Extract each question (lines starting with - or •)
            questions = re.findall(r'[-•]\s*(.+)', questions_text)
            return [q.strip() for q in questions if q.strip()]

        return []

    def _detect_response_type(self, answer: str) -> str:
        """
        Detect the type of response based on content.

        Returns: 'analytical', 'informational', 'comparative', 'simple'
        """
        answer_lower = answer.lower()

        # Check for analytical markers
        if '## executive summary' in answer_lower or '## key findings' in answer_lower:
            return 'analytical'

        # Check for comparative markers
        if 'compared to' in answer_lower or 'versus' in answer_lower or 'vs' in answer_lower:
            return 'comparative'

        # Check for simple/short responses
        if len(answer) < 500 and '\n#' not in answer:
            return 'simple'

        return 'informational'

    def _generate_fallback_questions(
        self,
        original_question: str,
        answer: str,
        context_documents: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generate intelligent follow-up questions when Claude doesn't provide them.

        Uses quick heuristics based on question type and answer content.
        """
        questions = []
        question_lower = original_question.lower()
        answer_lower = answer.lower()

        # Product-related questions
        if any(word in question_lower for word in ['product', 'specification', 'circuit breaker', 'frcdm', 'model']):
            if 'frcdm' in answer_lower or 'circuit breaker' in answer_lower:
                questions.extend([
                    "What are the physical dimensions and weight of this circuit breaker?",
                    "What compliance standards and certifications does it have?",
                    "Are there other models in the FRCDM product line?",
                ])
            else:
                questions.extend([
                    "Can you show me detailed technical specifications?",
                    "What product families or series are available?",
                    "How do these products compare to competitors?",
                ])

        # Standards/compliance questions
        elif any(word in question_lower for word in ['standard', 'eclass', 'etim', 'classification', 'compliance']):
            questions.extend([
                "What ECLASS classification codes are used for our products?",
                "Explain the difference between ECLASS and ETIM standards",
                "Which products comply with IEC/EN 61008 standards?",
            ])

        # Data/catalog questions
        elif any(word in question_lower for word in ['catalog', 'bmecat', 'pdh', 'data']):
            questions.extend([
                "What product data formats do we use (BMEcat, ETIM xChange)?",
                "How many products are in our Product Data Hub?",
                "What attributes do we track for each product?",
            ])

        # Generic fallback
        else:
            # Extract key terms from the answer for context-aware questions
            if 'eaton' in answer_lower:
                questions.append("What other Eaton products are in our catalog?")
            if any(num in answer for num in ['40', '440', '300']):
                questions.append("Can you compare specifications across different product models?")
            questions.append("What documentation or guidelines are available for this topic?")

        # Return up to 5 questions
        return questions[:5]


# Global instance
_claude_chat: Optional[ClaudeChat] = None


def get_claude_chat() -> ClaudeChat:
    """Get global Claude chat instance"""
    global _claude_chat
    if _claude_chat is None:
        _claude_chat = ClaudeChat()
    return _claude_chat
