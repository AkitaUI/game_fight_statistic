# app/api/auth.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import User
from app.db.models.user import UserRole
from app.db.session import get_db
from app.schemas.auth import Token, UserPublic, UserRegister

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)) -> User:
    existing = db.query(User).filter(User.username == payload.username).one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    pwd = payload.password
    print("PASSWORD TYPE:", type(pwd))
    print("PASSWORD REPR:", repr(pwd))
    print("PASSWORD len(chars):", len(pwd))
    print("PASSWORD len(bytes):", len(pwd.encode("utf-8")))

    try:
        password_hash = hash_password(pwd)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        role=UserRole.player,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/token", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> Token:
    user = db.query(User).filter(User.username == form.username).one_or_none()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    token = create_access_token(
        subject=str(user.id),
        secret_key=settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
        expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    return Token(access_token=token)