"""
Reusable authentication middleware for FastMCP servers.

This module provides JWT (Bearer) and API key authentication middleware
that can be easily integrated into any FastMCP server.
"""

import os
import jwt
from fastapi import Request
from fastapi.responses import JSONResponse
from typing import Optional

# Environment variable configuration
JWT_SECRET = os.getenv("MCP_JWT_SECRET")
API_KEY = os.getenv("MCP_API_KEY")
PROTECT_HEALTH = os.getenv("MCP_PROTECT_HEALTH", "false").lower() in ("true", "1", "yes")
JWT_AUDIENCE = os.getenv("MCP_JWT_AUDIENCE")
JWT_ISSUER = os.getenv("MCP_JWT_ISSUER")
JWT_LEEWAY = int(os.getenv("MCP_JWT_LEEWAY", "30"))


def install_auth(app):
    """
    Install authentication middleware on a FastAPI app.
    
    This middleware supports two authentication methods:
    1. API Key: X-API-Key header matching MCP_API_KEY env var
    2. JWT: Authorization: Bearer <token> with HS256 validation
    
    The /health endpoint is excluded by default unless MCP_PROTECT_HEALTH=true.
    
    Args:
        app: FastAPI application instance to install middleware on
    """
    
    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        path = request.url.path
        
        # Skip auth for health endpoint unless explicitly protected
        if path == "/health" and not PROTECT_HEALTH:
            return await call_next(request)
        
        # Check for API key authentication
        api_key = request.headers.get("X-API-Key")
        if API_KEY and api_key and api_key == API_KEY:
            return await call_next(request)
        
        # Check for JWT authentication
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer ") and JWT_SECRET:
            token = auth_header.split(" ", 1)[1]
            try:
                # Only validate audience and issuer if they are set
                decode_kwargs = {
                    "token": token,
                    "key": JWT_SECRET,
                    "algorithms": ["HS256"],
                    "leeway": JWT_LEEWAY,
                }
                
                if JWT_AUDIENCE:
                    decode_kwargs["audience"] = JWT_AUDIENCE
                if JWT_ISSUER:
                    decode_kwargs["issuer"] = JWT_ISSUER
                
                claims = jwt.decode(**decode_kwargs)
                # Store claims in request state for potential use by handlers
                request.state.jwt_claims = claims
                return await call_next(request)
            except jwt.ExpiredSignatureError:
                return JSONResponse(
                    {"error": "Token expired"}, 
                    status_code=401
                )
            except jwt.InvalidTokenError as e:
                return JSONResponse(
                    {"error": f"Invalid token: {str(e)}"}, 
                    status_code=401
                )
            except Exception as e:
                return JSONResponse(
                    {"error": f"Token validation failed: {str(e)}"}, 
                    status_code=401
                )
        
        # No valid authentication found
        return JSONResponse(
            {"error": "Unauthorized. Provide X-API-Key or Authorization: Bearer <token>"}, 
            status_code=401
        )


def create_jwt_token(
    subject: str,
    secret: str,
    audience: Optional[str] = None,
    issuer: Optional[str] = None,
    expires_in_seconds: int = 3600,
    **additional_claims
) -> str:
    """
    Create a JWT token for testing or client use.
    
    Args:
        subject: Subject claim (sub)
        secret: Secret key for signing
        audience: Audience claim (aud)
        issuer: Issuer claim (iss)
        expires_in_seconds: Token expiration time in seconds
        **additional_claims: Additional claims to include
        
    Returns:
        Encoded JWT token string
    """
    import time
    
    now = int(time.time())
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + expires_in_seconds,
        **additional_claims
    }
    
    if audience:
        payload["aud"] = audience
    if issuer:
        payload["iss"] = issuer
    
    return jwt.encode(payload, secret, algorithm="HS256")
