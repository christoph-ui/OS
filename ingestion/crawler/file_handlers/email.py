"""
Email Handler - Extract text from email files (.eml, .msg)
"""

import asyncio
import email
from email import policy
from pathlib import Path
from typing import Optional
import logging

from .base import BaseHandler

logger = logging.getLogger(__name__)


class EmailHandler(BaseHandler):
    """
    Extract content from email files.

    Handles .eml (standard email format) files.
    Extracts headers, body, and basic metadata.
    """

    @classmethod
    def supported_extensions(cls) -> set[str]:
        return {'.eml'}

    async def extract(self, path: Path) -> Optional[str]:
        """Extract text from email file"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self._extract_sync, path
        )

    def _extract_sync(self, path: Path) -> Optional[str]:
        """Synchronous extraction"""
        try:
            # Read email file
            with open(path, 'rb') as f:
                msg = email.message_from_binary_file(f, policy=policy.default)

            parts = []

            # Extract headers
            parts.append("=== Email Headers ===")
            parts.append(f"From: {msg.get('From', 'N/A')}")
            parts.append(f"To: {msg.get('To', 'N/A')}")
            parts.append(f"Subject: {msg.get('Subject', 'N/A')}")
            parts.append(f"Date: {msg.get('Date', 'N/A')}")
            parts.append("")

            # Extract body
            body = self._get_email_body(msg)
            if body:
                parts.append("=== Email Body ===")
                parts.append(body)

            full_text = "\n".join(parts)

            if not full_text.strip():
                logger.info(f"No content in email: {path}")
                return None

            return full_text

        except Exception as e:
            logger.error(f"Email extraction failed for {path}: {e}")
            return None

    def _get_email_body(self, msg) -> str:
        """Extract body text from email message"""
        body_parts = []

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()

                # Get text parts
                if content_type == 'text/plain':
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or 'utf-8'
                            text = payload.decode(charset, errors='replace')
                            body_parts.append(text)
                    except Exception as e:
                        logger.warning(f"Failed to decode email part: {e}")

        else:
            # Single part email
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or 'utf-8'
                    text = payload.decode(charset, errors='replace')
                    body_parts.append(text)
            except Exception as e:
                logger.warning(f"Failed to decode email body: {e}")

        return "\n\n".join(body_parts)


class MSGHandler(BaseHandler):
    """
    Handler for Outlook .msg files.

    Requires extract-msg library or conversion.
    """

    @classmethod
    def supported_extensions(cls) -> set[str]:
        return {'.msg'}

    async def extract(self, path: Path) -> Optional[str]:
        """Extract text from .msg file"""
        # Try using extract-msg library
        try:
            import extract_msg
            return await self._extract_with_lib(path)
        except ImportError:
            logger.warning("extract-msg library not available for .msg files")
            logger.info("Install with: pip install extract-msg")
            return None

    async def _extract_with_lib(self, path: Path) -> Optional[str]:
        """Extract using extract-msg library"""
        import extract_msg

        return await asyncio.get_event_loop().run_in_executor(
            None, self._extract_msg_sync, path
        )

    def _extract_msg_sync(self, path: Path) -> Optional[str]:
        """Synchronous MSG extraction"""
        try:
            import extract_msg

            msg = extract_msg.Message(str(path))

            parts = []
            parts.append("=== Email Headers ===")
            parts.append(f"From: {msg.sender or 'N/A'}")
            parts.append(f"To: {msg.to or 'N/A'}")
            parts.append(f"Subject: {msg.subject or 'N/A'}")
            parts.append(f"Date: {msg.date or 'N/A'}")
            parts.append("")

            if msg.body:
                parts.append("=== Email Body ===")
                parts.append(msg.body)

            msg.close()

            full_text = "\n".join(parts)
            return full_text if full_text.strip() else None

        except Exception as e:
            logger.error(f"MSG extraction failed for {path}: {e}")
            return None
