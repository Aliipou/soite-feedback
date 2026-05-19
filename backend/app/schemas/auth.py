"""Pydantic v2 schemas for authentication endpoints."""

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.security.password import validate_password_policy


class LoginIn(BaseModel):
    """Request body for POST /auth/login."""

    model_config = ConfigDict(strict=True)

    email: EmailStr
    password: str


class TokenOut(BaseModel):
    """Response for login and token refresh."""

    model_config = ConfigDict(strict=True)

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class CreateUserIn(BaseModel):
    """Request body for POST /admin/users — admin only."""

    model_config = ConfigDict(strict=True)

    email: EmailStr
    password: str
    role: str = "staff"

    @field_validator("password")
    @classmethod
    def password_policy(cls, v: str) -> str:
        if not validate_password_policy(v):
            msg = (
                "Password must be at least 12 characters with "
                "at least one uppercase letter and one digit"
            )
            raise ValueError(msg)
        return v

    @field_validator("role")
    @classmethod
    def valid_role(cls, v: str) -> str:
        if v not in ("staff", "admin"):
            msg = "role must be 'staff' or 'admin'"
            raise ValueError(msg)
        return v


class UpdateUserIn(BaseModel):
    """Request body for PATCH /admin/users/{id}."""

    model_config = ConfigDict(strict=True)

    is_active: bool | None = None
    role: str | None = None

    @field_validator("role")
    @classmethod
    def valid_role(cls, v: str | None) -> str | None:
        if v is not None and v not in ("staff", "admin"):
            msg = "role must be 'staff' or 'admin'"
            raise ValueError(msg)
        return v


class UserOut(BaseModel):
    """Staff user as returned to admin panel."""

    model_config = ConfigDict(strict=False, from_attributes=True)

    id: object  # uuid.UUID — avoid strict UUID clash with from_attributes
    email: str
    role: str
    is_active: bool
    last_login_at: object | None = None
    created_at: object
