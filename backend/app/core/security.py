# app/core/security.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    # Жесткая проверка типа
    if not isinstance(password, str):
        raise ValueError(f"Password must be str, got {type(password)}: {repr(password)[:200]}")

    b = password.encode("utf-8")
    # Принудительно печатаем и принудительно флашим
    print("HASH_PASSWORD REPR:", repr(password), flush=True)
    print("HASH_PASSWORD len(chars):", len(password), flush=True)
    print("HASH_PASSWORD len(bytes):", len(b), flush=True)

    # Если вдруг >72 — не даём дойти до bcrypt и падаем с понятным текстом
    if len(b) > 72:
        raise ValueError(f"Password too long for bcrypt: {len(b)} bytes (max 72). REPR={repr(password)[:200]}")

    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(*, subject: str, secret_key: str, algorithm: str, expires_minutes: int) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=expires_minutes)
    to_encode: dict[str, Any] = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, secret_key, algorithm=algorithm)


def decode_token(token: str, *, secret_key: str, algorithm: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        return payload
    except JWTError as e:
        raise ValueError("Invalid token") from e
