"""
Device Log Intelligence Platform - Main FastAPI Application

A system that:
- Takes Android logcat logs
- Parses errors and warnings
- Detects patterns
- Displays insights on dashboard

Architecture:
- Frontend (HTML/React) → FastAPI Backend → Log Parser (Python) → Database (SQLite)
"""
import logging
import sys
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler

from app.utils.database import init_db, get_db, get_db_path
from app.models.log_models import Log, ErrorSummary


def setup_logging():
    """
    Setup production-ready logging with file rotation.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    try:
        file_handler = RotatingFileHandler(
            "logs/app.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.INFO)
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    except Exception:
        pass  # Continue without file logging
    
    return logger


logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup: Initialize database
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")
    yield
    # Shutdown: Cleanup if needed
    logger.info("Shutting down application...")


# Create FastAPI app
app = FastAPI(
    title="Device Log Intelligence Platform",
    description="A system that parses Android logcat logs, detects errors and warnings, and displays insights on a dashboard.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Basic health check endpoint.
    Returns the status of the service.
    """
    return {
        "status": "healthy",
        "service": "Device Log Intelligence Platform",
        "timestamp": datetime.now().isoformat(),
        "database": "connected" if get_db_path() else "disconnected"
    }


# Database dependency
def get_database():
    """
    Get database session dependency.
    """
    return Depends(get_db)


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """
    Handle HTTP exceptions.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """
    Handle general exceptions.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "status_code": 500
        }
    )


# Root route - serve dashboard
@app.get("/")
async def root():
    """
    Serve the dashboard HTML page at root.
    """
    return FileResponse("dashboard/index.html")


# Dashboard route (alias)
@app.get("/dashboard")
async def dashboard():
    """
    Serve the dashboard HTML page.
    """
    return FileResponse("dashboard/index.html")


# Include routers
from app.routes.logs import router as logs_router
app.include_router(logs_router, prefix="/api", tags=["logs"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
