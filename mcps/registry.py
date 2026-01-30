"""
MCP Registry

Central registry for discovering, loading, and managing MCPs.
Separates Core MCPs (ship with platform) from Marketplace MCPs (optional).

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │  MCP Registry                                               │
    ├─────────────────────────────────────────────────────────────┤
    │                                                             │
    │  Core MCPs (always available):                              │
    │  ┌─────────┐ ┌─────────┐ ┌─────────┐                       │
    │  │  CTAX   │ │   LAW   │ │ TENDER  │                       │
    │  └─────────┘ └─────────┘ └─────────┘                       │
    │                                                             │
    │  Marketplace MCPs (one-click install):                      │
    │  ┌─────────┐ ┌─────────┐ ┌─────────┐                       │
    │  │Invoice  │ │ DATEV   │ │  ...    │                       │
    │  └─────────┘ └─────────┘ └─────────┘                       │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘

Usage:
    from mcps.registry import MCPRegistry, get_registry

    registry = get_registry()

    # List core MCPs
    core = registry.list_core()  # ["ctax", "law", "tender"]

    # Get MCP instance
    ctax = registry.get("ctax")

    # Check if core
    registry.is_core("ctax")  # True
    registry.is_core("invoice-pro")  # False
"""

import logging
from typing import Dict, List, Optional, Type
from pathlib import Path
import importlib.util

from .sdk.base import BaseMCP

logger = logging.getLogger(__name__)


# Core MCPs that ship with the platform
CORE_MCPS = ["ctax", "law", "tender", "market", "publish", "syndicate", "orchestrator"]


class MCPRegistry:
    """
    Central registry for all MCPs.

    Manages discovery, loading, and lifecycle of MCPs.
    """

    def __init__(self):
        self._mcps: Dict[str, BaseMCP] = {}
        self._mcp_classes: Dict[str, Type[BaseMCP]] = {}
        self._loaded_core = False

    def register(self, mcp: BaseMCP) -> None:
        """
        Register an MCP instance.

        Args:
            mcp: MCP instance to register
        """
        if mcp.name in self._mcps:
            logger.warning(f"MCP '{mcp.name}' already registered, replacing")

        self._mcps[mcp.name] = mcp
        logger.info(f"Registered MCP: {mcp.name} v{mcp.version}")

    def register_class(self, name: str, mcp_class: Type[BaseMCP]) -> None:
        """
        Register an MCP class for lazy instantiation.

        Args:
            name: MCP identifier
            mcp_class: MCP class (not instance)
        """
        self._mcp_classes[name] = mcp_class
        logger.debug(f"Registered MCP class: {name}")

    def get(self, mcp_id: str) -> Optional[BaseMCP]:
        """
        Get an MCP by ID.

        Args:
            mcp_id: MCP identifier (e.g., "ctax", "law")

        Returns:
            MCP instance or None if not found
        """
        # Check if already instantiated
        if mcp_id in self._mcps:
            return self._mcps[mcp_id]

        # Try lazy instantiation
        if mcp_id in self._mcp_classes:
            try:
                instance = self._mcp_classes[mcp_id]()
                self._mcps[mcp_id] = instance
                return instance
            except Exception as e:
                logger.error(f"Failed to instantiate MCP '{mcp_id}': {e}")
                return None

        # Try to load from core
        if mcp_id in CORE_MCPS and not self._loaded_core:
            self.load_core_mcps()
            return self._mcps.get(mcp_id)

        logger.warning(f"MCP '{mcp_id}' not found in registry")
        return None

    def list_all(self) -> List[str]:
        """List all registered MCP IDs"""
        all_mcps = set(self._mcps.keys()) | set(self._mcp_classes.keys())
        return sorted(list(all_mcps))

    def list_core(self) -> List[str]:
        """List core MCP IDs"""
        return CORE_MCPS.copy()

    def list_installed(self) -> List[str]:
        """List all installed (registered) MCP IDs"""
        return sorted(list(self._mcps.keys()))

    def is_core(self, mcp_id: str) -> bool:
        """Check if MCP is a core MCP"""
        return mcp_id in CORE_MCPS

    def is_registered(self, mcp_id: str) -> bool:
        """Check if MCP is registered"""
        return mcp_id in self._mcps or mcp_id in self._mcp_classes

    def unregister(self, mcp_id: str) -> bool:
        """
        Unregister an MCP.

        Args:
            mcp_id: MCP identifier

        Returns:
            True if unregistered, False if not found
        """
        if mcp_id in self._mcps:
            del self._mcps[mcp_id]
            logger.info(f"Unregistered MCP: {mcp_id}")
            return True

        if mcp_id in self._mcp_classes:
            del self._mcp_classes[mcp_id]
            return True

        return False

    def load_core_mcps(self) -> int:
        """
        Load all core MCPs.

        Returns:
            Number of MCPs loaded
        """
        if self._loaded_core:
            return len([m for m in self._mcps if m in CORE_MCPS])

        loaded = 0

        # Import core MCPs
        try:
            from mcps.core import ctax, law, tender, market, publish, syndicate, orchestrator

            # CTAX
            if hasattr(ctax, 'CTAXMCP'):
                self.register_class("ctax", ctax.CTAXMCP)
                loaded += 1

            # LAW
            if hasattr(law, 'LAWMCP'):
                self.register_class("law", law.LAWMCP)
                loaded += 1

            # TENDER
            if hasattr(tender, 'TenderEngineMCP'):
                self.register_class("tender", tender.TenderEngineMCP)
                loaded += 1

            # MARKET
            if hasattr(market, 'MarketMCP'):
                self.register_class("market", market.MarketMCP)
                loaded += 1

            # PUBLISH
            if hasattr(publish, 'PublishMCP'):
                self.register_class("publish", publish.PublishMCP)
                loaded += 1

            # SYNDICATE
            if hasattr(syndicate, 'SyndicateMCP'):
                self.register_class("syndicate", syndicate.SyndicateMCP)
                loaded += 1

            # ORCHESTRATOR (NEW)
            if hasattr(orchestrator, 'OrchestratorMCP'):
                self.register_class("orchestrator", orchestrator.OrchestratorMCP)
                loaded += 1

        except ImportError as e:
            logger.warning(f"Could not import core MCPs: {e}")

        self._loaded_core = True
        logger.info(f"Loaded {loaded}/{len(CORE_MCPS)} core MCPs")
        return loaded

    def load_from_path(self, path: Path) -> Optional[BaseMCP]:
        """
        Load an MCP from a directory path.

        Used for marketplace MCP installation.

        Args:
            path: Path to MCP directory (should contain mcp.py)

        Returns:
            Loaded MCP instance or None
        """
        mcp_file = path / "mcp.py"
        if not mcp_file.exists():
            logger.error(f"MCP file not found: {mcp_file}")
            return None

        try:
            # Dynamic import
            spec = importlib.util.spec_from_file_location("mcp", mcp_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find BaseMCP subclass
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                    issubclass(attr, BaseMCP) and
                    attr is not BaseMCP):
                    instance = attr()
                    self.register(instance)
                    return instance

            logger.error(f"No BaseMCP subclass found in {mcp_file}")
            return None

        except Exception as e:
            logger.error(f"Failed to load MCP from {path}: {e}")
            return None

    def get_info(self, mcp_id: str) -> Optional[Dict]:
        """Get MCP info without instantiating"""
        mcp = self.get(mcp_id)
        if mcp:
            return mcp.info
        return None

    def __len__(self) -> int:
        return len(self._mcps) + len(self._mcp_classes)

    def __contains__(self, mcp_id: str) -> bool:
        return self.is_registered(mcp_id)


# Singleton instance
_registry: Optional[MCPRegistry] = None


def get_registry() -> MCPRegistry:
    """Get the global MCP registry singleton"""
    global _registry
    if _registry is None:
        _registry = MCPRegistry()
    return _registry


def register_mcp(mcp: BaseMCP) -> None:
    """Convenience function to register an MCP"""
    get_registry().register(mcp)


def get_mcp(mcp_id: str) -> Optional[BaseMCP]:
    """Convenience function to get an MCP"""
    return get_registry().get(mcp_id)
