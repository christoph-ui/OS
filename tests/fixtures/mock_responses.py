"""
Mock Responses for Testing

Mock LLM responses and other external service responses.
"""

# Mock vLLM responses
MOCK_VLLM_RESPONSES = {
    "tax_query": {
        "answer": "The corporate tax rate in Germany is 15% (Körperschaftsteuer) plus 5.5% solidarity surcharge, resulting in an effective rate of approximately 15.825%.",
        "confidence": 0.95,
        "sources": ["German Tax Code § 23 KStG"]
    },
    "legal_query": {
        "answer": "The contract complies with German law (BGB) and includes all required clauses for service agreements.",
        "confidence": 0.88,
        "sources": ["BGB § 611", "Contract document section 4"]
    },
    "tender_query": {
        "answer": "This public tender requires VOB compliance and submission by March 15, 2024.",
        "confidence": 0.92,
        "sources": ["Tender document page 3", "VOB/A requirements"]
    }
}

# Mock embedding responses
MOCK_EMBEDDINGS = {
    "sample_text": [0.1] * 1024  # 1024-dim embedding vector
}

# Mock MCP info
MOCK_MCP_INFO = {
    "ctax": {
        "name": "CTAX Engine",
        "description": "German tax automation specialist",
        "version": "1.0.0",
        "tools": ["calculate_vat", "get_tax_rates", "check_compliance"],
        "resources": ["tax_laws", "rate_tables"]
    },
    "law": {
        "name": "LAW MCP",
        "description": "Legal document analysis",
        "version": "1.0.0",
        "tools": ["analyze_contract", "check_gdpr", "find_clauses"],
        "resources": ["contract_templates", "legal_databases"]
    },
    "tender": {
        "name": "TENDER MCP",
        "description": "Public tender analysis",
        "version": "1.0.0",
        "tools": ["analyze_rfp", "check_requirements", "generate_response"],
        "resources": ["vob_standards", "tender_history"]
    }
}
