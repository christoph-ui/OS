"""
0711 Console Backend

FastAPI application providing:
- Chat interface (WebSocket)
- MCP management
- Data browsing
- Ingestion triggers

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │  Console Backend (:8080)                                    │
    ├─────────────────────────────────────────────────────────────┤
    │                                                             │
    │  Routes:                                                    │
    │  • WS /ws/chat     - Real-time chat with MCPs              │
    │  • POST /chat      - Single message chat                   │
    │  • GET /mcps       - List available MCPs                   │
    │  • POST /ingest    - Trigger ingestion                     │
    │  • GET /data       - Browse lakehouse data                 │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
"""

import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import config
from .routes import chat, mcps, ingest, data, categories, products, syndicate, mcp_marketplace, tender, stats, smart_onboarding
from .auth import routes as auth_routes
from .auth.store import init_default_users

logging.basicConfig(level=config.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Console backend starting...")

    # Initialize default users (development only)
    if config.debug:
        await init_default_users()
        logger.info("Default users initialized (dev mode)")

    # Initialize platform (use MockPlatform in test mode)
    try:
        if config.testing:
            # Use MockPlatform for testing
            import sys
            from pathlib import Path
            test_fixtures_path = Path(__file__).parent.parent.parent / "tests" / "fixtures"
            if test_fixtures_path.exists():
                sys.path.insert(0, str(test_fixtures_path.parent))

            from tests.fixtures.mock_platform import MockPlatform
            app.state.platform = MockPlatform(
                lakehouse_path=config.lakehouse_path,
                vllm_url=config.vllm_url
            )
            logger.info("MockPlatform initialized (test mode)")
        else:
            # Use real Platform in production
            from core import Platform
            app.state.platform = Platform(
                lakehouse_path=config.lakehouse_path,
                vllm_url=config.vllm_url
            )
            logger.info("Platform initialized")
    except Exception as e:
        logger.warning(f"Platform initialization skipped: {e}")
        app.state.platform = None

    yield

    # Cleanup
    logger.info("Console backend shutting down")


app = FastAPI(
    title="0711 Console",
    description="Chat with your data using AI-powered MCPs",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_routes.router, prefix="/api/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(mcps.router, prefix="/api/mcps", tags=["mcps"])
app.include_router(ingest.router, prefix="/api/ingest", tags=["ingest"])
app.include_router(data.router, prefix="/api/data", tags=["data"])
app.include_router(categories.router, tags=["categories"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(tender.router, prefix="/api/tender", tags=["tender"])
app.include_router(syndicate.router, prefix="/api/syndicate", tags=["syndicate"])
app.include_router(mcp_marketplace.router, prefix="/api/mcp", tags=["mcp-marketplace"])
app.include_router(stats.router, tags=["stats"])  # NEW: Customer stats for MCP Central
app.include_router(smart_onboarding.router, prefix="/api", tags=["smart-onboarding"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "console-backend"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "0711 Console Backend",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "console.backend.main:app",
        host=config.host,
        port=config.port,
        reload=config.debug
    )
