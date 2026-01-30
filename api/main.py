"""
0711 Control Plane API
Main FastAPI application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from .config import settings
from .database import engine, Base

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Customer Management & Billing System for 0711 Intelligence",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting 0711 Control Plane API")
    logger.info(f"Version: {settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")

    # Create database tables in debug mode
    if settings.debug:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")

    # Start background job scheduler (disabled for now)
    # from .scheduler import start_scheduler
    # start_scheduler()
    # logger.info("Background scheduler started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down 0711 Control Plane API")

    # Stop background job scheduler (disabled)
    # from .scheduler import stop_scheduler
    # stop_scheduler()
    # logger.info("Background scheduler stopped")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Import and include routers
from .routes import (
    auth,
    users,
    partners,
    subscriptions,
    deployments,
    webhooks,
    admin,
    experts,
    mcps,
    mcp_developers,
    workflows,
    workflow_developers,
    engagements,
    tasks,
    onboarding,
    upload,
    upload_async,
    deployment_ws,
    progress_ws,
    ingestion,
    minio_browser,
    realtime_analysis,
    data_value_report,
    claude_data_analyst,
    expert_auth,
    medusa,
    connections,
    orchestrator,
    marketplace,
    approvals
)

# Control Plane routers (customer management & billing)
app.include_router(auth.router, prefix=f"{settings.api_prefix}/auth", tags=["auth"])
app.include_router(users.router, tags=["users"])  # User management (team members)
app.include_router(partners.router, tags=["partners"])  # Partner/agency management
app.include_router(subscriptions.router, prefix=f"{settings.api_prefix}/subscriptions", tags=["subscriptions"])
app.include_router(deployments.router, prefix=f"{settings.api_prefix}/deployments", tags=["deployments"])
app.include_router(webhooks.router, prefix=f"{settings.api_prefix}/webhooks", tags=["webhooks"])
app.include_router(admin.router, prefix=f"{settings.api_prefix}/admin", tags=["admin"])
app.include_router(onboarding.router, tags=["onboarding"])
app.include_router(upload.router, tags=["upload"])
app.include_router(upload_async.router, tags=["upload-async"])
app.include_router(deployment_ws.router, prefix="/api", tags=["deployment-ws"])
app.include_router(progress_ws.router, prefix="/api", tags=["progress-ws"])
app.include_router(ingestion.router, tags=["ingestion"])
app.include_router(minio_browser.router, tags=["minio"])
app.include_router(realtime_analysis.router, tags=["analysis"])
app.include_router(data_value_report.router, tags=["reports"])
app.include_router(claude_data_analyst.router, tags=["claude-analysis"])

# Expert authentication
app.include_router(expert_auth.router, tags=["expert-auth"])

# Medusa
app.include_router(medusa.router, prefix=f"{settings.api_prefix}/medusa", tags=["medusa"])

# Marketplace routers (experts & MCPs & Workflows)
app.include_router(experts.router, prefix=f"{settings.api_prefix}/experts", tags=["experts"])
app.include_router(mcps.router, prefix=f"{settings.api_prefix}/mcps", tags=["mcps"])
app.include_router(mcp_developers.router, tags=["mcp-developers"])  # MCP developer portal
app.include_router(workflows.router, tags=["workflows"])  # Workflow marketplace
app.include_router(workflow_developers.router, tags=["workflow-developers"])  # Workflow developer portal
app.include_router(engagements.router, prefix=f"{settings.api_prefix}/engagements", tags=["engagements"])
app.include_router(tasks.router, prefix=f"{settings.api_prefix}/tasks", tags=["tasks"])

# Orchestrator & Marketplace (NEW)
app.include_router(orchestrator.router, tags=["orchestrator"])
app.include_router(marketplace.router, tags=["marketplace"])
app.include_router(approvals.router, tags=["approvals"])

# Connection Management (MCP Integrations)
app.include_router(connections.router, tags=["connections"])


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Catch-all exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
