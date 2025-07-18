from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import logging

from .api.routes import router, initialize_system

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    logger.info("Starting Multi-Agent Development System...")
    await initialize_system()
    logger.info("System initialized successfully")
    yield
    logger.info("Shutting down Multi-Agent Development System...")


app = FastAPI(
    title="Multi-Agent Development System",
    version="1.0.0",
    description="AI-powered multi-agent development workflow system",
    lifespan=lifespan
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

@app.get("/")
async def root():
    return {
        "message": "Multi-Agent Development System API",
        "version": "1.0.0",
        "endpoints": {
            "api": "/api",
            "docs": "/docs",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "multi-agent-dev-system"}
