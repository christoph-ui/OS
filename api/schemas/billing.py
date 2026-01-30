"""
Billing schemas
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from uuid import UUID
from decimal import Decimal


class LineItem(BaseModel):
    """Line item in an invoice"""
    description: str
    period: Optional[str] = None
    quantity: int
    unit_price_cents: int
    total_cents: int


class InvoiceResponse(BaseModel):
    """Schema for invoice response"""
    id: UUID
    customer_id: UUID
    invoice_number: str
    invoice_date: date
    due_date: date
    subtotal_cents: int
    vat_rate: Decimal
    vat_cents: int
    total_cents: int
    currency: str
    payment_method: Optional[str]
    payment_status: str
    pdf_url: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class CreateSubscriptionRequest(BaseModel):
    """Request schema for creating a subscription with card payment"""
    plan: str = Field(..., pattern="^(starter|professional|business|enterprise)$")
    billing_cycle: str = Field(..., pattern="^(monthly|annual)$")
    payment_method_id: str = Field(..., description="Stripe payment method ID")


class CreateInvoiceSubscriptionRequest(BaseModel):
    """Request schema for creating a subscription with invoice payment"""
    plan: str = Field(..., pattern="^(starter|professional|business|enterprise)$")
    billing_cycle: str = Field(..., pattern="^(monthly|annual)$")
    vat_id: Optional[str] = Field(None, description="VAT ID (USt-IdNr.)")
    billing_email: Optional[EmailStr] = Field(None, description="Email for invoice delivery")
    po_number: Optional[str] = Field(None, description="Purchase order number")


class UsageMetricResponse(BaseModel):
    """Schema for usage metrics response"""
    id: UUID
    deployment_id: UUID
    period_start: datetime
    period_end: datetime
    query_count: int
    mcp_calls: Optional[Dict[str, int]]
    storage_bytes: int
    embedding_tokens: int
    llm_tokens_input: int
    llm_tokens_output: int
    estimated_cost_cents: Optional[int]

    model_config = {"from_attributes": True}
