import logging
import base64
import uuid

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from jose import jwt

from app.core import security
from app.core.config import settings



_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
def test_verify_supabase_token_accepts_hs256(monkeypatch):
    user_id = uuid.uuid4()
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret")

    token = jwt.encode(
        {"sub": str(user_id), "email": "user@example.com"},
        "test-secret",
        algorithm="HS256",
    )

    claims = security.verify_supabase_token(token)

    assert claims is not None
    assert claims.user_id == user_id
    assert claims.email == "user@example.com"


def test_verify_supabase_token_accepts_es256_jwks(monkeypatch):
    user_id = uuid.uuid4()
    private_key = ec.generate_private_key(ec.SECP256R1())
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    token = jwt.encode(
        {"sub": str(user_id), "email": "google@example.com"},
        private_pem,
        algorithm="ES256",
        headers={"kid": "test-key"},
    )
    monkeypatch.setattr(
        security,
        "_get_supabase_jwks",
        lambda: {"keys": [_public_ec_jwk(private_key, "test-key")]},
    )

    claims = security.verify_supabase_token(token)

    assert claims is not None
    assert claims.user_id == user_id
    assert claims.email == "google@example.com"


def test_verify_supabase_token_rejects_unknown_jwks_key(monkeypatch):
    private_key = ec.generate_private_key(ec.SECP256R1())
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    token = jwt.encode(
        {"sub": str(uuid.uuid4()), "email": "google@example.com"},
        private_pem,
        algorithm="ES256",
        headers={"kid": "missing-key"},
    )
    monkeypatch.setattr(security, "_get_supabase_jwks", lambda: {"keys": []})

    assert security.verify_supabase_token(token) is None


def _public_ec_jwk(private_key: ec.EllipticCurvePrivateKey, kid: str) -> dict:
    public_numbers = private_key.public_key().public_numbers()
    return {
        "kty": "EC",
        "kid": kid,
        "use": "sig",
        "alg": "ES256",
        "crv": "P-256",
        "x": _base64url_uint(public_numbers.x),
        "y": _base64url_uint(public_numbers.y),
    }


def _base64url_uint(value: int) -> str:
    raw = value.to_bytes(32, "big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")
