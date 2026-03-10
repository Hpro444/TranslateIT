"""
TranslateIt Application

FastAPI application entry point for the TranslateIt translation service.
This module initializes the FastAPI app, registers routes and error handlers,
and starts the uvicorn server.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from project import __version__
from project.config import Configuration
from project.error_handlers import register_exception_handlers
from project.logger import get_logger
from project.routes import router

# Initialize configuration and logger
config = Configuration()
logger = get_logger()

# Create FastAPI application
app = FastAPI(
    title="TranslateIt API",
    description="A multi-language translation service with automatic language detection",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
register_exception_handlers(app)

# Include API router
app.include_router(router, prefix="/api/v1", tags=["translation"])

logger.info(f"TranslateIt API v{__version__} initialized")


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("=" * 60)
    logger.info(f"Starting TranslateIt API v{__version__}")
    logger.info(f"Server: {config.server_host}:{config.server_port}")
    logger.info(f"Debug mode: {config.debug_mode}")
    logger.info(f"Translation provider: {config.translation_provider}")
    logger.info(f"Cache enabled: {config.enable_cache}")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("Shutting down TranslateIt API")


if __name__ == "__main__":
    logger.info(f"Starting uvicorn server on {config.server_host}:{config.server_port}")

    uvicorn.run(
        "app:app",
        host=config.server_host,
        port=config.server_port,
        reload=config.reload,
        log_level=config.log_level.lower(),
    )
