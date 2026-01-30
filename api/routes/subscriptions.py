"""
Subscription and billing routes
Handles subscription creation, management, and billing
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from uuid import UUID

from ..database import get_db
from ..models.customer import Customer
from ..models.subscription import Subscription
from ..models.deployment import Deployment
from ..schemas.billing import (
    CreateSubscriptionRequest,
    CreateInvoiceSubscriptionRequest,
    InvoiceResponse
)
from ..schemas.subscription import SubscriptionResponse
from ..services.stripe_service import StripeService
from ..services.invoice_service import InvoiceService
from ..services.license_service import LicenseService
from ..services.email_service import EmailService
from ..utils.security import get_current_customer_id
from ..config import settings

router = APIRouter()


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_subscription(
    request: CreateSubscriptionRequest,
    customer_id: str = Depends(get_current_customer_id),
    db: Session = Depends(get_db)
):
    """
    Create subscription with card payment (Stripe)

    Creates a Stripe subscription and stores it in the database.
    Also creates a deployment and generates a license key.
    """
    # Get customer
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    # Check if customer already has an active subscription
    existing_sub = db.query(Subscription).filter(
        Subscription.customer_id == customer_id,
        Subscription.status.in_(["active", "trialing"])
    ).first()

    if existing_sub:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sie haben bereits ein aktives Abonnement"
        )

    try:
        # Create or get Stripe customer
        if not customer.stripe_customer_id:
            stripe_customer = await StripeService.create_customer(
                email=customer.contact_email,
                name=customer.company_name,
                metadata={"customer_id": str(customer.id)}
            )
            customer.stripe_customer_id = stripe_customer.id
            db.commit()

        # Get Stripe price ID
        price_id = StripeService.get_price_id(request.plan, request.billing_cycle)

        # Create Stripe subscription
        stripe_sub = await StripeService.create_subscription(
            customer_id=customer.stripe_customer_id,
            price_id=price_id,
            payment_method_id=request.payment_method_id
        )

        # Get pricing
        pricing = StripeService.get_plan_price(request.plan, request.billing_cycle)

        # Create subscription record
        subscription = Subscription(
            customer_id=customer.id,
            plan_id=request.plan,
            plan_name=request.plan.title(),
            billing_cycle=request.billing_cycle,
            price_monthly_cents=pricing["monthly"],
            price_annual_cents=pricing["annual"],
            stripe_subscription_id=stripe_sub.id,
            stripe_price_id=price_id,
            status=stripe_sub.status,
            current_period_start=datetime.fromtimestamp(stripe_sub.current_period_start),
            current_period_end=datetime.fromtimestamp(stripe_sub.current_period_end)
        )

        db.add(subscription)

        # Update customer tier
        customer.tier = request.plan

        db.commit()
        db.refresh(subscription)

        # Create deployment and license key
        license_key = LicenseService.generate_license_key(
            customer_id=str(customer.id),
            plan=request.plan
        )

        license_expires = LicenseService.calculate_expiration(request.plan)

        deployment = Deployment(
            customer_id=customer.id,
            name=f"{customer.company_name} - Production",
            deployment_type="self_hosted",
            version="1.0.0",
            license_key=license_key,
            license_expires_at=license_expires,
            status="active",
            mcps_enabled=_get_plan_mcps(request.plan)
        )

        db.add(deployment)
        db.commit()

        # Send welcome email
        await EmailService.send_welcome_email(
            email=customer.contact_email,
            name=customer.contact_name,
            license_key=license_key
        )

        return {
            "subscription_id": str(subscription.id),
            "status": stripe_sub.status,
            "license_key": license_key,
            "message": "Subscription erfolgreich erstellt"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Erstellen des Abonnements: {str(e)}"
        )


@router.post("/create-invoice", status_code=status.HTTP_201_CREATED)
async def create_invoice_subscription(
    request: CreateInvoiceSubscriptionRequest,
    customer_id: str = Depends(get_current_customer_id),
    db: Session = Depends(get_db)
):
    """
    Create subscription with invoice payment (Rechnung)

    Creates a subscription record and generates a German invoice.
    No Stripe integration for this flow.
    """
    # Get customer
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    # Check if customer already has an active subscription
    existing_sub = db.query(Subscription).filter(
        Subscription.customer_id == customer_id,
        Subscription.status == "active"
    ).first()

    if existing_sub:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sie haben bereits ein aktives Abonnement"
        )

    try:
        # Update customer with VAT info
        if request.vat_id:
            customer.vat_id = request.vat_id
            db.commit()

        # Get pricing
        pricing = StripeService.get_plan_price(request.plan, request.billing_cycle)

        # Calculate period dates
        period_start = datetime.utcnow()
        if request.billing_cycle == "annual":
            period_end = period_start + timedelta(days=365)
        else:
            period_end = period_start + timedelta(days=30)

        # Create subscription record
        subscription = Subscription(
            customer_id=customer.id,
            plan_id=request.plan,
            plan_name=request.plan.title(),
            billing_cycle=request.billing_cycle,
            price_monthly_cents=pricing["monthly"],
            price_annual_cents=pricing["annual"],
            status="active",
            current_period_start=period_start,
            current_period_end=period_end
        )

        db.add(subscription)

        # Update customer tier
        customer.tier = request.plan

        db.commit()
        db.refresh(subscription)

        # Generate and send invoice
        invoice = await InvoiceService.create_invoice(
            db=db,
            customer=customer,
            subscription=subscription,
            billing_email=request.billing_email or customer.contact_email,
            po_number=request.po_number
        )

        # Create deployment and license key
        license_key = LicenseService.generate_license_key(
            customer_id=str(customer.id),
            plan=request.plan
        )

        license_expires = LicenseService.calculate_expiration(request.plan)

        deployment = Deployment(
            customer_id=customer.id,
            name=f"{customer.company_name} - Production",
            deployment_type="self_hosted",
            version="1.0.0",
            license_key=license_key,
            license_expires_at=license_expires,
            status="active",
            mcps_enabled=_get_plan_mcps(request.plan)
        )

        db.add(deployment)
        db.commit()

        return {
            "subscription_id": str(subscription.id),
            "invoice_number": invoice.invoice_number,
            "license_key": license_key,
            "status": "pending_payment",
            "message": "Abonnement erstellt. Rechnung wurde per E-Mail versandt."
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Erstellen des Abonnements: {str(e)}"
        )


@router.get("/current", response_model=SubscriptionResponse)
async def get_current_subscription(
    customer_id: str = Depends(get_current_customer_id),
    db: Session = Depends(get_db)
):
    """Get customer's current subscription"""
    subscription = db.query(Subscription).filter(
        Subscription.customer_id == customer_id,
        Subscription.status.in_(["active", "trialing", "past_due"])
    ).first()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kein aktives Abonnement gefunden"
        )

    return SubscriptionResponse.from_orm(subscription)


@router.post("/cancel")
async def cancel_subscription(
    immediately: bool = False,
    customer_id: str = Depends(get_current_customer_id),
    db: Session = Depends(get_db)
):
    """
    Cancel subscription

    Args:
        immediately: If true, cancel immediately. Otherwise, at period end.
    """
    subscription = db.query(Subscription).filter(
        Subscription.customer_id == customer_id,
        Subscription.status.in_(["active", "trialing"])
    ).first()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kein aktives Abonnement gefunden"
        )

    try:
        # Cancel Stripe subscription if exists
        if subscription.stripe_subscription_id:
            await StripeService.cancel_subscription(
                subscription_id=subscription.stripe_subscription_id,
                immediately=immediately
            )

        # Update subscription status
        if immediately:
            subscription.status = "canceled"
            subscription.canceled_at = datetime.utcnow()
        else:
            # Will be canceled at period end
            subscription.canceled_at = subscription.current_period_end

        db.commit()

        return {
            "message": "Abonnement gekündigt" if immediately else "Abonnement wird am Ende der Laufzeit gekündigt",
            "canceled_at": subscription.canceled_at.isoformat() if subscription.canceled_at else None
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Kündigen des Abonnements: {str(e)}"
        )


@router.post("/upgrade")
async def upgrade_subscription(
    new_plan: str,
    customer_id: str = Depends(get_current_customer_id),
    db: Session = Depends(get_db)
):
    """
    Upgrade/downgrade subscription plan

    Upgrades are prorated immediately, downgrades take effect at period end.
    """
    subscription = db.query(Subscription).filter(
        Subscription.customer_id == customer_id,
        Subscription.status == "active"
    ).first()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kein aktives Abonnement gefunden"
        )

    if new_plan == subscription.plan_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sie haben bereits diesen Plan"
        )

    try:
        # Update Stripe subscription if exists
        if subscription.stripe_subscription_id:
            new_price_id = StripeService.get_price_id(new_plan, subscription.billing_cycle)
            await StripeService.update_subscription(
                subscription_id=subscription.stripe_subscription_id,
                new_price_id=new_price_id
            )

        # Update subscription
        subscription.plan_id = new_plan
        subscription.plan_name = new_plan.title()

        # Update pricing
        pricing = StripeService.get_plan_price(new_plan, subscription.billing_cycle)
        subscription.price_monthly_cents = pricing["monthly"]
        subscription.price_annual_cents = pricing["annual"]

        # Update customer tier
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        customer.tier = new_plan

        # Update deployment MCPs
        deployment = db.query(Deployment).filter(
            Deployment.customer_id == customer_id,
            Deployment.status == "active"
        ).first()

        if deployment:
            deployment.mcps_enabled = _get_plan_mcps(new_plan)

        db.commit()

        return {
            "message": f"Plan erfolgreich auf {new_plan} geändert",
            "new_plan": new_plan
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Ändern des Plans: {str(e)}"
        )


@router.get("/invoices", response_model=List[InvoiceResponse])
async def list_invoices(
    customer_id: str = Depends(get_current_customer_id),
    db: Session = Depends(get_db)
):
    """List all invoices for customer"""
    from ..models.invoice import Invoice

    invoices = db.query(Invoice).filter(
        Invoice.customer_id == customer_id
    ).order_by(Invoice.created_at.desc()).all()

    return [InvoiceResponse.from_orm(inv) for inv in invoices]


def _get_plan_mcps(plan: str) -> List[str]:
    """Get available MCPs for a plan"""
    mcp_mapping = {
        "starter": ["ctax"],  # 1 MCP
        "professional": ["ctax", "etim", "law", "hr", "pricing"],  # 5 MCPs
        "business": ["ctax", "etim", "law", "hr", "pricing", "tender", "sanctions"],  # All MCPs
        "enterprise": ["ctax", "etim", "law", "hr", "pricing", "tender", "sanctions"]  # All MCPs
    }
    return mcp_mapping.get(plan, ["ctax"])
