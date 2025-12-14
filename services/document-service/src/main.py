"""LMA Synapse Document Service - FastAPI Application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .config import settings
from .database.jobs import init_db
from .api.routes.upload import router as upload_router

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event handler"""
    # Startup
    logger.info("Initializing LMA Synapse Document Service...")
    await init_db()
    logger.info("Database initialized")
    logger.info(f"Gemini API configured with models: {settings.GEMINI_FLASH_MODEL}, {settings.GEMINI_PRO_MODEL}")
    yield
    # Shutdown
    logger.info("Shutting down...")

# Create FastAPI app
app = FastAPI(
    title="LMA Synapse Document Service",
    description="AI-powered data extraction for loan documents",
    version="1.0.0-mvp",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For MVP - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload_router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "LMA Synapse Document Service",
        "version": "1.0.0-mvp",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "gemini_configured": bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        workers=settings.API_WORKERS
    )
