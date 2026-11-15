"""Password hashing (bcrypt) and JWT creation/verification (PyJWT)."""
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt

from app.config import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, SECRET_KEY


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    raw = plain_password.encode("utf-8")
    if len(raw) > 72:  # bcrypt limit; such a password can never have been stored
        return False
    try:
        return bcrypt.checkpw(raw, hashed_password.encode("utf-8"))
    except ValueError:
        return False


# Used to keep login timing similar whether or not the user exists.
DUMMY_HASH = hash_password("dummy-password-1")


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT. `subject` is the user id as a string."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {"sub": str(subject), "iat": now, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    """Return the subject (user id) if the token is valid and unexpired, else None."""
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError:
        return None
    sub = payload.get("sub")
    return sub if isinstance(sub, str) else None
