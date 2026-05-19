"""FastAPI security dependencies for route protection."""

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.security.jwt import decode_access_token

_bearer = HTTPBearer(auto_error=False)


def _extract_payload(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> dict:
    """Decode JWT and return payload, raising 401 on any failure."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Authentication required"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Token expired"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Invalid token"},
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_auth(
    payload: Annotated[dict, Depends(_extract_payload)],
) -> dict:
    """Dependency: any authenticated staff member (staff or admin)."""
    return payload


def require_admin(
    payload: Annotated[dict, Depends(_extract_payload)],
) -> dict:
    """Dependency: admin role only. Returns 403 for staff role."""
    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Admin role required"},
        )
    return payload


AuthPayload = Annotated[dict, Depends(require_auth)]
AdminPayload = Annotated[dict, Depends(require_admin)]
