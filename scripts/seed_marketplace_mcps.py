"""
Seed Marketplace MCPs
Creates initial 20 priority MCPs with complete connection configuration
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from api.database import SessionLocal
from api.models import MCP
import uuid

# Top 20 Priority MCPs with full configuration
PRIORITY_MCPS = [
    # === CRM (4 MCPs) ===
    {
        "name": "salesforce",
        "display_name": "Salesforce",
        "version": "1.0.0",
        "description": "Connect to Salesforce CRM for customer data, leads, opportunities, and sales automation",
        "category": "crm",
        "subcategory": "sales",
        "tags": ["crm", "sales", "enterprise", "cloud"],
        "direction": "bidirectional",
        "model_type": "adapter",
        "capabilities": ["read_contacts", "write_contacts", "read_opportunities", "sync_data"],
        "supported_languages": ["en", "de"],
        "icon": "🌩️",
        "icon_color": "blue",
        "featured": True,
        "verified": True,
        "pricing_model": "free",
        "status": "active",
        "published": True,
        "connection_type": "oauth2",
        "oauth_config": {
            "provider": "salesforce",
            "scopes": ["full", "refresh_token", "offline_access"],
            "authorization_url": "https://login.salesforce.com/services/oauth2/authorize",
            "token_url": "https://login.salesforce.com/services/oauth2/token"
        },
        "api_docs_url": "https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/",
        "setup_instructions": """## Salesforce OAuth Setup

1. Log in to Salesforce as administrator
2. Navigate to **Setup** → **App Manager**
3. Click **New Connected App**
4. Fill in:
   - Connected App Name: `0711 Intelligence`
   - API Name: `0711_intelligence`
   - Contact Email: Your email
5. Enable **OAuth Settings**
6. Callback URL: `https://api.0711.io/api/oauth2/callback/salesforce`
7. Selected OAuth Scopes:
   - Full access (full)
   - Perform requests at any time (refresh_token, offline_access)
8. Click **Save**
9. Copy **Consumer Key** and **Consumer Secret**
10. Paste into 0711 connection wizard

**Security**: OAuth2 with PKCE, token refresh every 2 hours
""",
        "connection_test_endpoint": "{instance_url}/services/data/v57.0/sobjects"
    },

    {
        "name": "hubspot",
        "display_name": "HubSpot CRM",
        "version": "1.0.0",
        "description": "Connect to HubSpot for marketing automation, CRM, and sales pipeline management",
        "category": "crm",
        "subcategory": "marketing",
        "tags": ["crm", "marketing", "automation", "cloud"],
        "direction": "bidirectional",
        "model_type": "adapter",
        "capabilities": ["read_contacts", "write_contacts", "read_deals", "email_campaigns"],
        "supported_languages": ["en", "de"],
        "icon": "🟠",
        "icon_color": "orange",
        "featured": True,
        "verified": True,
        "pricing_model": "free",
        "status": "active",
        "published": True,
        "connection_type": "oauth2",
        "oauth_config": {
            "provider": "hubspot",
            "scopes": ["crm.objects.contacts.read", "crm.objects.companies.read", "crm.objects.deals.read", "files"],
            "authorization_url": "https://app.hubspot.com/oauth/authorize",
            "token_url": "https://api.hubapi.com/oauth/v1/token"
        },
        "api_docs_url": "https://developers.hubspot.com/docs/api/overview",
        "setup_instructions": """## HubSpot OAuth Setup

1. Go to [HubSpot Developer Portal](https://developers.hubspot.com/)
2. Create an app or select existing
3. Navigate to **Auth** tab
4. Set Redirect URL: `https://api.0711.io/api/oauth2/callback/hubspot`
5. Select scopes:
   - CRM: Contacts, Companies, Deals (read/write)
   - Files (read)
6. Copy **Client ID** and **Client Secret**
7. Paste into 0711 connection wizard

**Security**: OAuth2, token refresh every 6 hours
""",
        "connection_test_endpoint": "https://api.hubapi.com/crm/v3/objects/contacts?limit=1"
    },

    # === Finance/Accounting (4 MCPs) ===
    {
        "name": "quickbooks",
        "display_name": "QuickBooks",
        "version": "1.0.0",
        "description": "Connect to QuickBooks for accounting, invoicing, and financial reporting",
        "category": "finance",
        "subcategory": "accounting",
        "tags": ["accounting", "finance", "invoicing", "enterprise"],
        "direction": "bidirectional",
        "model_type": "adapter",
        "capabilities": ["read_invoices", "write_invoices", "read_expenses", "financial_reports"],
        "supported_languages": ["en", "de"],
        "icon": "💚",
        "icon_color": "green",
        "featured": True,
        "verified": True,
        "pricing_model": "free",
        "status": "active",
        "published": True,
        "connection_type": "oauth2",
        "oauth_config": {
            "provider": "quickbooks",
            "scopes": ["com.intuit.quickbooks.accounting"],
            "authorization_url": "https://appcenter.intuit.com/connect/oauth2",
            "token_url": "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
        },
        "api_docs_url": "https://developer.intuit.com/app/developer/qbo/docs/get-started",
        "setup_instructions": """## QuickBooks OAuth Setup

1. Go to [Intuit Developer Portal](https://developer.intuit.com/)
2. Create app → Select **QuickBooks Online API**
3. Configure OAuth:
   - Redirect URI: `https://api.0711.io/api/oauth2/callback/quickbooks`
   - Scope: Accounting
4. Copy **Client ID** and **Client Secret**
5. Paste into 0711 connection wizard

**Note**: Requires QuickBooks Online subscription
""",
        "connection_test_endpoint": "https://quickbooks.api.intuit.com/v3/company/{realmId}/companyinfo/{realmId}"
    },

    {
        "name": "xero",
        "display_name": "Xero",
        "version": "1.0.0",
        "description": "Connect to Xero for cloud accounting, invoicing, and expense management",
        "category": "finance",
        "subcategory": "accounting",
        "tags": ["accounting", "finance", "cloud", "invoicing"],
        "direction": "bidirectional",
        "model_type": "adapter",
        "capabilities": ["read_transactions", "write_transactions", "read_contacts", "bank_reconciliation"],
        "supported_languages": ["en", "de"],
        "icon": "💙",
        "icon_color": "blue",
        "featured": True,
        "verified": True,
        "pricing_model": "free",
        "status": "active",
        "published": True,
        "connection_type": "oauth2",
        "oauth_config": {
            "provider": "xero",
            "scopes": ["offline_access", "accounting.transactions.read", "accounting.contacts.read", "accounting.settings.read"],
            "authorization_url": "https://login.xero.com/identity/connect/authorize",
            "token_url": "https://identity.xero.com/connect/token"
        },
        "api_docs_url": "https://developer.xero.com/documentation/",
        "setup_instructions": """## Xero OAuth Setup

1. Go to [Xero Developer Portal](https://developer.xero.com/myapps/)
2. Create new app → **Web app**
3. Set Redirect URI: `https://api.0711.io/api/oauth2/callback/xero`
4. Select scopes:
   - Accounting: Transactions, Contacts, Settings (read)
   - offline_access (for refresh tokens)
5. Copy **Client ID** and **Client Secret**
6. Paste into 0711 connection wizard

**Note**: Requires Xero subscription
""",
        "connection_test_endpoint": "https://api.xero.com/api.xro/2.0/Organisation"
    },

    {
        "name": "stripe",
        "display_name": "Stripe",
        "version": "1.0.0",
        "description": "Connect to Stripe for payment processing, subscriptions, and revenue analytics",
        "category": "finance",
        "subcategory": "payments",
        "tags": ["payments", "billing", "subscriptions", "api"],
        "direction": "bidirectional",
        "model_type": "adapter",
        "capabilities": ["read_payments", "read_subscriptions", "refund_payments", "revenue_analytics"],
        "supported_languages": ["en", "de"],
        "icon": "💳",
        "icon_color": "purple",
        "featured": True,
        "verified": True,
        "pricing_model": "free",
        "status": "active",
        "published": True,
        "connection_type": "api_key",
        "api_docs_url": "https://stripe.com/docs/api",
        "setup_instructions": """## Stripe API Key Setup

1. Log in to [Stripe Dashboard](https://dashboard.stripe.com/)
2. Navigate to **Developers** → **API keys**
3. Copy **Secret key** (starts with `sk_`)
4. Paste into 0711 connection wizard

**Security**:
- Use restricted keys for production
- Never commit keys to version control
- Rotate keys quarterly

**Test Mode**: Use `sk_test_` keys for testing
""",
        "connection_test_endpoint": "https://api.stripe.com/v1/balance"
    },

    {
        "name": "datev",
        "display_name": "DATEV",
        "version": "1.0.0",
        "description": "Connect to DATEV for German tax compliance, payroll, and accounting (DSGVO compliant)",
        "category": "finance",
        "subcategory": "tax",
        "tags": ["accounting", "tax", "germany", "compliance", "dsgvo"],
        "direction": "bidirectional",
        "model_type": "adapter",
        "capabilities": ["read_financial_data", "tax_reports", "payroll", "elster_export"],
        "supported_languages": ["de"],
        "icon": "🇩🇪",
        "icon_color": "black",
        "featured": True,
        "verified": True,
        "pricing_model": "free",
        "status": "active",
        "published": True,
        "connection_type": "api_key",
        "api_docs_url": "https://developer.datev.de/",
        "setup_instructions": """## DATEV API Key Setup

1. Login zu [DATEV SmartLogin](https://www.datev.de/smartlogin)
2. Navigate zu **Entwickler** → **API Zugang**
3. Neuen API-Schlüssel erstellen
4. Bereiche auswählen:
   - Rechnungswesen
   - Lohn & Gehalt
   - ELSTER
5. API-Schlüssel kopieren
6. In 0711 Verbindungs-Wizard einfügen

**Datenschutz**: DSGVO-konform, Daten bleiben in Deutschland
""",
        "connection_test_endpoint": "https://api.datev.de/v1/ping"
    },

    # === Communication (4 MCPs) ===
    {
        "name": "slack",
        "display_name": "Slack",
        "version": "1.0.0",
        "description": "Connect to Slack for team communication, file sharing, and workflow automation",
        "category": "communication",
        "subcategory": "messaging",
        "tags": ["communication", "messaging", "collaboration", "cloud"],
        "direction": "bidirectional",
        "model_type": "adapter",
        "capabilities": ["read_messages", "send_messages", "read_files", "manage_channels"],
        "supported_languages": ["en", "de"],
        "icon": "💬",
        "icon_color": "purple",
        "featured": True,
        "verified": True,
        "pricing_model": "free",
        "status": "active",
        "published": True,
        "connection_type": "oauth2",
        "oauth_config": {
            "provider": "slack",
            "scopes": ["channels:read", "chat:write", "files:read", "users:read", "team:read"],
            "authorization_url": "https://slack.com/oauth/v2/authorize",
            "token_url": "https://slack.com/api/oauth.v2.access"
        },
        "api_docs_url": "https://api.slack.com/",
        "setup_instructions": """## Slack OAuth Setup

1. Go to [Slack API Portal](https://api.slack.com/apps)
2. Create new app → **From scratch**
3. Select workspace
4. Navigate to **OAuth & Permissions**
5. Add Redirect URL: `https://api.0711.io/api/oauth2/callback/slack`
6. Add Bot Token Scopes:
   - channels:read
   - chat:write
   - files:read
   - users:read
7. Copy **Client ID** and **Client Secret**
8. Paste into 0711 connection wizard

**Note**: Requires workspace admin approval
""",
        "connection_test_endpoint": "https://slack.com/api/auth.test"
    },

    {
        "name": "google-workspace",
        "display_name": "Google Workspace",
        "version": "1.0.0",
        "description": "Connect to Google Workspace for Gmail, Drive, Calendar, and Meet integration",
        "category": "communication",
        "subcategory": "collaboration",
        "tags": ["email", "cloud", "collaboration", "storage"],
        "direction": "bidirectional",
        "model_type": "adapter",
        "capabilities": ["read_emails", "read_drive", "read_calendar", "manage_docs"],
        "supported_languages": ["en", "de"],
        "icon": "🔵",
        "icon_color": "blue",
        "featured": True,
        "verified": True,
        "pricing_model": "free",
        "status": "active",
        "published": True,
        "connection_type": "oauth2",
        "oauth_config": {
            "provider": "google",
            "scopes": [
                "https://www.googleapis.com/auth/drive.readonly",
                "https://www.googleapis.com/auth/calendar.readonly",
                "https://www.googleapis.com/auth/gmail.readonly",
                "email",
                "profile"
            ],
            "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token"
        },
        "api_docs_url": "https://developers.google.com/workspace",
        "setup_instructions": """## Google Workspace OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project or select existing
3. Enable APIs:
   - Gmail API
   - Google Drive API
   - Google Calendar API
4. Configure OAuth consent screen
5. Create **OAuth client ID** → Web application
6. Add Authorized redirect URI: `https://api.0711.io/api/oauth2/callback/google`
7. Copy **Client ID** and **Client Secret**
8. Paste into 0711 connection wizard

**Note**: May require Google Workspace admin approval for organization-wide deployment
""",
        "connection_test_endpoint": "https://www.googleapis.com/oauth2/v1/userinfo"
    },

    {
        "name": "microsoft-365",
        "display_name": "Microsoft 365",
        "version": "1.0.0",
        "description": "Connect to Microsoft 365 for Outlook, OneDrive, Teams, and SharePoint integration",
        "category": "communication",
        "subcategory": "collaboration",
        "tags": ["email", "cloud", "collaboration", "enterprise"],
        "direction": "bidirectional",
        "model_type": "adapter",
        "capabilities": ["read_emails", "read_onedrive", "read_calendar", "teams_integration"],
        "supported_languages": ["en", "de"],
        "icon": "Ⓜ️",
        "icon_color": "blue",
        "featured": True,
        "verified": True,
        "pricing_model": "free",
        "status": "active",
        "published": True,
        "connection_type": "oauth2",
        "oauth_config": {
            "provider": "microsoft",
            "scopes": ["Files.Read.All", "Calendars.Read", "Mail.Read", "User.Read", "offline_access"],
            "authorization_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        },
        "api_docs_url": "https://learn.microsoft.com/en-us/graph/overview",
        "setup_instructions": """## Microsoft 365 OAuth Setup

1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click **New registration**
4. Set Redirect URI: `https://api.0711.io/api/oauth2/callback/microsoft`
5. Navigate to **Certificates & secrets** → Create new client secret
6. Navigate to **API permissions** → Add:
   - Microsoft Graph: Files.Read.All, Mail.Read, Calendars.Read, User.Read
7. Grant admin consent (if required)
8. Copy **Application (client) ID** and **Client secret**
9. Paste into 0711 connection wizard

**Note**: Requires Azure AD tenant
""",
        "connection_test_endpoint": "https://graph.microsoft.com/v1.0/me"
    },

    # === DevOps (2 MCPs) ===
    {
        "name": "github",
        "display_name": "GitHub",
        "version": "1.0.0",
        "description": "Connect to GitHub for code repositories, issues, pull requests, and CI/CD workflows",
        "category": "devops",
        "subcategory": "version_control",
        "tags": ["git", "devops", "ci_cd", "code"],
        "direction": "bidirectional",
        "model_type": "adapter",
        "capabilities": ["read_repos", "read_issues", "read_prs", "create_issues"],
        "supported_languages": ["en"],
        "icon": "🐙",
        "icon_color": "black",
        "featured": True,
        "verified": True,
        "pricing_model": "free",
        "status": "active",
        "published": True,
        "connection_type": "oauth2",
        "oauth_config": {
            "provider": "github",
            "scopes": ["repo", "read:org", "read:user"],
            "authorization_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token"
        },
        "api_docs_url": "https://docs.github.com/en/rest",
        "setup_instructions": """## GitHub OAuth Setup

1. Go to [GitHub Settings](https://github.com/settings/developers)
2. Navigate to **OAuth Apps** → **New OAuth App**
3. Fill in:
   - Application name: `0711 Intelligence`
   - Homepage URL: `https://0711.io`
   - Authorization callback URL: `https://api.0711.io/api/oauth2/callback/github`
4. Click **Register application**
5. Copy **Client ID** and generate **Client Secret**
6. Paste into 0711 connection wizard

**Note**: For organization access, organization admin must approve
""",
        "connection_test_endpoint": "https://api.github.com/user"
    },

    {
        "name": "gitlab",
        "display_name": "GitLab",
        "version": "1.0.0",
        "description": "Connect to GitLab for DevOps lifecycle management, CI/CD, and code collaboration",
        "category": "devops",
        "subcategory": "version_control",
        "tags": ["git", "devops", "ci_cd", "code"],
        "direction": "bidirectional",
        "model_type": "adapter",
        "capabilities": ["read_repos", "read_issues", "read_merge_requests", "ci_cd_pipelines"],
        "supported_languages": ["en"],
        "icon": "🦊",
        "icon_color": "orange",
        "featured": True,
        "verified": True,
        "pricing_model": "free",
        "status": "active",
        "published": True,
        "connection_type": "oauth2",
        "oauth_config": {
            "provider": "gitlab",
            "scopes": ["api", "read_user", "read_repository"],
            "authorization_url": "https://gitlab.com/oauth/authorize",
            "token_url": "https://gitlab.com/oauth/token"
        },
        "api_docs_url": "https://docs.gitlab.com/ee/api/",
        "setup_instructions": """## GitLab OAuth Setup

1. Go to [GitLab Applications](https://gitlab.com/-/profile/applications)
2. Create new application:
   - Name: `0711 Intelligence`
   - Redirect URI: `https://api.0711.io/api/oauth2/callback/gitlab`
   - Scopes: api, read_user, read_repository
3. Click **Save application**
4. Copy **Application ID** and **Secret**
5. Paste into 0711 connection wizard

**Note**: For self-hosted GitLab, configure custom OAuth endpoints
""",
        "connection_test_endpoint": "https://gitlab.com/api/v4/user"
    },

    # === Design & Collaboration (1 MCP) ===
    {
        "name": "figma",
        "display_name": "Figma",
        "version": "1.0.0",
        "description": "Connect to Figma for design collaboration, prototyping, and asset management",
        "category": "design",
        "subcategory": "collaboration",
        "tags": ["design", "prototyping", "collaboration", "cloud"],
        "direction": "bidirectional",
        "model_type": "adapter",
        "capabilities": ["read_files", "export_assets", "read_comments", "design_analytics"],
        "supported_languages": ["en"],
        "icon": "🎨",
        "icon_color": "purple",
        "featured": True,
        "verified": True,
        "pricing_model": "free",
        "status": "active",
        "published": True,
        "connection_type": "api_key",
        "api_docs_url": "https://www.figma.com/developers/api",
        "setup_instructions": """## Figma API Key Setup

1. Log in to [Figma](https://www.figma.com/)
2. Click on your profile → **Settings**
3. Scroll to **Personal access tokens**
4. Click **Create new token**
5. Enter token description: `0711 Intelligence`
6. Select scopes:
   - File content (read)
   - File comments (read)
7. Click **Create token**
8. Copy the token (starts with `figd_`)
9. Paste into 0711 connection wizard

**Security**:
- Never share your personal access token
- Rotate tokens every 90 days
- Use separate tokens for different integrations

**Permissions**: Token inherits your Figma permissions (team access, file access)
""",
        "connection_test_endpoint": "https://api.figma.com/v1/me"
    },

    # === AI Models (1 MCP) ===
    {
        "name": "meta-andromeda",
        "display_name": "Meta Andromeda",
        "version": "1.0.0",
        "description": "Connect to Meta's Andromeda AI model for advanced reasoning, multimodal understanding, and enterprise AI tasks",
        "category": "ai",
        "subcategory": "llm",
        "tags": ["ai", "llm", "meta", "reasoning", "multimodal"],
        "direction": "output",
        "model_type": "full_model",
        "capabilities": ["text_generation", "multimodal_understanding", "reasoning", "code_generation"],
        "supported_languages": ["en", "de", "fr", "es", "it"],
        "icon": "🌌",
        "icon_color": "blue",
        "featured": True,
        "verified": True,
        "pricing_model": "usage_based",
        "status": "active",
        "published": True,
        "connection_type": "api_key",
        "api_docs_url": "https://ai.meta.com/andromeda/docs",
        "setup_instructions": """## Meta Andromeda API Setup

### Prerequisites:
- Meta AI Platform account
- Approved enterprise access (contact Meta sales)

### Setup Steps:
1. Go to [Meta AI Platform](https://ai.meta.com/platform)
2. Navigate to **API Keys** section
3. Click **Generate New API Key**
4. Select usage tier:
   - Development (free tier, rate-limited)
   - Production (pay-as-you-go)
   - Enterprise (custom pricing)
5. Configure model access:
   - **Andromeda-405B** (flagship model)
   - **Andromeda-70B** (cost-effective)
   - **Andromeda-13B** (fast inference)
6. Copy API key (starts with `meta_`)
7. Paste into 0711 connection wizard

**Pricing**:
- Development: Free (1M tokens/month)
- Production: $0.002/1K tokens (input), $0.006/1K tokens (output)
- Enterprise: Custom pricing with volume discounts

**Features**:
- Context window: 128K tokens
- Multimodal: Text, images, code
- Reasoning: Advanced chain-of-thought
- Safety: Built-in content moderation

**Use Cases**:
- Complex reasoning tasks
- Multimodal data analysis
- Code generation & review
- Document understanding
- Enterprise chatbots

**Security**:
- API keys are scoped to your organization
- All data encrypted in transit (TLS 1.3)
- GDPR & SOC 2 compliant
- Data not used for model training (enterprise tier)

**Rate Limits**:
- Development: 60 requests/minute
- Production: 600 requests/minute
- Enterprise: Custom limits

**Support**: 24/7 enterprise support available
""",
        "connection_test_endpoint": "https://api.meta.com/v1/andromeda/health"
    },

    # === E-commerce (2 MCPs) ===
    {
        "name": "shopify",
        "display_name": "Shopify",
        "version": "1.0.0",
        "description": "Connect to Shopify for e-commerce store management, products, orders, and inventory",
        "category": "ecommerce",
        "subcategory": "platform",
        "tags": ["ecommerce", "store", "products", "cloud"],
        "direction": "bidirectional",
        "model_type": "adapter",
        "capabilities": ["read_products", "read_orders", "read_customers", "inventory_sync"],
        "supported_languages": ["en", "de"],
        "icon": "🛍️",
        "icon_color": "green",
        "featured": True,
        "verified": True,
        "pricing_model": "free",
        "status": "active",
        "published": True,
        "connection_type": "oauth2",
        "oauth_config": {
            "provider": "shopify",
            "scopes": ["read_products", "read_orders", "read_customers", "read_inventory"],
            "authorization_url": "https://{shop}.myshopify.com/admin/oauth/authorize",
            "token_url": "https://{shop}.myshopify.com/admin/oauth/access_token"
        },
        "api_docs_url": "https://shopify.dev/docs/api",
        "setup_instructions": """## Shopify OAuth Setup

1. Go to Shopify Partner Dashboard
2. Create new app or select existing
3. Configure app:
   - App URL: `https://0711.io`
   - Allowed redirection URL: `https://api.0711.io/api/oauth2/callback/shopify`
4. Select scopes:
   - read_products
   - read_orders
   - read_customers
   - read_inventory
5. Copy **API key** and **API secret key**
6. Paste into 0711 connection wizard
7. Enter your **Shop domain** (e.g., mystore.myshopify.com)

**Note**: Requires Shopify Partner account
""",
        "connection_test_endpoint": "https://{shop}.myshopify.com/admin/api/2024-01/shop.json"
    },

    # === Databases (4 MCPs) ===
    {
        "name": "postgresql",
        "display_name": "PostgreSQL",
        "version": "1.0.0",
        "description": "Connect to PostgreSQL database for data queries, analytics, and reporting",
        "category": "database",
        "subcategory": "relational",
        "tags": ["database", "sql", "relational", "open_source"],
        "direction": "input",
        "model_type": "adapter",
        "capabilities": ["read_data", "execute_queries", "schema_introspection"],
        "supported_languages": ["en"],
        "icon": "🐘",
        "icon_color": "blue",
        "featured": True,
        "verified": True,
        "pricing_model": "free",
        "status": "active",
        "published": True,
        "connection_type": "database",
        "api_docs_url": "https://www.postgresql.org/docs/",
        "setup_instructions": """## PostgreSQL Connection Setup

Enter your database connection details:

1. **Host**: Database server address (e.g., localhost or db.example.com)
2. **Port**: Usually 5432
3. **Database**: Database name
4. **Username**: Database user with read access
5. **Password**: User password
6. **SSL Mode**:
   - `prefer` (default) - Use SSL if available
   - `require` - SSL required
   - `disable` - No SSL

**Security Best Practices**:
- Use read-only user for analytics
- Enable SSL in production
- Restrict access by IP address
- Rotate credentials quarterly

**Test Connection**: We'll run `SELECT 1` to verify connectivity
""",
        "connection_test_endpoint": "SELECT 1"
    },

    {
        "name": "mysql",
        "display_name": "MySQL",
        "version": "1.0.0",
        "description": "Connect to MySQL database for data queries, analytics, and reporting",
        "category": "database",
        "subcategory": "relational",
        "tags": ["database", "sql", "relational", "open_source"],
        "direction": "input",
        "model_type": "adapter",
        "capabilities": ["read_data", "execute_queries", "schema_introspection"],
        "supported_languages": ["en"],
        "icon": "🐬",
        "icon_color": "blue",
        "featured": True,
        "verified": True,
        "pricing_model": "free",
        "status": "active",
        "published": True,
        "connection_type": "database",
        "api_docs_url": "https://dev.mysql.com/doc/",
        "setup_instructions": """## MySQL Connection Setup

Enter your database connection details:

1. **Host**: Database server address
2. **Port**: Usually 3306
3. **Database**: Database name
4. **Username**: Database user
5. **Password**: User password
6. **SSL Mode**: Enable for encrypted connections

**Compatible With**:
- MySQL 5.7+
- MariaDB 10.3+
- Amazon RDS MySQL
- Azure Database for MySQL

**Test Connection**: We'll run `SELECT 1` to verify
""",
        "connection_test_endpoint": "SELECT 1"
    },

    {
        "name": "mongodb",
        "display_name": "MongoDB",
        "version": "1.0.0",
        "description": "Connect to MongoDB for NoSQL document queries and analytics",
        "category": "database",
        "subcategory": "nosql",
        "tags": ["database", "nosql", "document", "cloud"],
        "direction": "input",
        "model_type": "adapter",
        "capabilities": ["read_documents", "aggregate_queries", "schema_inference"],
        "supported_languages": ["en"],
        "icon": "🍃",
        "icon_color": "green",
        "featured": True,
        "verified": True,
        "pricing_model": "free",
        "status": "active",
        "published": True,
        "connection_type": "database",
        "api_docs_url": "https://www.mongodb.com/docs/",
        "setup_instructions": """## MongoDB Connection Setup

### MongoDB Atlas (Cloud):
1. Go to [MongoDB Atlas](https://cloud.mongodb.com/)
2. Navigate to **Database Access** → Create user
3. Navigate to **Network Access** → Add IP (0.0.0.0/0 for testing)
4. Get connection string from **Connect** button
5. Format: `mongodb+srv://username:password@cluster.mongodb.net/database`

### Self-Hosted:
- **Host**: MongoDB server address
- **Port**: Usually 27017
- **Database**: Database name
- **Username**: Database user
- **Password**: User password

**Test Connection**: We'll run `db.runCommand({ping: 1})`
""",
        "connection_test_endpoint": "db.runCommand({ping: 1})"
    },

    {
        "name": "redis",
        "display_name": "Redis",
        "version": "1.0.0",
        "description": "Connect to Redis for caching, session management, and real-time analytics",
        "category": "database",
        "subcategory": "cache",
        "tags": ["database", "cache", "key_value", "in_memory"],
        "direction": "input",
        "model_type": "adapter",
        "capabilities": ["read_keys", "cache_analytics", "monitor_performance"],
        "supported_languages": ["en"],
        "icon": "🔴",
        "icon_color": "red",
        "featured": False,
        "verified": True,
        "pricing_model": "free",
        "status": "active",
        "published": True,
        "connection_type": "database",
        "api_docs_url": "https://redis.io/docs/",
        "setup_instructions": """## Redis Connection Setup

Enter your Redis connection details:

1. **Host**: Redis server address
2. **Port**: Usually 6379
3. **Database**: Database number (0-15)
4. **Password**: Redis password (if configured)
5. **SSL**: Enable for encrypted connections

**Compatible With**:
- Redis 6.0+
- Redis Cloud
- Amazon ElastiCache
- Azure Cache for Redis

**Test Connection**: We'll run `PING`
""",
        "connection_test_endpoint": "PING"
    },

    # === Data Platforms (2 MCPs) ===
    {
        "name": "snowflake",
        "display_name": "Snowflake",
        "version": "1.0.0",
        "description": "Connect to Snowflake data warehouse for enterprise analytics and data processing",
        "category": "data",
        "subcategory": "warehouse",
        "tags": ["data_warehouse", "analytics", "cloud", "enterprise"],
        "direction": "input",
        "model_type": "adapter",
        "capabilities": ["read_tables", "execute_sql", "data_sharing"],
        "supported_languages": ["en"],
        "icon": "❄️",
        "icon_color": "blue",
        "featured": True,
        "verified": True,
        "pricing_model": "free",
        "status": "active",
        "published": True,
        "connection_type": "api_key",
        "api_docs_url": "https://docs.snowflake.com/",
        "setup_instructions": """## Snowflake Connection Setup

### Option 1: Username/Password
1. **Account**: Your Snowflake account identifier (e.g., xy12345.us-east-1)
2. **Username**: Snowflake username
3. **Password**: User password
4. **Warehouse**: Compute warehouse name
5. **Database**: Default database
6. **Schema**: Default schema

### Option 2: Key Pair Authentication (Recommended)
1. Generate RSA key pair:
   ```bash
   openssl genrsa -out snowflake_key.pem 2048
   openssl rsa -in snowflake_key.pem -pubout -out snowflake_key.pub
   ```
2. Upload public key to Snowflake user
3. Use private key for authentication

**Test Connection**: We'll run `SELECT CURRENT_VERSION()`
""",
        "connection_test_endpoint": "SELECT CURRENT_VERSION()"
    },

    {
        "name": "bigquery",
        "display_name": "Google BigQuery",
        "version": "1.0.0",
        "description": "Connect to Google BigQuery for serverless data warehouse and analytics",
        "category": "data",
        "subcategory": "warehouse",
        "tags": ["data_warehouse", "analytics", "google_cloud", "serverless"],
        "direction": "input",
        "model_type": "adapter",
        "capabilities": ["read_tables", "execute_sql", "ml_models"],
        "supported_languages": ["en"],
        "icon": "📊",
        "icon_color": "blue",
        "featured": True,
        "verified": True,
        "pricing_model": "free",
        "status": "active",
        "published": True,
        "connection_type": "service_account",
        "api_docs_url": "https://cloud.google.com/bigquery/docs",
        "setup_instructions": """## BigQuery Service Account Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select project or create new one
3. Navigate to **IAM & Admin** → **Service Accounts**
4. Click **Create Service Account**:
   - Name: `0711-intelligence`
   - Description: `BigQuery access for 0711 platform`
5. Grant roles:
   - BigQuery Data Viewer
   - BigQuery Job User
6. Click **Done**
7. Click on service account → **Keys** → **Add Key** → **JSON**
8. Download JSON key file
9. Upload to 0711 connection wizard

**Security**: Store JSON key securely, never commit to version control
""",
        "connection_test_endpoint": "SELECT 1"
    }
]


def seed_mcps():
    """Seed database with priority MCPs"""
    db = SessionLocal()

    try:
        print(f"🌱 Seeding {len(PRIORITY_MCPS)} priority MCPs...")

        created_count = 0
        updated_count = 0

        for mcp_data in PRIORITY_MCPS:
            # Check if MCP already exists
            existing = db.query(MCP).filter(MCP.name == mcp_data["name"]).first()

            if existing:
                # Update existing MCP
                for key, value in mcp_data.items():
                    setattr(existing, key, value)
                updated_count += 1
                print(f"   ✓ Updated: {mcp_data['display_name']}")
            else:
                # Create new MCP
                mcp = MCP(
                    id=uuid.uuid4(),
                    **mcp_data
                )
                db.add(mcp)
                created_count += 1
                print(f"   ✅ Created: {mcp_data['display_name']}")

        db.commit()

        print(f"\n✅ Seeding complete!")
        print(f"   Created: {created_count}")
        print(f"   Updated: {updated_count}")
        print(f"   Total: {len(PRIORITY_MCPS)}")

    except Exception as e:
        print(f"❌ Error seeding MCPs: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_mcps()
