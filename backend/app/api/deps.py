from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import UnauthorizedError
from app.core.logging import get_logger
from app.core.security import AuthClaims, verify_supabase_token
from app.db.session import get_db
from app.models.user import AppUser

logger = get_logger(__name__)


async def get_current_auth(
    authorization: str = Header(None),
) -> AuthClaims:
    """Extract and verify JWT from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        logger.warning("auth.header.missing_or_invalid")
        raise UnauthorizedError("Missing or invalid authorization header")

    token = authorization.split(" ", 1)[1]
    claims = verify_supabase_token(token)

    if not claims:
        logger.warning("auth.token.invalid_or_expired")
        raise UnauthorizedError("Invalid or expired token")

    logger.info("auth.token.accepted user_id=%s", _mask_id(str(claims.user_id)))
    return claims


async def get_current_user(
    auth: AuthClaims = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> AppUser:
    """Get or create the current user from Supabase claims."""
    result = await db.execute(
        select(AppUser).where(AppUser.supabase_user_id == auth.user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        logger.info("auth.user.bootstrap_started supabase_user_id=%s", _mask_id(str(auth.user_id)))
        # Bootstrap new user
        user = AppUser(
            supabase_user_id=auth.user_id,
            email=auth.email,
            display_name=auth.email.split("@")[0] if auth.email else None,
        )
        db.add(user)
        await db.flush()
        logger.info(
            "auth.user.bootstrap_completed user_id=%s supabase_user_id=%s",
            _mask_id(str(user.id)),
            _mask_id(str(auth.user_id)),
        )
    else:
        logger.info(
            "auth.user.loaded user_id=%s supabase_user_id=%s",
            _mask_id(str(user.id)),
            _mask_id(str(auth.user_id)),
        )

    return user


def _mask_id(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 8:
        return value
    return f"...{value[-8:]}"
