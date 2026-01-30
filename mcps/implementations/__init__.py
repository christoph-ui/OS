"""
DEPRECATED: MCP Implementations

This module is deprecated. Use mcps.core instead.

Migration:
    # Old (deprecated)
    from mcps.implementations.ctax import CTAXMCP

    # New
    from mcps.core.ctax import CTAXMCP
    # or
    from mcps import get_mcp
    ctax = get_mcp("ctax")
"""

import warnings

# Redirect imports for backwards compatibility
from mcps.core.ctax import CTAXMCP
from mcps.core.law import LAWMCP
from mcps.core.tender import TenderEngineMCP

warnings.warn(
    "mcps.implementations is deprecated. Use mcps.core instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ["CTAXMCP", "LAWMCP", "TenderEngineMCP"]
