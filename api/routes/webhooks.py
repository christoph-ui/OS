"""
Webhook routes
Handles webhooks from external services (Stripe, etc.)
"""

from fastapi import APIRouter, HTTPException, Request, Depends, status
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from ..database import get_db
from ..models.subscription import Subscription
from ..models.invoice import Invoice
from ..services.stripe_service import StripeService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhooks

    Processes events from Stripe (payment success, subscription updates, etc.)
    """
    # Get raw body and signature
    payload = await request.body()
    signature = request.headers.get("stripe-signature")

    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe signature"
        )

    try:
        # Verify webhook signature
        event = StripeService.construct_webhook_event(payload, signature)

    except ValueError as e:
        logger.error(f"Invalid Stripe webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload"
        )
    except Exception as e:
        logger.error(f"Invalid Stripe webhook signature: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature"
        )

    # Handle event
    event_type = event["type"]
    event_data = event["data"]["object"]

    logger.info(f"Received Stripe webhook: {event_type}")

    try:
        if event_type == "customer.subscription.created":
            await handle_subscription_created(event_data, db)

        elif event_type == "customer.subscription.updated":
            await handle_subscription_updated(event_data, db)

        elif event_type == "customer.subscription.deleted":
            await handle_subscription_deleted(event_data, db)

        elif event_type == "invoice.paid":
            await handle_invoice_paid(event_data, db)

        elif event_type == "invoice.payment_failed":
            await handle_invoice_payment_failed(event_data, db)

        elif event_type == "customer.subscription.trial_will_end":
            await handle_trial_will_end(event_data, db)

        else:
            logger.info(f"Unhandled Stripe event type: {event_type}")

    except Exception as e:
        logger.error(f"Error processing Stripe webhook {event_type}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing webhook"
        )

    return {"status": "success"}


async def handle_subscription_created(data: dict, db: Session):
    """Handle subscription.created event"""
    stripe_sub_id = data["id"]
    logger.info(f"Subscription created: {stripe_sub_id}")

    # Subscription should already be created by our API
    # This is mainly a confirmation


async def handle_subscription_updated(data: dict, db: Session):
    """Handle subscription.updated event"""
    stripe_sub_id = data["id"]
    status_value = data["status"]

    logger.info(f"Subscription updated: {stripe_sub_id} -> {status_value}")

    # Find subscription
    subscription = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == stripe_sub_id
    ).first()

    if not subscription:
        logger.warning(f"Subscription not found: {stripe_sub_id}")
        return

    # Update status
    subscription.status = status_value

    # Update period dates
    if "current_period_start" in data:
        subscription.current_period_start = datetime.fromtimestamp(
            data["current_period_start"]
        )

    if "current_period_end" in data:
        subscription.current_period_end = datetime.fromtimestamp(
            data["current_period_end"]
        )

    # Check if canceled
    if "canceled_at" in data and data["canceled_at"]:
        subscription.canceled_at = datetime.fromtimestamp(data["canceled_at"])

    db.commit()

    logger.info(f"Subscription {stripe_sub_id} updated in database")


async def handle_subscription_deleted(data: dict, db: Session):
    """Handle subscription.deleted event"""
    stripe_sub_id = data["id"]

    logger.info(f"Subscription deleted: {stripe_sub_id}")

    # Find subscription
    subscription = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == stripe_sub_id
    ).first()

    if not subscription:
        logger.warning(f"Subscription not found: {stripe_sub_id}")
        return

    # Update status
    subscription.status = "canceled"
    subscription.canceled_at = datetime.utcnow()

    # Update customer status
    from ..models.customer import Customer
    customer = db.query(Customer).filter(Customer.id == subscription.customer_id).first()

    if customer:
        # Check if customer has any other active subscriptions
        other_active = db.query(Subscription).filter(
            Subscription.customer_id == customer.id,
            Subscription.id != subscription.id,
            Subscription.status == "active"
        ).first()

        if not other_active:
            customer.status = "churned"
            customer.tier = "starter"  # Downgrade to free tier

    db.commit()

    logger.info(f"Subscription {stripe_sub_id} deleted in database")

    # TODO: Send cancellation email
    # TODO: Suspend deployments


async def handle_invoice_paid(data: dict, db: Session):
    """Handle invoice.paid event"""
    stripe_invoice_id = data["id"]
    amount_paid = data["amount_paid"]

    logger.info(f"Invoice paid: {stripe_invoice_id} - €{amount_paid / 100}")

    # Find invoice
    invoice = db.query(Invoice).filter(
        Invoice.stripe_invoice_id == stripe_invoice_id
    ).first()

    if invoice:
        invoice.payment_status = "paid"
        invoice.paid_at = datetime.utcnow()
        db.commit()

        logger.info(f"Invoice {invoice.invoice_number} marked as paid")

    # If this is for a subscription, ensure subscription is active
    if "subscription" in data and data["subscription"]:
        subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == data["subscription"]
        ).first()

        if subscription and subscription.status == "past_due":
            subscription.status = "active"
            db.commit()

            logger.info(f"Subscription {subscription.id} reactivated after payment")


async def handle_invoice_payment_failed(data: dict, db: Session):
    """Handle invoice.payment_failed event"""
    stripe_invoice_id = data["id"]

    logger.warning(f"Invoice payment failed: {stripe_invoice_id}")

    # Find invoice
    invoice = db.query(Invoice).filter(
        Invoice.stripe_invoice_id == stripe_invoice_id
    ).first()

    if invoice:
        invoice.payment_status = "failed"
        db.commit()

    # Update subscription to past_due
    if "subscription" in data and data["subscription"]:
        subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == data["subscription"]
        ).first()

        if subscription:
            subscription.status = "past_due"
            db.commit()

            logger.info(f"Subscription {subscription.id} marked as past_due")

    # TODO: Send payment failed email
    # TODO: Notify admin


async def handle_trial_will_end(data: dict, db: Session):
    """Handle customer.subscription.trial_will_end event"""
    stripe_sub_id = data["id"]
    trial_end = datetime.fromtimestamp(data["trial_end"])

    logger.info(f"Trial ending soon: {stripe_sub_id} at {trial_end}")

    # Find subscription
    subscription = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == stripe_sub_id
    ).first()

    if subscription:
        # Get customer
        from ..models.customer import Customer
        customer = db.query(Customer).filter(
            Customer.id == subscription.customer_id
        ).first()

        # TODO: Send trial ending email
        logger.info(f"Trial ending for customer {customer.company_name}")
