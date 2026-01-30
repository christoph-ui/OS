"""
Classification Prompts for LLM-based document classification
"""

CLASSIFICATION_PROMPT = """Analyze the following document and classify it into ONE of these categories:

**Categories:**
- **tax**: Tax documents, accounting, financial statements, DATEV exports, tax returns
- **legal**: Contracts, legal agreements, compliance documents, invoices, terms & conditions
- **products**: Product catalogs, specifications, ETIM/ECLASS data, inventory, materials
- **hr**: HR documents, employee records, applications, payroll, training records
- **general**: Everything else that doesn't fit the above categories

**Document Information:**
Filename: {filename}
Sample Content (first 1000 characters):
```
{content_sample}
```

**Instructions:**
1. Consider the filename and content
2. Look for German business terminology
3. Choose the SINGLE most appropriate category
4. Be concise

Output ONLY the category name in lowercase (e.g., "tax", "legal", "products", "hr", "general").
"""


BATCH_CLASSIFICATION_PROMPT = """Classify the following {count} documents into categories.

**Categories:**
- tax: Tax/accounting documents
- legal: Contracts and legal documents
- products: Product catalogs and specifications
- hr: Human resources documents
- general: Other documents

**Documents:**
{documents_list}

For each document, output a line with: filename|category

Example:
jahresabschluss_2023.pdf|tax
arbeitsvertrag_mueller.docx|hr
produktkatalog.xlsx|products

Output:
"""


def build_classification_prompt(filename: str, content_sample: str) -> str:
    """
    Build classification prompt for a single document.

    Args:
        filename: Name of the file
        content_sample: Sample of the document content (first ~1000 chars)

    Returns:
        Formatted prompt
    """
    # Truncate content sample
    if len(content_sample) > 1000:
        content_sample = content_sample[:1000] + "\n...[truncated]"

    return CLASSIFICATION_PROMPT.format(
        filename=filename,
        content_sample=content_sample
    )


def build_batch_classification_prompt(documents: list[tuple[str, str]]) -> str:
    """
    Build batch classification prompt for multiple documents.

    Args:
        documents: List of (filename, content_sample) tuples

    Returns:
        Formatted prompt
    """
    docs_text = []
    for i, (filename, sample) in enumerate(documents, 1):
        # Truncate each sample
        if len(sample) > 200:
            sample = sample[:200] + "..."

        docs_text.append(f"{i}. {filename}\n   {sample}\n")

    return BATCH_CLASSIFICATION_PROMPT.format(
        count=len(documents),
        documents_list="\n".join(docs_text)
    )
