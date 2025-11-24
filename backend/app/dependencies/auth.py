"""Authentication dependencies for FastAPI routes."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient
from app.config import settings
from loguru import logger

security = HTTPBearer()

# JWKS client will be initialized lazily to avoid startup issues
_jwks_client = None

def get_jwks_client():
    """Get or create JWKS client for Supabase JWT verification."""
    global _jwks_client
    if _jwks_client is None:
        # Supabase uses JWT Signing Keys (ES256) instead of legacy HS256
        jwks_url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
        logger.info(f"Initializing JWKS client with URL: {jwks_url}")
        _jwks_client = PyJWKClient(jwks_url)
    return _jwks_client


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Verify Supabase JWT token and extract user_id.

    This dependency validates the JWT token from the Authorization header
    and returns the user_id (sub claim) from the token payload.

    Args:
        credentials: HTTP Bearer token from Authorization header

    Returns:
        str: User ID (UUID) from token payload

    Raises:
        HTTPException: If token is invalid, expired, or missing user_id
    """
    try:
        token = credentials.credentials
        logger.debug(f"Validating JWT token (length: {len(token)})")

        # Get the signing key from JWKS endpoint
        jwks_client = get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # Decode and verify Supabase JWT using public key from JWKS
        # Supabase uses ES256 (Elliptic Curve) for JWT signing
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],  # Supabase uses ES256, not HS256
            options={"verify_aud": False}  # Don't verify audience
        )

        # Extract user ID from 'sub' claim
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("JWT token missing 'sub' claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        logger.info(f"Authenticated user: {user_id}")
        return user_id

    except jwt.ExpiredSignatureError as e:
        logger.warning(f"Expired JWT token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False))
) -> str | None:
    """
    Optional authentication dependency.
    Returns user_id if valid token provided, None otherwise.

    Useful for endpoints that work for both authenticated and anonymous users.
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        jwks_client = get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            options={"verify_aud": False}
        )
        return payload.get("sub")
    except:
        return None
