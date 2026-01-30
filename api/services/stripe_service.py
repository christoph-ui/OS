"""
Stripe service for payment processing
"""

import stripe
import logging
from typing import Dict, Optional
from decimal import Decimal

from ..config import settings

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.stripe_secret_key


class StripeService:
    """Stripe integration service"""

    # Plan pricing (in cents)
    PLANS = {
        "starter": {
            "monthly": 0,
            "annual": 0
        },
        "professional": {
            "monthly": 99000,  # €990
            "annual": 950400   # €9,504 (20% discount)
        },
        "business": {
            "monthly": 299000,  # €2,990
            "annual": 2870400   # €28,704 (20% discount)
        }
    }

    # Stripe Price IDs (would be set up in Stripe Dashboard)
    PRICE_IDS = {
        "professional_monthly": "price_professional_monthly",
        "professional_annual": "price_professional_annual",
        "business_monthly": "price_business_monthly",
        "business_annual": "price_business_annual"
    }

    @classmethod
    def get_plan_price(cls, plan: str, billing_cycle: str) -> Dict[str, int]:
        """Get plan pricing"""
        if plan not in cls.PLANS:
            raise ValueError(f"Invalid plan: {plan}")

        return cls.PLANS[plan]

    @classmethod
    def get_price_id(cls, plan: str, billing_cycle: str) -> str:
        """
        Get Stripe Price ID for a plan and billing cycle

        Args:
            plan: Plan name (starter, professional, business)
            billing_cycle: Billing cycle (monthly, annual)

        Returns:
            Stripe Price ID

        Raises:
            ValueError: If invalid plan or billing cycle
        """
        if plan == "starter":
            return None  # Free plan, no Stripe price

        key = f"{plan}_{billing_cycle}"
        if key not in cls.PRICE_IDS:
            raise ValueError(f"Invalid plan/cycle combination: {key}")

        return cls.PRICE_IDS[key]

    @classmethod
    async def create_customer(
        cls,
        email: str,
        name: str,
        metadata: Optional[Dict] = None
    ) -> stripe.Customer:
        """
        Create a Stripe customer

        Args:
            email: Customer email
            name: Customer name
            metadata: Additional metadata

        Returns:
            Stripe Customer object
        """
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {}
            )
            logger.info(f"Created Stripe customer: {customer.id} for {email}")
            return customer

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            raise

    @classmethod
    async def create_subscription(
        cls,
        customer_id: str,
        price_id: str,
        payment_method_id: str
    ) -> stripe.Subscription:
        """
        Create a Stripe subscription

        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID
            payment_method_id: Stripe payment method ID

        Returns:
            Stripe Subscription object
        """
        try:
            # Attach payment method to customer
            stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id
            )

            # Set as default payment method
            stripe.Customer.modify(
                customer_id,
                invoice_settings={"default_payment_method": payment_method_id}
            )

            # Create subscription
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": price_id}],
                expand=["latest_invoice.payment_intent"]
            )

            logger.info(f"Created Stripe subscription: {subscription.id} for customer {customer_id}")
            return subscription

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe subscription: {e}")
            raise

    @classmethod
    async def cancel_subscription(
        cls,
        subscription_id: str,
        immediately: bool = False
    ) -> stripe.Subscription:
        """
        Cancel a Stripe subscription

        Args:
            subscription_id: Stripe subscription ID
            immediately: If True, cancel immediately. Otherwise, at period end.

        Returns:
            Updated Stripe Subscription object
        """
        try:
            if immediately:
                subscription = stripe.Subscription.cancel(subscription_id)
            else:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )

            logger.info(f"Canceled Stripe subscription: {subscription_id}")
            return subscription

        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel Stripe subscription: {e}")
            raise

    @classmethod
    async def update_subscription(
        cls,
        subscription_id: str,
        new_price_id: str
    ) -> stripe.Subscription:
        """
        Update subscription plan (upgrade/downgrade)

        Args:
            subscription_id: Stripe subscription ID
            new_price_id: New Stripe price ID

        Returns:
            Updated Stripe Subscription object
        """
        try:
            # Get current subscription
            subscription = stripe.Subscription.retrieve(subscription_id)

            # Update subscription item
            stripe.Subscription.modify(
                subscription_id,
                items=[{
                    "id": subscription["items"]["data"][0].id,
                    "price": new_price_id
                }],
                proration_behavior="always_invoice"
            )

            logger.info(f"Updated Stripe subscription: {subscription_id} to price {new_price_id}")
            return subscription

        except stripe.error.StripeError as e:
            logger.error(f"Failed to update Stripe subscription: {e}")
            raise

    @classmethod
    def construct_webhook_event(cls, payload: bytes, signature: str):
        """
        Construct and verify a Stripe webhook event

        Args:
            payload: Raw request body
            signature: Stripe signature header

        Returns:
            Stripe Event object

        Raises:
            ValueError: If signature verification fails
        """
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                settings.stripe_webhook_secret
            )
            return event

        except ValueError as e:
            logger.error(f"Invalid Stripe webhook payload: {e}")
            raise
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid Stripe webhook signature: {e}")
            raise
