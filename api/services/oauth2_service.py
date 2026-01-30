"""
OAuth2 Service
Handles OAuth2 authentication flows for various providers (Salesforce, Google, Microsoft, etc.)
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, timezone
import httpx
from urllib.parse import urlencode, parse_qs
import secrets
import logging

logger = logging.getLogger(__name__)


class OAuth2Provider:
    """Base OAuth2 provider configuration"""

    def __init__(
        self,
        name: str,
        authorization_url: str,
        token_url: str,
        client_id: str,
        client_secret: str,
        scopes: List[str],
        redirect_uri: str,
        additional_params: Optional[Dict[str, str]] = None
    ):
        self.name = name
        self.authorization_url = authorization_url
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.scopes = scopes
        self.redirect_uri = redirect_uri
        self.additional_params = additional_params or {}

    def get_authorization_url(self, state: str) -> str:
        """Generate OAuth authorization URL"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "state": state,
            **self.additional_params
        }
        return f"{self.authorization_url}?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.token_url, data=data)
            response.raise_for_status()
            return response.json()

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.token_url, data=data)
            response.raise_for_status()
            return response.json()


class OAuth2Service:
    """
    OAuth2 authentication service with support for multiple providers

    Supported Providers:
    - Salesforce
    - Google Workspace
    - Microsoft 365
    - Slack
    - HubSpot
    - Shopify
    - GitHub
    - GitLab
    - QuickBooks
    - Xero
    - Stripe
    """

    def __init__(self):
        self.providers: Dict[str, OAuth2Provider] = {}
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize OAuth2 provider configurations"""

        # Get base URLs from environment
        base_url = os.getenv("API_BASE_URL", "http://localhost:4080")

        # Salesforce
        self.providers["salesforce"] = OAuth2Provider(
            name="Salesforce",
            authorization_url="https://login.salesforce.com/services/oauth2/authorize",
            token_url="https://login.salesforce.com/services/oauth2/token",
            client_id=os.getenv("SALESFORCE_CLIENT_ID", ""),
            client_secret=os.getenv("SALESFORCE_CLIENT_SECRET", ""),
            scopes=["full", "refresh_token", "offline_access"],
            redirect_uri=f"{base_url}/api/oauth2/callback/salesforce",
            additional_params={"prompt": "consent"}
        )

        # Google Workspace
        self.providers["google"] = OAuth2Provider(
            name="Google Workspace",
            authorization_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
            scopes=[
                "https://www.googleapis.com/auth/drive.readonly",
                "https://www.googleapis.com/auth/calendar.readonly",
                "https://www.googleapis.com/auth/gmail.readonly",
                "email",
                "profile"
            ],
            redirect_uri=f"{base_url}/api/oauth2/callback/google",
            additional_params={"access_type": "offline", "prompt": "consent"}
        )

        # Microsoft 365
        self.providers["microsoft"] = OAuth2Provider(
            name="Microsoft 365",
            authorization_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
            client_id=os.getenv("MICROSOFT_CLIENT_ID", ""),
            client_secret=os.getenv("MICROSOFT_CLIENT_SECRET", ""),
            scopes=[
                "Files.Read.All",
                "Calendars.Read",
                "Mail.Read",
                "User.Read",
                "offline_access"
            ],
            redirect_uri=f"{base_url}/api/oauth2/callback/microsoft"
        )

        # Slack
        self.providers["slack"] = OAuth2Provider(
            name="Slack",
            authorization_url="https://slack.com/oauth/v2/authorize",
            token_url="https://slack.com/api/oauth.v2.access",
            client_id=os.getenv("SLACK_CLIENT_ID", ""),
            client_secret=os.getenv("SLACK_CLIENT_SECRET", ""),
            scopes=[
                "channels:read",
                "chat:write",
                "files:read",
                "users:read",
                "team:read"
            ],
            redirect_uri=f"{base_url}/api/oauth2/callback/slack"
        )

        # HubSpot
        self.providers["hubspot"] = OAuth2Provider(
            name="HubSpot",
            authorization_url="https://app.hubspot.com/oauth/authorize",
            token_url="https://api.hubapi.com/oauth/v1/token",
            client_id=os.getenv("HUBSPOT_CLIENT_ID", ""),
            client_secret=os.getenv("HUBSPOT_CLIENT_SECRET", ""),
            scopes=[
                "crm.objects.contacts.read",
                "crm.objects.companies.read",
                "crm.objects.deals.read",
                "files"
            ],
            redirect_uri=f"{base_url}/api/oauth2/callback/hubspot"
        )

        # Shopify
        self.providers["shopify"] = OAuth2Provider(
            name="Shopify",
            authorization_url="https://{shop}.myshopify.com/admin/oauth/authorize",
            token_url="https://{shop}.myshopify.com/admin/oauth/access_token",
            client_id=os.getenv("SHOPIFY_CLIENT_ID", ""),
            client_secret=os.getenv("SHOPIFY_CLIENT_SECRET", ""),
            scopes=[
                "read_products",
                "read_orders",
                "read_customers",
                "read_inventory"
            ],
            redirect_uri=f"{base_url}/api/oauth2/callback/shopify"
        )

        # GitHub
        self.providers["github"] = OAuth2Provider(
            name="GitHub",
            authorization_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            client_id=os.getenv("GITHUB_CLIENT_ID", ""),
            client_secret=os.getenv("GITHUB_CLIENT_SECRET", ""),
            scopes=["repo", "read:org", "read:user"],
            redirect_uri=f"{base_url}/api/oauth2/callback/github"
        )

        # GitLab
        self.providers["gitlab"] = OAuth2Provider(
            name="GitLab",
            authorization_url="https://gitlab.com/oauth/authorize",
            token_url="https://gitlab.com/oauth/token",
            client_id=os.getenv("GITLAB_CLIENT_ID", ""),
            client_secret=os.getenv("GITLAB_CLIENT_SECRET", ""),
            scopes=["api", "read_user", "read_repository"],
            redirect_uri=f"{base_url}/api/oauth2/callback/gitlab"
        )

        # QuickBooks
        self.providers["quickbooks"] = OAuth2Provider(
            name="QuickBooks",
            authorization_url="https://appcenter.intuit.com/connect/oauth2",
            token_url="https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer",
            client_id=os.getenv("QUICKBOOKS_CLIENT_ID", ""),
            client_secret=os.getenv("QUICKBOOKS_CLIENT_SECRET", ""),
            scopes=["com.intuit.quickbooks.accounting"],
            redirect_uri=f"{base_url}/api/oauth2/callback/quickbooks"
        )

        # Xero
        self.providers["xero"] = OAuth2Provider(
            name="Xero",
            authorization_url="https://login.xero.com/identity/connect/authorize",
            token_url="https://identity.xero.com/connect/token",
            client_id=os.getenv("XERO_CLIENT_ID", ""),
            client_secret=os.getenv("XERO_CLIENT_SECRET", ""),
            scopes=[
                "offline_access",
                "accounting.transactions.read",
                "accounting.contacts.read",
                "accounting.settings.read"
            ],
            redirect_uri=f"{base_url}/api/oauth2/callback/xero"
        )

        # Stripe
        self.providers["stripe"] = OAuth2Provider(
            name="Stripe",
            authorization_url="https://connect.stripe.com/oauth/authorize",
            token_url="https://connect.stripe.com/oauth/token",
            client_id=os.getenv("STRIPE_CONNECT_CLIENT_ID", ""),
            client_secret=os.getenv("STRIPE_SECRET_KEY", ""),
            scopes=["read_write"],
            redirect_uri=f"{base_url}/api/oauth2/callback/stripe",
            additional_params={"stripe_landing": "login"}
        )

    def get_provider(self, provider_name: str) -> OAuth2Provider:
        """Get OAuth2 provider by name"""
        if provider_name not in self.providers:
            raise ValueError(f"Unknown OAuth2 provider: {provider_name}")

        provider = self.providers[provider_name]

        # Validate configuration
        if not provider.client_id or not provider.client_secret:
            raise ValueError(
                f"OAuth2 provider '{provider_name}' not configured. "
                f"Set {provider_name.upper()}_CLIENT_ID and {provider_name.upper()}_CLIENT_SECRET"
            )

        return provider

    def generate_state(self) -> str:
        """Generate secure random state for CSRF protection"""
        return secrets.token_urlsafe(32)

    def initiate_oauth_flow(
        self,
        provider_name: str,
        customer_id: str,
        mcp_id: str,
        shop_domain: Optional[str] = None  # For Shopify
    ) -> Dict[str, str]:
        """
        Initiate OAuth2 authorization flow

        Args:
            provider_name: OAuth provider (salesforce, google, etc.)
            customer_id: Customer UUID
            mcp_id: MCP UUID
            shop_domain: Shopify shop domain (optional)

        Returns:
            {
                "authorization_url": "https://...",
                "state": "random_state_token"
            }
        """
        provider = self.get_provider(provider_name)

        # Generate state token (includes customer_id and mcp_id for callback)
        state = self.generate_state()
        state_data = {
            "state": state,
            "customer_id": customer_id,
            "mcp_id": mcp_id,
            "provider": provider_name,
        }

        # For Shopify, replace {shop} in URLs
        if provider_name == "shopify" and shop_domain:
            provider.authorization_url = provider.authorization_url.replace(
                "{shop}", shop_domain
            )
            provider.token_url = provider.token_url.replace("{shop}", shop_domain)
            state_data["shop_domain"] = shop_domain

        authorization_url = provider.get_authorization_url(state)

        logger.info(f"Initiated OAuth flow: {provider_name} for customer {customer_id}")

        return {
            "authorization_url": authorization_url,
            "state": state,
            "state_data": state_data  # Store this temporarily (Redis cache)
        }

    async def handle_oauth_callback(
        self,
        provider_name: str,
        code: str,
        state: str,
        shop_domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle OAuth2 callback and exchange code for tokens

        Args:
            provider_name: OAuth provider
            code: Authorization code
            state: State token (for CSRF validation)
            shop_domain: Shopify shop domain (optional)

        Returns:
            {
                "access_token": "...",
                "refresh_token": "...",
                "expires_in": 3600,
                "token_type": "Bearer",
                "scope": "...",
                ...
            }
        """
        provider = self.get_provider(provider_name)

        # For Shopify, replace {shop} in URLs
        if provider_name == "shopify" and shop_domain:
            provider.authorization_url = provider.authorization_url.replace(
                "{shop}", shop_domain
            )
            provider.token_url = provider.token_url.replace("{shop}", shop_domain)

        # Exchange code for token
        token_response = await provider.exchange_code_for_token(code)

        logger.info(f"OAuth callback successful: {provider_name}")

        return token_response

    async def refresh_token(
        self,
        provider_name: str,
        refresh_token: str
    ) -> Dict[str, Any]:
        """
        Refresh OAuth2 access token

        Args:
            provider_name: OAuth provider
            refresh_token: Refresh token

        Returns:
            {
                "access_token": "new_token",
                "expires_in": 3600,
                ...
            }
        """
        provider = self.get_provider(provider_name)
        token_response = await provider.refresh_access_token(refresh_token)

        logger.info(f"Token refreshed: {provider_name}")

        return token_response

    def calculate_token_expiry(self, expires_in: int) -> datetime:
        """Calculate token expiration datetime"""
        return datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    def list_providers(self) -> List[Dict[str, Any]]:
        """List all configured OAuth2 providers"""
        result = []
        for name, provider in self.providers.items():
            is_configured = bool(provider.client_id and provider.client_secret)
            result.append({
                "name": name,
                "display_name": provider.name,
                "configured": is_configured,
                "scopes": provider.scopes
            })
        return result


# Singleton instance
_oauth2_service_instance: Optional[OAuth2Service] = None


def get_oauth2_service() -> OAuth2Service:
    """Get singleton OAuth2Service instance"""
    global _oauth2_service_instance
    if _oauth2_service_instance is None:
        _oauth2_service_instance = OAuth2Service()
    return _oauth2_service_instance
