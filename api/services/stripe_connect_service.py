"""
Stripe Connect Service
Handles expert payout accounts and transfers
"""

import stripe
from typing import Optional, Dict
from datetime import datetime
from core.config import settings

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeConnectService:
    """Service for managing Stripe Connect accounts for experts"""

    def create_connect_account(
        self,
        expert_id: str,
        email: str,
        first_name: str,
        last_name: str,
        country: str = "DE",
        iban: Optional[str] = None,
        tax_id: Optional[str] = None
    ) -> Dict:
        """
        Create Stripe Connect account for expert

        Args:
            expert_id: Expert UUID
            email: Expert email
            first_name: Expert first name
            last_name: Expert last name
            country: Country code (default: DE for Germany)
            iban: IBAN for payouts
            tax_id: Tax ID number

        Returns:
            dict with account_id, onboarding_url
        """
        try:
            # Create Express Connect account (simplest onboarding)
            account = stripe.Account.create(
                type="express",
                country=country,
                email=email,
                capabilities={
                    "transfers": {"requested": True},
                },
                business_type="individual",
                individual={
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                },
                metadata={
                    "expert_id": expert_id,
                    "platform": "0711"
                }
            )

            # Add bank account if IBAN provided
            if iban:
                self._add_bank_account(account.id, iban, country)

            # Create account link for onboarding
            account_link = stripe.AccountLink.create(
                account=account.id,
                refresh_url=f"{settings.WEBSITE_URL}/expert-signup/connect-refresh",
                return_url=f"{settings.WEBSITE_URL}/expert-signup/connect-success",
                type="account_onboarding",
            )

            return {
                "success": True,
                "account_id": account.id,
                "onboarding_url": account_link.url,
                "created": True
            }

        except stripe.error.StripeError as e:
            print(f"Stripe Connect error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _add_bank_account(self, account_id: str, iban: str, country: str = "DE"):
        """Add bank account to Connect account"""
        try:
            stripe.Account.create_external_account(
                account_id,
                external_account={
                    "object": "bank_account",
                    "country": country,
                    "currency": "eur",
                    "account_number": iban,
                }
            )
        except stripe.error.StripeError as e:
            print(f"Error adding bank account: {e}")

    def get_account_status(self, account_id: str) -> Dict:
        """Get Stripe Connect account status"""
        try:
            account = stripe.Account.retrieve(account_id)

            return {
                "account_id": account.id,
                "charges_enabled": account.charges_enabled,
                "payouts_enabled": account.payouts_enabled,
                "details_submitted": account.details_submitted,
                "requirements": {
                    "currently_due": account.requirements.currently_due,
                    "eventually_due": account.requirements.eventually_due,
                    "past_due": account.requirements.past_due,
                },
                "email": account.email
            }

        except stripe.error.StripeError as e:
            return {
                "error": str(e)
            }

    def create_payout(
        self,
        account_id: str,
        amount_cents: int,
        currency: str = "eur",
        description: str = "Weekly payout"
    ) -> Dict:
        """
        Create payout to expert's Connect account

        Args:
            account_id: Stripe Connect account ID
            amount_cents: Amount in cents (e.g., 880000 for €8,800)
            currency: Currency code (default: eur)
            description: Payout description

        Returns:
            dict with payout_id, amount, status
        """
        try:
            # Create transfer to Connect account
            transfer = stripe.Transfer.create(
                amount=amount_cents,
                currency=currency,
                destination=account_id,
                description=description,
            )

            return {
                "success": True,
                "payout_id": transfer.id,
                "amount": amount_cents / 100,
                "currency": currency,
                "status": transfer.status,
                "created": transfer.created
            }

        except stripe.error.StripeError as e:
            print(f"Payout error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def batch_weekly_payouts(self, expert_payouts: List[Dict]) -> Dict:
        """
        Process weekly payouts for all experts

        Args:
            expert_payouts: List of dicts with:
                - expert_id
                - account_id (Stripe Connect)
                - amount_cents
                - engagement_ids (for reference)

        Returns:
            dict with success_count, failed_count, results
        """
        results = {
            "success_count": 0,
            "failed_count": 0,
            "payouts": []
        }

        for payout_data in expert_payouts:
            result = self.create_payout(
                account_id=payout_data["account_id"],
                amount_cents=payout_data["amount_cents"],
                description=f"Weekly payout - {datetime.utcnow().strftime('%Y-%m-%d')}"
            )

            if result.get("success"):
                results["success_count"] += 1
            else:
                results["failed_count"] += 1

            results["payouts"].append({
                "expert_id": payout_data["expert_id"],
                "amount": payout_data["amount_cents"] / 100,
                "status": "success" if result.get("success") else "failed",
                "payout_id": result.get("payout_id"),
                "error": result.get("error")
            })

        return results

    def get_payout_history(
        self,
        account_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """Get payout history for expert"""
        try:
            transfers = stripe.Transfer.list(
                destination=account_id,
                limit=limit
            )

            return [
                {
                    "id": t.id,
                    "amount": t.amount / 100,
                    "currency": t.currency,
                    "status": t.status,
                    "created": datetime.fromtimestamp(t.created),
                    "description": t.description
                }
                for t in transfers.data
            ]

        except stripe.error.StripeError as e:
            print(f"Error fetching payout history: {e}")
            return []

    def get_account_balance(self, account_id: str) -> Dict:
        """Get Connect account balance"""
        try:
            balance = stripe.Balance.retrieve(
                stripe_account=account_id
            )

            return {
                "available": [
                    {
                        "amount": b.amount / 100,
                        "currency": b.currency
                    }
                    for b in balance.available
                ],
                "pending": [
                    {
                        "amount": b.amount / 100,
                        "currency": b.currency
                    }
                    for b in balance.pending
                ]
            }

        except stripe.error.StripeError as e:
            print(f"Error fetching balance: {e}")
            return {"error": str(e)}

    def update_bank_account(
        self,
        account_id: str,
        iban: str,
        country: str = "DE"
    ) -> Dict:
        """Update expert's bank account"""
        try:
            # Get existing external accounts
            external_accounts = stripe.Account.list_external_accounts(
                account_id,
                object="bank_account"
            )

            # Delete existing accounts
            for account in external_accounts.data:
                stripe.Account.delete_external_account(
                    account_id,
                    account.id
                )

            # Add new account
            new_account = stripe.Account.create_external_account(
                account_id,
                external_account={
                    "object": "bank_account",
                    "country": country,
                    "currency": "eur",
                    "account_number": iban,
                }
            )

            return {
                "success": True,
                "bank_account_id": new_account.id,
                "last4": new_account.last4
            }

        except stripe.error.StripeError as e:
            print(f"Error updating bank account: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instance
stripe_connect_service = StripeConnectService()
