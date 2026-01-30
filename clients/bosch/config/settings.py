"""
Bosch Client Configuration

Database, API keys, and processing settings specific to Bosch Thermotechnik
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class BoschConfig:
    """Bosch-specific configuration"""

    # Client Identity
    client_id: str = "bosch-thermotechnik"
    client_name: str = "Bosch Thermotechnik GmbH"
    industry: str = "Manufacturing/HVAC"

    # Database Configuration
    db_schema: str = "bosch_products"
    product_count: int = 23138
    embedding_dimension: int = 384

    # AI/LLM Configuration
    openai_api_key: Optional[str] = os.getenv("BOSCH_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    tavily_api_key: Optional[str] = os.getenv("BOSCH_TAVILY_API_KEY") or os.getenv("TAVILY_API_KEY")
    anthropic_api_key: Optional[str] = os.getenv("BOSCH_ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

    # Models
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    enrichment_model: str = "gpt-4-turbo-preview"
    vision_model: str = "Qwen/Qwen2-VL-72B-Instruct"

    # Classification Standards
    eclass_version: str = "15.0"
    etim_version: str = "10.0"

    # Manufacturer Details
    manufacturer_name: str = "Bosch Thermotechnik GmbH"
    manufacturer_gln: str = "4260179470004"
    manufacturer_uri: str = "https://www.bosch-thermotechnology.com"
    brand: str = "Bosch"

    # Data Quality Standards
    allow_mock_data: bool = False  # MANDATORY: No mock data policy
    min_quality_score: float = 4.0  # 0-5 scale
    min_completeness: float = 0.90  # 90% field completeness

    # Processing Settings
    batch_size: int = 32
    max_workers: int = 4
    enable_multimodal: bool = True
    enable_graph: bool = True

    # Lakehouse Paths
    delta_path: str = "lakehouse/clients/bosch/delta"
    vector_path: str = "lakehouse/clients/bosch/vector"
    graph_path: str = "lakehouse/clients/bosch/graph"

    # MCP Settings
    mcp_name: str = "bosch-product-expert"
    mcp_description: str = "Bosch Thermotechnik product catalog expert with ECLASS/ETIM support"
    mcp_version: str = "1.0.0"

    def validate(self) -> bool:
        """Validate configuration"""
        errors = []

        if not self.openai_api_key:
            errors.append("OpenAI API key required for enrichment pipeline")

        if not self.tavily_api_key:
            errors.append("Tavily API key required for research")

        if self.allow_mock_data:
            errors.append("CRITICAL: Mock data is not allowed per Bosch quality standards")

        if errors:
            for error in errors:
                print(f"❌ Configuration Error: {error}")
            return False

        return True


# Global config instance
config = BoschConfig()
