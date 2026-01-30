"""
Pre-built Workflow Templates
Standard workflows that customers can subscribe to and run immediately
"""

from typing import Dict, Any, Optional, List


# =============================================================================
# E-COMMERCE WORKFLOWS
# =============================================================================

PRODUCT_SYNDICATION_WORKFLOW = {
    "name": "product-syndication",
    "display_name": "Product Syndication Workflow",
    "description": "Extract products from PIM → Classify with ETIM → Enrich descriptions → Syndicate to channels",
    "category": "ecommerce",
    "subcategory": "syndication",
    "tags": ["product", "automation", "multichannel"],
    "icon": "🛒",
    "icon_color": "blue",
    "complexity_level": "moderate",
    "estimated_duration_minutes": 15,
    "required_mcps": ["pim", "etim", "channel"],
    "pricing_model": "subscription",
    "price_per_month_cents": 9900,  # €99/month
    "definition": {
        "nodes": [
            {
                "id": "extract_products",
                "mcp": "pim",
                "action": "extract_products",
                "config": {
                    "filters": {"status": "active"},
                    "limit": 1000
                }
            },
            {
                "id": "classify",
                "mcp": "etim",
                "action": "classify_products",
                "config": {
                    "confidence_threshold": 0.8
                }
            },
            {
                "id": "enrich",
                "mcp": "llm",
                "action": "generate_descriptions",
                "config": {
                    "tone": "professional",
                    "length": "medium"
                }
            },
            {
                "id": "syndicate",
                "mcp": "channel",
                "action": "publish_to_channels",
                "config": {
                    "channels": ["amazon", "google_shopping", "ebay"]
                }
            }
        ],
        "edges": [
            {"from": "extract_products", "to": "classify"},
            {"from": "classify", "to": "enrich", "condition": "success"},
            {"from": "enrich", "to": "syndicate", "condition": "success"}
        ],
        "entry_point": "extract_products",
        "error_handlers": [
            {"step": "*", "action": "retry", "max_attempts": 3}
        ]
    }
}


# =============================================================================
# FINANCE & COMPLIANCE WORKFLOWS
# =============================================================================

TAX_COMPLIANCE_WORKFLOW = {
    "name": "tax-compliance",
    "display_name": "Automated Tax Compliance",
    "description": "Extract financials from ERP → Calculate tax liability → Validate compliance → Generate reports",
    "category": "finance",
    "subcategory": "tax",
    "tags": ["tax", "compliance", "automation", "german"],
    "icon": "💶",
    "icon_color": "green",
    "complexity_level": "advanced",
    "estimated_duration_minutes": 30,
    "required_mcps": ["erp", "tax", "compliance"],
    "pricing_model": "subscription",
    "price_per_month_cents": 29900,  # €299/month
    "definition": {
        "nodes": [
            {
                "id": "extract_financials",
                "mcp": "erp",
                "action": "extract_financial_data",
                "config": {
                    "accounts": ["revenue", "expenses", "vat"],
                    "period": "current_quarter"
                }
            },
            {
                "id": "calculate_tax",
                "mcp": "tax",
                "action": "calculate_liability",
                "config": {
                    "country": "DE",
                    "tax_year": "current"
                }
            },
            {
                "id": "validate_compliance",
                "mcp": "compliance",
                "action": "validate_tax_filing",
                "config": {
                    "jurisdiction": "germany"
                }
            },
            {
                "id": "generate_reports",
                "mcp": "tax",
                "action": "generate_filings",
                "config": {
                    "format": "elster",  # German tax format
                    "include_receipts": True
                }
            }
        ],
        "edges": [
            {"from": "extract_financials", "to": "calculate_tax"},
            {"from": "calculate_tax", "to": "validate_compliance", "condition": "success"},
            {"from": "validate_compliance", "to": "generate_reports", "condition": "success"}
        ],
        "entry_point": "extract_financials"
    }
}


# =============================================================================
# MARKETING WORKFLOWS
# =============================================================================

CONTENT_PUBLISHING_WORKFLOW = {
    "name": "content-publishing",
    "display_name": "Multi-Channel Content Publishing",
    "description": "Extract assets from DAM → Optimize for SEO → Generate variations → Publish to channels",
    "category": "marketing",
    "subcategory": "content",
    "tags": ["marketing", "seo", "content", "automation"],
    "icon": "📢",
    "icon_color": "purple",
    "complexity_level": "simple",
    "estimated_duration_minutes": 10,
    "required_mcps": ["dam", "web"],
    "pricing_model": "usage_based",
    "price_per_execution_cents": 99,  # €0.99/run
    "definition": {
        "nodes": [
            {
                "id": "get_assets",
                "mcp": "dam",
                "action": "get_marketing_assets",
                "config": {
                    "campaign": "current"
                }
            },
            {
                "id": "seo_optimize",
                "mcp": "llm",
                "action": "seo_optimization",
                "config": {
                    "keywords": ["product", "buy", "best"],
                    "target_length": 300
                }
            },
            {
                "id": "generate_variations",
                "mcp": "llm",
                "action": "generate_content_variations",
                "config": {
                    "variations": 3,
                    "platforms": ["web", "social", "email"]
                }
            },
            {
                "id": "publish",
                "mcp": "web",
                "action": "publish_content",
                "config": {
                    "platforms": ["website", "facebook", "linkedin"]
                }
            }
        ],
        "edges": [
            {"from": "get_assets", "to": "seo_optimize"},
            {"from": "seo_optimize", "to": "generate_variations", "condition": "success"},
            {"from": "generate_variations", "to": "publish", "condition": "success"}
        ],
        "entry_point": "get_assets"
    }
}


# =============================================================================
# DATA QUALITY WORKFLOWS
# =============================================================================

DATA_QUALITY_WORKFLOW = {
    "name": "data-quality-check",
    "display_name": "Data Quality & Enrichment",
    "description": "Extract data → Validate quality → Enrich missing fields → Deduplicate → Update source",
    "category": "data",
    "subcategory": "quality",
    "tags": ["data", "quality", "cleansing", "automation"],
    "icon": "🔍",
    "icon_color": "orange",
    "complexity_level": "moderate",
    "estimated_duration_minutes": 20,
    "required_mcps": ["pim", "dam"],
    "pricing_model": "free",  # Free workflow (attracts customers)
    "definition": {
        "nodes": [
            {
                "id": "extract_data",
                "mcp": "pim",
                "action": "extract_all_products",
                "config": {}
            },
            {
                "id": "validate",
                "mcp": "llm",
                "action": "validate_data_quality",
                "config": {
                    "rules": ["required_fields", "valid_formats", "consistency"]
                }
            },
            {
                "id": "enrich",
                "mcp": "llm",
                "action": "enrich_missing_data",
                "config": {
                    "fields": ["description", "category", "tags"]
                }
            },
            {
                "id": "deduplicate",
                "mcp": "llm",
                "action": "detect_duplicates",
                "config": {
                    "similarity_threshold": 0.9
                }
            },
            {
                "id": "update_source",
                "mcp": "pim",
                "action": "update_products",
                "config": {
                    "batch_size": 100
                }
            }
        ],
        "edges": [
            {"from": "extract_data", "to": "validate"},
            {"from": "validate", "to": "enrich", "condition": "success"},
            {"from": "enrich", "to": "deduplicate"},
            {"from": "deduplicate", "to": "update_source"}
        ],
        "entry_point": "extract_data"
    }
}


# =============================================================================
# TEMPLATE REGISTRY
# =============================================================================

# All built-in workflow templates
BUILT_IN_WORKFLOWS = [
    PRODUCT_SYNDICATION_WORKFLOW,
    TAX_COMPLIANCE_WORKFLOW,
    CONTENT_PUBLISHING_WORKFLOW,
    DATA_QUALITY_WORKFLOW
]


def get_workflow_template(name: str) -> Optional[Dict[str, Any]]:
    """
    Get a workflow template by name

    Args:
        name: Workflow name

    Returns:
        Workflow template dict or None
    """
    for workflow in BUILT_IN_WORKFLOWS:
        if workflow["name"] == name:
            return workflow
    return None


def list_workflow_templates() -> List[Dict[str, Any]]:
    """
    List all available workflow templates

    Returns:
        List of workflow templates
    """
    return BUILT_IN_WORKFLOWS.copy()
