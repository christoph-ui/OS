# Contributing to 0711 Intelligence Platform

Thank you for your interest in contributing to the 0711 Intelligence Platform! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and professional
- Focus on constructive feedback
- Help create a welcoming environment

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker + Docker Compose
- Git

### Setup Steps

```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/0711-OS.git
cd 0711-OS

# 2. Set up environment
cp .env.example .env
# Add your API keys to .env

# 3. Install dependencies
pip install -r requirements.txt
cd console/frontend && npm install && cd ../..
cd apps/website && npm install && cd ../..

# 4. Start infrastructure
docker compose up -d postgres redis minio

# 5. Run migrations
alembic upgrade head

# 6. Verify setup
pytest tests/ -v
```

## Code Style

### Python

- **Formatter**: Black with 100 character line length
- **Linter**: Ruff
- **Type hints**: Required for public APIs
- **Docstrings**: Google style for all public functions

```bash
# Format code
black . --line-length 100

# Lint code
ruff check --fix .

# Type check
mypy .
```

### TypeScript

- **Formatter**: Prettier
- **Linter**: ESLint
- **Style**: Functional components with hooks

```bash
cd console/frontend
npm run lint
npm run format
```

### Naming Conventions

- **Python modules**: `snake_case.py`
- **Python classes**: `PascalCase`
- **Python functions**: `snake_case()`
- **Constants**: `UPPER_SNAKE_CASE`
- **React components**: `PascalCase.tsx`
- **React hooks**: `useCamelCase.ts`

## Git Workflow

### Branch Naming

- **Features**: `feature/description` (e.g., `feature/add-pdf-handler`)
- **Bug fixes**: `fix/description` (e.g., `fix/login-error`)
- **Documentation**: `docs/description` (e.g., `docs/update-readme`)
- **Refactoring**: `refactor/description`
- **Tests**: `test/description`

### Commit Messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```bash
feat(ingestion): add Claude-powered XML handler
fix(auth): resolve JWT expiration issue
docs(readme): update installation instructions
test(api): add integration tests for upload endpoint
```

### Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make your changes**
   - Write clear, focused commits
   - Add tests for new functionality
   - Update documentation as needed

3. **Verify your changes**
   ```bash
   # Run tests
   pytest tests/ -v

   # Format code
   black . && ruff check --fix .

   # Verify TypeScript (if applicable)
   cd console/frontend && npm run lint
   ```

4. **Push and create PR**
   ```bash
   git push origin feature/my-feature
   ```
   - Open a pull request on GitHub
   - Fill out the PR template
   - Link any related issues

5. **Code review**
   - Address feedback from reviewers
   - Keep the PR up to date with main branch
   - Squash commits if requested

6. **Merge**
   - PRs are merged by maintainers after approval
   - Delete your feature branch after merge

## Testing Requirements

### Required Tests

- **Unit tests**: For all new functions and classes
- **Integration tests**: For API endpoints and workflows
- **E2E tests**: For critical user flows (when applicable)

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_file_handler.py -v

# Run with coverage
pytest --cov=api --cov=ingestion --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Writing Tests

```python
# tests/unit/test_example.py
import pytest
from my_module import my_function

def test_my_function_success():
    """Test my_function with valid input"""
    result = my_function("valid input")
    assert result == "expected output"

def test_my_function_error():
    """Test my_function with invalid input"""
    with pytest.raises(ValueError):
        my_function("invalid input")
```

## Documentation

### Code Documentation

- Add docstrings to all public functions, classes, and modules
- Use Google style docstrings
- Include examples for complex functions

```python
def process_document(path: Path, customer_id: str) -> dict:
    """Process a document and extract metadata.

    Args:
        path: Path to the document file
        customer_id: ID of the customer who owns the document

    Returns:
        Dictionary containing extracted metadata:
        - filename: str
        - size: int
        - mime_type: str
        - chunks: List[str]

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If customer_id is invalid

    Example:
        >>> result = process_document(Path("doc.pdf"), "acme")
        >>> print(result["filename"])
        "doc.pdf"
    """
    pass
```

### User Documentation

- Update README.md for user-facing changes
- Add/update docs in `docs/` directory
- Include examples and code snippets

## Areas to Contribute

### High Priority

1. **File Handlers**: Add support for new file formats
2. **MCPs**: Create new domain-specific experts
3. **Tests**: Improve test coverage
4. **Documentation**: Improve docs and examples

### Good First Issues

Look for issues labeled `good-first-issue` on GitHub. These are well-scoped tasks suitable for newcomers.

### Feature Requests

- Open an issue to discuss the feature before implementing
- Explain the use case and benefits
- Get feedback from maintainers

## Adding New File Handlers

To add support for a new file format:

```python
# ingestion/crawler/file_handlers/my_format.py
from pathlib import Path
from typing import Optional
from .base import BaseFileHandler

class MyFormatHandler(BaseFileHandler):
    """Handler for .myformat files"""

    supported_extensions = [".myformat"]

    async def extract(self, path: Path) -> Optional[str]:
        """Extract text from .myformat files

        Args:
            path: Path to the file

        Returns:
            Extracted text content or None if extraction fails
        """
        try:
            # Your extraction logic here
            with open(path, 'r') as f:
                content = f.read()
            return content
        except Exception as e:
            logger.error(f"Failed to extract {path}: {e}")
            return None
```

Then register it in `__init__.py`:
```python
from .my_format import MyFormatHandler
```

## Adding New MCPs

To create a new MCP (Model Context Protocol expert):

```python
# mcps/core/my_expert.py
from mcps.sdk import BaseMCP, tool, resource

class MyExpertMCP(BaseMCP):
    """Expert for [domain description]"""

    name = "my-expert"
    description = "Specialist in [domain]"
    version = "1.0.0"

    @tool
    async def analyze_data(self, query: str) -> dict:
        """Analyze data and return insights

        Args:
            query: User query

        Returns:
            Analysis results
        """
        # Query lakehouse
        docs = await self.lakehouse.search(query)

        # Query LLM with context
        result = await self.llm.query(docs, query)

        return {"answer": result, "sources": docs}

    @resource
    async def get_reference_data(self) -> dict:
        """Get reference data for this domain"""
        return await self.lakehouse.get_table("my_domain_data")
```

Register in `mcps/registry.py`:
```python
from mcps.core.my_expert import MyExpertMCP
```

## Security

### Reporting Security Issues

**DO NOT open public issues for security vulnerabilities.**

Email: security@0711.io

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if available)

### Security Best Practices

- Never commit secrets or credentials
- Use `.env` for all configuration
- Validate all user input
- Use parameterized queries (no SQL injection)
- Sanitize file uploads
- Follow OWASP guidelines

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bug reports**: Open a GitHub Issue
- **Security**: Email security@0711.io
- **General**: Email support@0711.io

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (Proprietary License).

---

Thank you for contributing to 0711! 🚀
