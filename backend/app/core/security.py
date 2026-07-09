import uuid
from dataclasses import dataclass
from functools import lru_cache

import httpx
from jose import JWTError, jwt

from app.core.config import settings

ASYMMETRIC_JWT_ALGORITHMS = {"ES256", "RS256"}


@dataclass
class AuthClaims:
    user_id: uuid.UUID
    email: str


def verify_supabase_token(token: str) -> AuthClaims | None:
    """Verify a Supabase JWT access token and return claims."""
    try:
        header = jwt.get_unverified_header(token)
        algorithm = header.get("alg")

        if algorithm == "HS256":
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
        elif algorithm in ASYMMETRIC_JWT_ALGORITHMS:
            payload = _decode_with_jwks(token, algorithm, header.get("kid"))
        else:
            return None

        return _claims_from_payload(payload)

    except (JWTError, ValueError, httpx.HTTPError):
        return None


def _decode_with_jwks(token: str, algorithm: str, kid: str | None) -> dict:
    if not kid:
        raise JWTError("Missing JWT key id")

    jwks = _get_supabase_jwks()
    key = next(
        (candidate for candidate in jwks.get("keys", []) if candidate.get("kid") == kid),
        None,
    )
    if not key:
        raise JWTError("Supabase JWT signing key not found")

    return jwt.decode(
        token,
        key,
        algorithms=[algorithm],
        options={"verify_aud": False},
    )


def _claims_from_payload(payload: dict) -> AuthClaims | None:
    user_id = payload.get("sub")
    email = payload.get("email")

    if not user_id:
        return None

    return AuthClaims(user_id=uuid.UUID(user_id), email=email or "")


@lru_cache(maxsize=1)
def _get_supabase_jwks() -> dict:
    if not settings.SUPABASE_URL:
        raise JWTError("SUPABASE_URL is not configured")

    url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
    response = httpx.get(url, timeout=5.0)
    response.raise_for_status()
    return response.json()
