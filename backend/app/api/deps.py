from fastapi import Depends, Header, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import UnauthorizedError
from app.core.security import AuthClaims, verify_supabase_token
from app.db.session import get_db
from app.models.user import AppUser
from app.services.workspace_service import (
    get_workspace_or_404,
    require_workspace_access,
    require_workspace_owner,
)


async def get_current_auth(
    authorization: str = Header(None),
) -> AuthClaims:
    """Extract and verify JWT from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError("Missing or invalid authorization header")

    token = authorization.split(" ", 1)[1]
    claims = verify_supabase_token(token)

    if not claims:
        raise UnauthorizedError("Invalid or expired token")

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
        # Bootstrap new user
        user = AppUser(
            supabase_user_id=auth.user_id,
            email=auth.email,
            display_name=auth.email.split("@")[0] if auth.email else None,
        )
        db.add(user)
        await db.flush()

    return user
