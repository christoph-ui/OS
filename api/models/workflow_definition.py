"""
Workflow Definition model
Stores the actual LangGraph state machine definition for a workflow
Supports versioning (multiple definitions per workflow)
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, func, Text, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from ..database import Base


class WorkflowDefinition(Base):
    """Workflow Definition - LangGraph state machine configuration"""

    __tablename__ = "workflow_definitions"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to workflow
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)

    # Version tracking
    version = Column(String(50), nullable=False)  # e.g., "1.0.0", "1.1.0"
    is_active = Column(Boolean, default=True)  # Only one active version per workflow

    # LangGraph state machine definition
    # Example structure:
    # {
    #   "nodes": [
    #     {"id": "extract", "mcp": "pim", "action": "extract_products", "config": {...}},
    #     {"id": "classify", "mcp": "etim", "action": "classify", "config": {...}},
    #     {"id": "syndicate", "mcp": "channel", "action": "publish", "config": {...}}
    #   ],
    #   "edges": [
    #     {"from": "extract", "to": "classify"},
    #     {"from": "classify", "to": "syndicate", "condition": "success"}
    #   ],
    #   "entry_point": "extract",
    #   "error_handlers": [
    #     {"step": "*", "action": "retry", "max_attempts": 3}
    #   ]
    # }
    definition = Column(JSONB, nullable=False)

    # Metadata
    changelog = Column(Text)  # What changed in this version
    breaking_changes = Column(Boolean, default=False)  # If true, customers need to update config

    # Validation
    validated = Column(Boolean, default=False)  # If definition has been validated
    validation_errors = Column(JSONB)  # List of validation errors

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Relationships
    workflow = relationship("Workflow", back_populates="definitions")
    created_by = relationship("User", foreign_keys=[created_by_id])

    def __repr__(self):
        return f"<WorkflowDefinition {self.workflow_id} v{self.version}>"

    @property
    def step_count(self) -> int:
        """Get number of steps in workflow"""
        return len(self.definition.get("nodes", []))

    @property
    def required_mcps(self) -> list[str]:
        """Extract list of required MCPs from definition"""
        nodes = self.definition.get("nodes", [])
        return list(set(node.get("mcp") for node in nodes if node.get("mcp")))

    def validate_definition(self) -> tuple[bool, list[str]]:
        """
        Validate workflow definition structure

        Returns:
            (is_valid, errors)
        """
        errors = []

        # Check required fields
        if "nodes" not in self.definition:
            errors.append("Missing 'nodes' field in definition")

        if "edges" not in self.definition:
            errors.append("Missing 'edges' field in definition")

        if "entry_point" not in self.definition:
            errors.append("Missing 'entry_point' field in definition")

        # Validate nodes
        nodes = self.definition.get("nodes", [])
        if not nodes:
            errors.append("Workflow must have at least one node")

        node_ids = set()
        for i, node in enumerate(nodes):
            if "id" not in node:
                errors.append(f"Node {i} missing 'id' field")
            else:
                if node["id"] in node_ids:
                    errors.append(f"Duplicate node ID: {node['id']}")
                node_ids.add(node["id"])

            if "mcp" not in node:
                errors.append(f"Node {i} missing 'mcp' field")

            if "action" not in node:
                errors.append(f"Node {i} missing 'action' field")

        # Validate edges
        edges = self.definition.get("edges", [])
        for i, edge in enumerate(edges):
            if "from" not in edge or "to" not in edge:
                errors.append(f"Edge {i} missing 'from' or 'to' field")
            else:
                if edge["from"] not in node_ids:
                    errors.append(f"Edge {i}: 'from' node '{edge['from']}' does not exist")
                if edge["to"] not in node_ids:
                    errors.append(f"Edge {i}: 'to' node '{edge['to']}' does not exist")

        # Validate entry point
        entry_point = self.definition.get("entry_point")
        if entry_point and entry_point not in node_ids:
            errors.append(f"Entry point '{entry_point}' does not exist in nodes")

        return len(errors) == 0, errors
