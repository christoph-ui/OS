"""
Claude Handler Generator - Adaptive import script creation using Claude Sonnet 4.5

This module generates custom file handlers for unknown or proprietary file formats.
When the ingestion pipeline encounters a file it can't process with built-in handlers,
it uses Claude to analyze the file structure and generate a Python handler class.
"""

import ast
import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Optional, Tuple
import importlib.util
import re

import anthropic
import chardet

logger = logging.getLogger(__name__)


class ClaudeHandlerGenerator:
    """Generate custom file handlers using Claude Sonnet 4.5"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929"):
        """
        Initialize the handler generator.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_sample_bytes = 4000  # First 4KB for analysis

    async def generate_handler(
        self,
        file_path: Path,
        user_hint: Optional[str] = None,
        timeout: int = 60
    ) -> Tuple[str, str]:
        """
        Generate a custom file handler for an unknown file format.

        Args:
            file_path: Path to the file to analyze
            user_hint: Optional user description of the file format
            timeout: Generation timeout in seconds

        Returns:
            Tuple of (handler_code, handler_class_name)

        Raises:
            ValueError: If handler generation or validation fails
            TimeoutError: If generation takes too long
        """
        logger.info(f"Generating handler for {file_path}")

        try:
            # Analyze file structure
            analysis = await asyncio.wait_for(
                self._analyze_file_structure(file_path),
                timeout=10
            )

            # Build prompt for Claude
            prompt = self._build_handler_prompt(
                file_path=file_path,
                analysis=analysis,
                user_hint=user_hint
            )

            # Call Claude to generate handler
            handler_code = await asyncio.wait_for(
                self._call_claude(prompt),
                timeout=timeout
            )

            # Validate generated code
            if not self._validate_handler(handler_code):
                raise ValueError("Generated handler failed validation")

            # Test on sample file
            if not await self._test_handler(handler_code, file_path):
                raise ValueError("Generated handler failed test on sample file")

            # Extract class name
            handler_class = self._extract_class_name(handler_code)

            logger.info(f"Successfully generated handler: {handler_class}")
            return handler_code, handler_class

        except asyncio.TimeoutError:
            logger.error(f"Handler generation timed out for {file_path}")
            raise TimeoutError(f"Handler generation exceeded {timeout}s timeout")
        except Exception as e:
            logger.error(f"Handler generation failed: {e}")
            raise

    async def _analyze_file_structure(self, file_path: Path) -> dict:
        """
        Analyze file to understand its structure.

        Args:
            file_path: Path to file

        Returns:
            Dictionary with analysis results
        """
        try:
            # Read first N bytes
            with open(file_path, 'rb') as f:
                sample_bytes = f.read(self.max_sample_bytes)

            # Detect encoding
            encoding_result = chardet.detect(sample_bytes)
            encoding = encoding_result.get('encoding', 'utf-8')
            confidence = encoding_result.get('confidence', 0.0)

            # Try to decode
            try:
                sample_text = sample_bytes.decode(encoding, errors='replace')
            except:
                sample_text = sample_bytes.decode('utf-8', errors='replace')

            # Get file stats
            stat = file_path.stat()

            # Basic structure detection
            structure_hints = []
            if sample_text.strip().startswith('<?xml'):
                structure_hints.append("XML format")
            elif sample_text.strip().startswith('{'):
                structure_hints.append("JSON-like structure")
            elif '\t' in sample_text[:500] or ',' in sample_text[:500]:
                structure_hints.append("Delimited text (CSV/TSV)")
            elif re.search(r'<[a-zA-Z][^>]*>', sample_text):
                structure_hints.append("Markup/tagged content")

            # Check for DATEV-specific patterns (common in German accounting)
            if any(term in sample_text.lower() for term in ['datev', 'buchung', 'konto', 'soll', 'haben']):
                structure_hints.append("DATEV accounting export")

            analysis = {
                'file_name': file_path.name,
                'extension': file_path.suffix,
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'encoding': encoding,
                'encoding_confidence': confidence,
                'sample_bytes': sample_bytes[:2000],  # First 2KB
                'sample_decoded': sample_text[:2000],
                'structure_hints': structure_hints,
                'line_count_sample': len(sample_text.split('\n')),
            }

            return analysis

        except Exception as e:
            logger.error(f"File analysis failed: {e}")
            raise

    def _build_handler_prompt(
        self,
        file_path: Path,
        analysis: dict,
        user_hint: Optional[str]
    ) -> str:
        """Build prompt for Claude to generate handler"""

        structure_info = "\n".join(f"- {hint}" for hint in analysis['structure_hints'])

        prompt = f"""You are generating a Python file handler for the 0711 Platform ingestion system.

**File Information:**
- Filename: {analysis['file_name']}
- Extension: {analysis['extension']}
- Size: {analysis['size_mb']} MB
- Encoding: {analysis['encoding']} (confidence: {analysis['encoding_confidence']:.2f})

**Detected Structure:**
{structure_info if structure_info else "No specific structure detected"}

**Sample Content (first 2000 characters):**
```
{analysis['sample_decoded']}
```

{f"**User Description:** {user_hint}" if user_hint else ""}

**Task:**
Write a Python class that inherits from `BaseHandler` and implements the `extract(path: Path) -> Optional[str]` method to extract all meaningful text content from this file format.

**Requirements:**
1. Extract all meaningful text content from files in this format
2. Handle encoding issues gracefully (try detected encoding, fall back to utf-8)
3. Return None if extraction fails completely
4. Preserve document structure where possible (paragraphs, sections)
5. Include comprehensive error handling
6. Add detailed docstring explaining the file format and extraction logic
7. Handle edge cases (empty files, corrupted data)

**Base Class Definition:**
```python
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class BaseHandler:
    \"\"\"Base class for file handlers\"\"\"

    async def extract(self, path: Path) -> Optional[str]:
        \"\"\"
        Extract text content from file.

        Args:
            path: Path to file

        Returns:
            Extracted text content, or None if extraction fails
        \"\"\"
        raise NotImplementedError
```

**Example Handler (for reference):**
```python
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class CustomXMLHandler(BaseHandler):
    \"\"\"Extracts text from custom XML format with nested document structure\"\"\"

    async def extract(self, path: Path) -> Optional[str]:
        try:
            # Read and parse XML
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            tree = ET.fromstring(content)
            text_parts = []

            # Extract text from all elements
            for elem in tree.iter():
                if elem.text and elem.text.strip():
                    text_parts.append(elem.text.strip())
                if elem.tail and elem.tail.strip():
                    text_parts.append(elem.tail.strip())

            result = "\\n".join(text_parts)
            return result if result.strip() else None

        except Exception as e:
            logger.error(f"XML extraction failed for {{path}}: {{e}}")
            return None
```

**Important:**
- Import only standard library or common packages (xml, json, csv, re, etc.)
- Do not use external dependencies unless absolutely necessary
- Make the handler robust and fault-tolerant
- Return None rather than raising exceptions for extraction failures

Generate the complete handler class now. Output ONLY the Python code, no explanation or markdown formatting.
"""
        return prompt

    async def _call_claude(self, prompt: str) -> str:
        """
        Call Claude API to generate handler code.

        Args:
            prompt: Generation prompt

        Returns:
            Generated Python code
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.0,  # Deterministic for code generation
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract code from response
            content = response.content[0].text
            code = self._extract_code_block(content)

            return code

        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            raise

    def _extract_code_block(self, text: str) -> str:
        """Extract Python code from Claude's response"""
        # Try to extract from markdown code block
        code_block_pattern = r'```python\s*\n(.*?)\n```'
        match = re.search(code_block_pattern, text, re.DOTALL)

        if match:
            return match.group(1).strip()

        # Try without language specifier
        code_block_pattern = r'```\s*\n(.*?)\n```'
        match = re.search(code_block_pattern, text, re.DOTALL)

        if match:
            return match.group(1).strip()

        # Assume entire response is code
        return text.strip()

    def _validate_handler(self, code: str) -> bool:
        """
        Validate generated handler code.

        Checks:
        - Valid Python syntax
        - Contains class definition
        - Class has extract method
        - Method signature is correct

        Args:
            code: Generated code

        Returns:
            True if valid, False otherwise
        """
        try:
            # Parse AST
            tree = ast.parse(code)

            # Find class definitions
            classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            if not classes:
                logger.warning("No class definition found in generated code")
                return False

            # Check for extract method
            extract_methods = []
            for cls in classes:
                for item in cls.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if item.name == 'extract':
                            extract_methods.append(item)

            if not extract_methods:
                logger.warning("No 'extract' method found in generated handler")
                return False

            # Validate method signature (should have self, path parameters)
            method = extract_methods[0]
            if len(method.args.args) < 2:  # self + path
                logger.warning("Extract method has incorrect signature")
                return False

            return True

        except SyntaxError as e:
            logger.error(f"Generated code has syntax error: {e}")
            return False
        except Exception as e:
            logger.error(f"Code validation failed: {e}")
            return False

    def _extract_class_name(self, code: str) -> str:
        """Extract the handler class name from generated code"""
        try:
            tree = ast.parse(code)
            classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            if classes:
                return classes[0].name
            return "GeneratedHandler"
        except:
            return "GeneratedHandler"

    async def _test_handler(self, code: str, test_file: Path) -> bool:
        """
        Test generated handler on the sample file.

        Args:
            code: Generated handler code
            test_file: File to test on

        Returns:
            True if handler successfully extracts content, False otherwise
        """
        temp_module_path = None
        try:
            # Create temporary module file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False
            ) as f:
                # Add necessary imports
                full_code = f"""
from pathlib import Path
from typing import Optional
import logging
import asyncio

logger = logging.getLogger(__name__)

class BaseHandler:
    async def extract(self, path: Path) -> Optional[str]:
        raise NotImplementedError

{code}
"""
                f.write(full_code)
                temp_module_path = f.name

            # Import the module
            spec = importlib.util.spec_from_file_location("temp_handler", temp_module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find the handler class
            handler_class = None
            for item_name in dir(module):
                item = getattr(module, item_name)
                if (isinstance(item, type) and
                    hasattr(item, 'extract') and
                    item.__name__ != 'BaseHandler'):
                    handler_class = item
                    break

            if not handler_class:
                logger.warning("Could not find handler class in generated code")
                return False

            # Test extraction
            handler = handler_class()
            result = await handler.extract(test_file)

            # Validate result
            if result is None:
                logger.warning("Handler returned None")
                return False

            if not isinstance(result, str):
                logger.warning(f"Handler returned non-string: {type(result)}")
                return False

            if len(result.strip()) < 10:
                logger.warning(f"Handler extracted very little content: {len(result)} chars")
                return False

            logger.info(f"Handler test successful, extracted {len(result)} characters")
            return True

        except Exception as e:
            logger.error(f"Handler test failed: {e}")
            return False
        finally:
            # Cleanup
            if temp_module_path:
                Path(temp_module_path).unlink(missing_ok=True)


# Example usage
async def main():
    """Example usage of ClaudeHandlerGenerator"""
    import os

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        return

    generator = ClaudeHandlerGenerator(api_key=api_key)

    # Example: generate handler for a custom file
    test_file = Path("example_custom_file.dat")

    try:
        code, class_name = await generator.generate_handler(
            file_path=test_file,
            user_hint="This is a DATEV accounting export with custom format"
        )

        print(f"Generated handler class: {class_name}")
        print("\nGenerated code:")
        print("=" * 80)
        print(code)
        print("=" * 80)

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
