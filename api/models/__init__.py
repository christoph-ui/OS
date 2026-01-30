"""
SQLAlchemy database models
"""

# Core models
from .user import User
from .customer import Customer
from .partner import Partner
from .subscription import Subscription
from .deployment import Deployment
from .invoice import Invoice
from .usage import UsageMetric
from .support_ticket import SupportTicket
from .audit_log import AuditLog

# Connector models (formerly MCP)
from .connector import Connector, MCP  # MCP is alias for backward compatibility
from .connection import Connection, MCPInstallation  # MCPInstallation is alias
from .connector_developer import ConnectorDeveloper, MCPDeveloper  # MCPDeveloper is alias
from .connector_category import ConnectorCategory
from .connector_review import ConnectorReview
from .connection_credential import ConnectionCredential, ConnectionType, ConnectionStatus

# Expert marketplace models
from .expert import Expert
from .engagement import Engagement
from .task import Task
from .booking import Booking, ExpertAvailability, ExpertBlockedTime
from .expert_payout import ExpertPayout, ExpertEarnings

# Workflow models
from .workflow import Workflow
from .workflow_definition import WorkflowDefinition
from .workflow_subscription import WorkflowSubscription
from .workflow_execution import WorkflowExecution
from .workflow_step_log import WorkflowStepLog

# Medusa models
from .medusa_registration import MedusaRegistration

__all__ = [
    # Core
    "User",
    "Customer",
    "Partner",
    "Subscription",
    "Deployment",
    "Invoice",
    "UsageMetric",
    "SupportTicket",
    "AuditLog",
    
    # Connectors (new)
    "Connector",
    "Connection",
    "ConnectorDeveloper",
    "ConnectorCategory",
    "ConnectorReview",
    "ConnectionCredential",
    "ConnectionType",
    "ConnectionStatus",
    
    # Legacy aliases (backward compatibility)
    "MCP",
    "MCPInstallation",
    "MCPDeveloper",
    
    # Expert marketplace
    "Expert",
    "Engagement",
    "Task",
    "Booking",
    "ExpertAvailability",
    "ExpertBlockedTime",
    "ExpertPayout",
    "ExpertEarnings",
    
    # Workflows
    "Workflow",
    "WorkflowDefinition",
    "WorkflowSubscription",
    "WorkflowExecution",
    "WorkflowStepLog",
    
    # Other
    "MedusaRegistration",
]
