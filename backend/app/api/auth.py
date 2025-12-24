# app/api/auth.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import User
from app.db.models.user import UserRole
from app.db.session import get_db
from app.schemas.auth import Token, UserPublic, UserRegister

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserPublic)
def me(current_user: User = Depends(get_current_user)) -> User:
    # Возвращаем публичные данные пользователя (включая role, если он есть в UserPublic)
    return current_user


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)) -> User:
    existing = db.query(User).filter(User.username == payload.username).one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")

    # bcrypt ограничение: 72 bytes
    if len(payload.password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password too long (max 72 bytes for bcrypt)",
        )

    password_hash = hash_password(payload.password)

    user = User(
        username=payload.username,
        password_hash=password_hash,
        role=UserRole.player,  # дефолтная роль при регистрации
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/token", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> Token:
    user = db.query(User).filter(User.username == form.username).one_or_none()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    token = create_access_token(
        subject=str(user.id),
        secret_key=settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
        expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        extra={"role": user.role.value},  # роль внутри токена (полезно для клиента/логов)
    )

    # Важно: здесь поля должны совпадать со схемой Token (app/schemas/auth.py)
    # Если Token у тебя ожидает token_type — добавь его в схему и верни тут.
    # Если Token ожидает role — ок, вернём role.
    return Token(
        access_token=token,
        token_type="bearer",   # если в Token нет поля token_type — убери эту строку
        role=user.role.value,  # если в Token нет поля role — убери эту строку
    )
