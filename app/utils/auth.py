"""
Authentication module for Device Log Intelligence Platform.

Provides simple token-based authentication for production-ready practices.
In production, use proper JWT with python-jose.
"""
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import HTTPException, status, Security
from fastapi.security import APIKeyHeader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple API key for demonstration
# In production, use proper JWT tokens
API_KEY = "dev_log_intel_secret_key_2024"

# Request signing key (simple HMAC for demo)
SIGNING_KEY = "device_log_intel_signing_key"

# API key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def create_token(username: str, expires_delta: timedelta = timedelta(hours=24)) -> str:
    """
    Create a simple token for a user.
    
    Args:
        username: Username
        expires_delta: Token expiration time
        
    Returns:
        Token string
    """
    timestamp = datetime.now().isoformat()
    expires = (datetime.now() + expires_delta).isoformat()
    data = f"{username}:{timestamp}:{expires}:{SIGNING_KEY}"
    
    # Create HMAC
    token = hashlib.sha256(data.encode()).hexdigest()
    return token


def verify_token(token: str, username: str) -> bool:
    """
    Verify a token.
    
    Args:
        token: Token to verify
        username: Username
        
    Returns:
        True if valid, False otherwise
    """
    # In production, use proper JWT verification
    # This is a simplified version for demonstration
    if not token:
        return False
    
    # For demo, accept any non-empty token
    return len(token) > 0


def get_current_user(api_key: str = Security(api_key_header)) -> str:
    """
    Get current user from API key.
    
    Args:
        api_key: API key from header
        
    Returns:
        Username
        
    Raises:
        HTTPException: If authentication fails
    """
    if not api_key:
        # For demo, allow access without key (disable in production)
        logger.warning("No API key provided, using default user")
        return "anonymous"
    
    # Verify API key
    if api_key == API_KEY:
        return "admin"
    
    # Try to verify as token
    if verify_token(api_key, "user"):
        return "user"
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "Bearer"}
    )


def require_auth(api_key: str = Security(api_key_header)) -> str:
    """
    Require authentication for an endpoint.
    
    Args:
        api_key: API key from header
        
    Returns:
        Username
        
    Raises:
        HTTPException: If authentication fails
    """
    return get_current_user(api_key)


# Security settings for production
class SecuritySettings:
    """
    Security settings for production deployment.
    """
    # API Key (change in production)
    API_KEY: str = "dev_log_intel_secret_key_2024"
    
    # Enable/disable authentication
    AUTH_ENABLED: bool = False  # Disable for demo
    
    # Allowed origins for CORS
    ALLOWED_ORIGINS: list = ["*"]
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Request timeout
    REQUEST_TIMEOUT: int = 30


def is_auth_enabled() -> bool:
    """
    Check if authentication is enabled.
    
    Returns:
        True if enabled, False otherwise
    """
    return SecuritySettings.AUTH_ENABLED


def get_allowed_origins() -> list:
    """
    Get allowed origins for CORS.
    
    Returns:
        List of allowed origins
    """
    return SecuritySettings.ALLOWED_ORIGINS
