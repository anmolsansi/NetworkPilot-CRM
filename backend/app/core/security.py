from dataclasses import dataclass

from jose import JWTError, jwt

from app.core.config import settings


@dataclass
class AuthClaims:
    user_id: str
    email: str


def verify_supabase_token(token: str) -> AuthClaims | None:
    """Verify a Supabase JWT access token and return claims."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )

        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id:
            return None

        return AuthClaims(user_id=user_id, email=email or "")

    except JWTError:
        return None
