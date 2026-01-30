# 0711-OS Refactoring Plan

## Overview

Three major initiatives:
1. **MCP → Connector Rename** - Clearer terminology
2. **Dynamic Marketplace** - Database-driven, not hardcoded
3. **Expert Booking System** - Complete freelancer marketplace with payments

---

## 1. MCP → Connector Rename

### Terminology Mapping

| Old Term | New Term | Description |
|----------|----------|-------------|
| MCP | Connector | Any integration (data source, AI model, output channel) |
| MCPInstallation | Connection | Active connection instance for a customer |
| MCPDeveloper | ConnectorDeveloper | Third-party connector creator |
| mcp_expertise | connector_expertise | Expert's connector skills |
| enabled_mcps | enabled_connectors | Customer's enabled connectors |

### Files to Rename

```
api/models/mcp.py → api/models/connector.py
api/models/mcp_installation.py → api/models/connection.py
api/models/mcp_developer.py → api/models/connector_developer.py
api/routes/mcps.py → api/routes/connectors.py
api/routes/mcp_services.py → api/routes/connector_services.py
api/routes/mcp_developers.py → api/routes/connector_developers.py
api/schemas/mcp.py → api/schemas/connector.py (if exists)
mcps/ → connectors/
```

### Database Migration

```sql
-- Rename tables
ALTER TABLE mcps RENAME TO connectors;
ALTER TABLE mcp_installations RENAME TO connections;
ALTER TABLE mcp_developers RENAME TO connector_developers;

-- Rename columns
ALTER TABLE customers RENAME COLUMN enabled_mcps TO enabled_connectors;
ALTER TABLE customers RENAME COLUMN connected_mcps TO active_connections;
ALTER TABLE experts RENAME COLUMN mcp_expertise TO connector_expertise;
ALTER TABLE engagements RENAME COLUMN mcps_used TO connectors_used;
ALTER TABLE tasks RENAME COLUMN mcp_used TO connector_used;
ALTER TABLE workflows RENAME COLUMN required_mcps TO required_connectors;

-- Rename foreign keys and indexes
ALTER INDEX ix_mcps_name RENAME TO ix_connectors_name;
ALTER INDEX ix_mcps_developer_id RENAME TO ix_connectors_developer_id;
-- etc.
```

### Connector Categories (New Structure)

```python
CONNECTOR_CATEGORIES = {
    "data_sources": {
        "name": "Data Sources",
        "description": "Connect your existing data",
        "subcategories": ["crm", "erp", "cloud_storage", "databases"]
    },
    "ai_models": {
        "name": "AI Models", 
        "description": "Specialized AI for your domain",
        "subcategories": ["tax", "legal", "logistics", "marketing"]
    },
    "outputs": {
        "name": "Output Channels",
        "description": "Publish and distribute",
        "subcategories": ["ecommerce", "publishing", "communication"]
    }
}
```

---

## 2. Dynamic Marketplace

### Current Problems
- Categories hardcoded in routes
- Featured connectors hardcoded
- Stats are fake numbers
- No search/filtering from DB

### New Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     MARKETPLACE SERVICE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   Search     │    │   Browse     │    │   Install    │       │
│  │   Engine     │    │   & Filter   │    │   Flow       │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                   │                   │                │
│         ▼                   ▼                   ▼                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    PostgreSQL                            │    │
│  │  • connectors (with full-text search)                   │    │
│  │  • connector_categories                                  │    │
│  │  • connector_reviews                                     │    │
│  │  • connections (installations)                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### New Models

```python
# connector_category.py
class ConnectorCategory(Base):
    __tablename__ = "connector_categories"
    
    id = Column(UUID, primary_key=True)
    slug = Column(String(50), unique=True)  # "data_sources"
    name = Column(String(100))  # "Data Sources"
    description = Column(Text)
    icon = Column(String(10))
    parent_id = Column(UUID, ForeignKey("connector_categories.id"))
    sort_order = Column(Integer, default=0)
    
# connector_review.py  
class ConnectorReview(Base):
    __tablename__ = "connector_reviews"
    
    id = Column(UUID, primary_key=True)
    connector_id = Column(UUID, ForeignKey("connectors.id"))
    customer_id = Column(UUID, ForeignKey("customers.id"))
    user_id = Column(UUID, ForeignKey("users.id"))
    rating = Column(Integer)  # 1-5
    title = Column(String(255))
    content = Column(Text)
    helpful_count = Column(Integer, default=0)
    verified_purchase = Column(Boolean, default=False)
    created_at = Column(DateTime)
```

### New API Endpoints

```
GET  /api/marketplace/connectors
     ?category=data_sources
     ?subcategory=crm
     ?search=salesforce
     ?pricing=free|paid
     ?sort=popular|newest|rating
     &page=1&limit=20

GET  /api/marketplace/connectors/{id}
GET  /api/marketplace/connectors/{id}/reviews
POST /api/marketplace/connectors/{id}/reviews
GET  /api/marketplace/categories
GET  /api/marketplace/categories/{slug}/connectors
GET  /api/marketplace/featured
GET  /api/marketplace/trending
GET  /api/marketplace/stats
POST /api/marketplace/connectors/{id}/install
DELETE /api/marketplace/connections/{id}
```

---

## 3. Expert Booking System

### Current State
- Expert model exists
- Engagement model exists
- Task model exists
- No booking flow
- No payment integration

### New Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXPERT BOOKING FLOW                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   DISCOVERY          BOOKING           EXECUTION      PAYMENT   │
│   ─────────          ───────           ─────────      ───────   │
│                                                                  │
│   Browse             Request           Expert         Invoice   │
│   Experts            Consultation      Works          Generated │
│      │                   │                │              │       │
│      ▼                   ▼                ▼              ▼       │
│   ┌─────┐           ┌─────┐          ┌─────┐        ┌─────┐    │
│   │     │           │     │          │     │        │     │    │
│   │ 🔍  │──────────►│ 📅  │─────────►│ ⚡  │───────►│ 💳  │    │
│   │     │           │     │          │     │        │     │    │
│   └─────┘           └─────┘          └─────┘        └─────┘    │
│   Filter by:        - Calendar       - Tasks        - Stripe   │
│   - Connector       - Availability   - Time logs    - Invoices │
│   - Rating          - Scope          - Deliverables - Payouts  │
│   - Price           - Proposal       - Chat         │           │
│   - Availability                                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### New Models

```python
# booking.py
class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(UUID, primary_key=True)
    customer_id = Column(UUID, ForeignKey("customers.id"))
    expert_id = Column(UUID, ForeignKey("experts.id"))
    
    # Request details
    title = Column(String(255))
    description = Column(Text)
    connector_focus = Column(ARRAY(String))  # Which connectors needed
    
    # Scheduling
    requested_start = Column(DateTime)
    estimated_hours = Column(Integer)
    urgency = Column(String(20))  # normal, urgent, flexible
    
    # Status workflow
    status = Column(String(20))  # pending, accepted, declined, in_progress, completed, cancelled
    
    # Expert response
    expert_proposal = Column(Text)
    proposed_rate_cents = Column(Integer)
    proposed_hours = Column(Integer)
    accepted_at = Column(DateTime)
    declined_reason = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

# expert_availability.py
class ExpertAvailability(Base):
    __tablename__ = "expert_availability"
    
    id = Column(UUID, primary_key=True)
    expert_id = Column(UUID, ForeignKey("experts.id"))
    
    day_of_week = Column(Integer)  # 0=Monday
    start_time = Column(Time)
    end_time = Column(Time)
    timezone = Column(String(50))
    
# expert_payout.py
class ExpertPayout(Base):
    __tablename__ = "expert_payouts"
    
    id = Column(UUID, primary_key=True)
    expert_id = Column(UUID, ForeignKey("experts.id"))
    engagement_id = Column(UUID, ForeignKey("engagements.id"))
    
    amount_cents = Column(Integer)
    platform_fee_cents = Column(Integer)  # 0711's cut
    net_amount_cents = Column(Integer)
    
    stripe_transfer_id = Column(String(255))
    status = Column(String(20))  # pending, processing, completed, failed
    
    paid_at = Column(DateTime)
    created_at = Column(DateTime)
```

### Stripe Connect Integration

```python
# Expert onboarding flow
1. Expert signs up
2. Redirect to Stripe Connect onboarding
3. Expert completes Stripe account setup
4. Webhook confirms account active
5. Expert can now receive payments

# Payment flow
1. Customer books expert
2. Expert completes work
3. Customer approves deliverables
4. Invoice generated
5. Customer pays via Stripe
6. Platform takes fee (e.g., 15%)
7. Remaining amount transferred to expert's Stripe account
```

### New API Endpoints

```
# Discovery
GET  /api/experts
GET  /api/experts/{id}
GET  /api/experts/{id}/availability
GET  /api/experts/{id}/reviews

# Booking
POST /api/bookings                    # Customer requests booking
GET  /api/bookings                    # List my bookings
GET  /api/bookings/{id}               # Booking details
PUT  /api/bookings/{id}/accept        # Expert accepts
PUT  /api/bookings/{id}/decline       # Expert declines
PUT  /api/bookings/{id}/cancel        # Either party cancels

# Engagement (after booking accepted)
POST /api/engagements                 # Create from booking
GET  /api/engagements/{id}
POST /api/engagements/{id}/tasks      # Add task
PUT  /api/engagements/{id}/complete   # Mark complete

# Payments
POST /api/experts/stripe/onboard      # Start Stripe Connect
GET  /api/experts/stripe/status       # Check onboarding status
POST /api/engagements/{id}/invoice    # Generate invoice
POST /api/invoices/{id}/pay           # Process payment
GET  /api/experts/payouts             # Expert views payouts
```

---

## Implementation Order

### Phase 1: Connector Rename (Day 1)
1. Create migration script
2. Rename files
3. Update imports
4. Update API routes
5. Update frontend references

### Phase 2: Dynamic Marketplace (Day 2)
1. Create new models (categories, reviews)
2. Seed categories
3. Build marketplace service
4. Replace hardcoded routes
5. Add search with pg_trgm

### Phase 3: Expert Booking (Day 3-4)
1. Create booking models
2. Build booking flow
3. Stripe Connect integration
4. Payment processing
5. Payout system

---

## Migration Safety

```bash
# Before migration
pg_dump -U vault os711 > backup_before_refactor.sql

# Run migration
alembic upgrade head

# Verify
python -c "from api.models import Connector; print('OK')"

# If failed, rollback
alembic downgrade -1
psql -U vault os711 < backup_before_refactor.sql
```
