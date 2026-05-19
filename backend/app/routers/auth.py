"""Authentication endpoints — login, refresh, logout."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import LoginIn, TokenOut
from app.services import auth as auth_svc

router = APIRouter(prefix="/auth")
limiter = Limiter(key_func=get_remote_address)

_REFRESH_COOKIE = "__Host-refresh_token"


def _set_refresh_cookie(response: Response, token: str) -> None:
    """Set httpOnly refresh token cookie with __Host- prefix security."""
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=True,
        samesite="strict",
        path="/",      # required for __Host- prefix
        max_age=7 * 24 * 3600,
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Clear refresh token cookie."""
    response.delete_cookie(key=_REFRESH_COOKIE, path="/", secure=True, samesite="strict")


@router.post("/login", response_model=TokenOut)
@limiter.limit("5/15minutes")
async def login(
    request: Request,
    body: LoginIn,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenOut:
    """Staff login. Returns access token in body, refresh token as httpOnly cookie."""
    user = await auth_svc.authenticate_user(db, body.email, body.password)
    if user is None:
        # Generic message — never reveal whether email exists
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Invalid credentials"},
        )

    await auth_svc.update_last_login(db, user)
    refresh_token = await auth_svc.create_refresh_token(db, user.id)

    _set_refresh_cookie(response, refresh_token)
    return TokenOut(**auth_svc.build_token_response(user))


@router.post("/refresh", response_model=TokenOut)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenOut:
    """Rotate refresh token. Old token is revoked; new one set in cookie."""
    raw_token = request.cookies.get(_REFRESH_COOKIE)
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Refresh token missing"},
        )

    try:
        user, new_raw = await auth_svc.rotate_refresh_token(db, raw_token)
    except ValueError as exc:
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": str(exc)},
        ) from exc

    _set_refresh_cookie(response, new_raw)
    return TokenOut(**auth_svc.build_token_response(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Revoke refresh token and clear cookie."""
    raw_token = request.cookies.get(_REFRESH_COOKIE)
    if raw_token:
        await auth_svc.revoke_refresh_token(db, raw_token)
    _clear_refresh_cookie(response)
