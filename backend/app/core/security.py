import uuid
from dataclasses import dataclass
from functools import lru_cache

import httpx
from jose import JWTError, jwt

from app.core.config import settings
from app.core.logging import get_logger

ASYMMETRIC_JWT_ALGORITHMS = {"ES256", "RS256"}

logger = get_logger(__name__)


@dataclass
class AuthClaims:
    user_id: uuid.UUID
    email: str


def verify_supabase_token(token: str) -> AuthClaims | None:
    """Verify a Supabase JWT access token and return claims."""
    try:
        header = jwt.get_unverified_header(token)
        algorithm = header.get("alg")
        kid = header.get("kid")

        logger.info(
            "auth.jwt_verification.started algorithm=%s kid=%s",
            algorithm,
            _mask_id(kid),
        )

        if algorithm == "HS256":
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
        elif algorithm in ASYMMETRIC_JWT_ALGORITHMS:
            payload = _decode_with_jwks(token, algorithm, kid)
        else:
            logger.warning(
                "auth.jwt_verification.unsupported_algorithm algorithm=%s kid=%s",
                algorithm,
                _mask_id(kid),
            )
            return None

        claims = _claims_from_payload(payload)
        logger.info(
            "auth.jwt_verification.completed algorithm=%s kid=%s has_claims=%s user_id=%s",
            algorithm,
            _mask_id(kid),
            bool(claims),
            _mask_id(str(claims.user_id) if claims else None),
        )
        return claims

    except (JWTError, ValueError, httpx.HTTPError) as exc:
        logger.warning(
            "auth.jwt_verification.failed error_type=%s message=%s",
            exc.__class__.__name__,
            str(exc),
        )
        return None


def _decode_with_jwks(token: str, algorithm: str, kid: str | None) -> dict:
    if not kid:
        logger.warning("auth.jwks.missing_kid algorithm=%s", algorithm)
        raise JWTError("Missing JWT key id")

    jwks = _get_supabase_jwks()
    key = next(
        (candidate for candidate in jwks.get("keys", []) if candidate.get("kid") == kid),
        None,
    )
    if not key:
        logger.warning("auth.jwks.key_not_found kid=%s", _mask_id(kid))
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
        logger.warning("auth.jwt_claims.missing_subject")
        return None

    return AuthClaims(user_id=uuid.UUID(user_id), email=email or "")


@lru_cache(maxsize=1)
def _get_supabase_jwks() -> dict:
    if not settings.SUPABASE_URL:
        logger.error("auth.jwks.supabase_url_missing")
        raise JWTError("SUPABASE_URL is not configured")

    url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
    logger.info("auth.jwks.fetching url=%s", url)
    response = httpx.get(url, timeout=5.0)
    response.raise_for_status()
    jwks = response.json()
    logger.info("auth.jwks.loaded key_count=%s", len(jwks.get("keys", [])))
    return jwks


def _mask_id(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 8:
        return value
    return f"...{value[-8:]}"
