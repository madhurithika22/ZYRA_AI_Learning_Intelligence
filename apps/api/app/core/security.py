import base64
import hashlib
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

# Derive symmetric encryption key from SECRET_KEY environment variable
_SECRET_RAW = os.getenv["SECRET_KEY"]
_DERIVED_KEY = base64.urlsafe_b64encode(hashlib.sha256(_SECRET_RAW.encode("utf-8")).digest())
_CIPHER = Fernet(_DERIVED_KEY)

PBKDF2_ITERATIONS = 200_000


def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with 200,000 iterations and 16-byte random salt."""
    salt = secrets.token_bytes(16)
    pw_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    salt_hex = salt.hex()
    hash_hex = pw_hash.hex()
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt_hex}${hash_hex}"


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify raw password against PBKDF2 hash using constant-time comparison."""
    try:
        parts = hashed_password.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        target_hash = bytes.fromhex(parts[3])

        computed_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations,
        )
        return secrets.compare_digest(computed_hash, target_hash)
    except Exception:
        return False


def create_session_token(
    user_id: str,
    learner_id: str,
    email: str,
    expires_delta_days: int = 7,
) -> str:
    """Create encrypted & signed Fernet session token containing user identity and expiration timestamp."""
    exp = datetime.now(timezone.utc) + timedelta(days=expires_delta_days)
    payload = {
        "user_id": str(user_id),
        "learner_id": str(learner_id),
        "email": email,
        "exp": exp.isoformat(),
    }
    raw_bytes = json.dumps(payload).encode("utf-8")
    encrypted_token = _CIPHER.encrypt(raw_bytes).decode("utf-8")
    return encrypted_token


def decode_session_token(token: str) -> dict[str, Any] | None:
    """Decrypt and validate Fernet session token. Returns payload dict or None if invalid/expired."""
    try:
        decrypted_bytes = _CIPHER.decrypt(token.encode("utf-8"))
        payload: dict[str, Any] = json.loads(decrypted_bytes.decode("utf-8"))
        exp_iso = payload.get("exp")
        if not exp_iso:
            return None

        exp_dt = datetime.fromisoformat(exp_iso)
        if datetime.now(timezone.utc) > exp_dt:
            return None

        return payload
    except (InvalidToken, ValueError, TypeError, KeyError):
        return None
