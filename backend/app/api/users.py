# app/api/users.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.models import User
from app.db.models.user import UserRole
from app.db.session import get_db
from app.schemas.auth import UserPublic

from pydantic import BaseModel


router = APIRouter(prefix="/users", tags=["users"])


class UserCreateByAdmin(BaseModel):
    username: str
    password: str
    role: UserRole


class UserRoleUpdate(BaseModel):
    role: UserRole


@router.get("", response_model=list[UserPublic], dependencies=[Depends(require_roles(UserRole.admin))])
def list_users(db: Session = Depends(get_db)) -> list[User]:
    return list(db.query(User).order_by(User.id.asc()).all())


@router.post("", response_model=UserPublic, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_roles(UserRole.admin))])
def create_user_by_admin(payload: UserCreateByAdmin, db: Session = Depends(get_db)) -> User:
    existing = db.query(User).filter(User.username == payload.username).one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    if len(payload.password.encode("utf-8")) > 72:
        raise HTTPException(status_code=400, detail="Password too long (max 72 bytes for bcrypt)")

    from app.core.security import hash_password
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/role", response_model=UserPublic, dependencies=[Depends(require_roles(UserRole.admin))])
def update_user_role(user_id: int, payload: UserRoleUpdate, db: Session = Depends(get_db)) -> User:
    user = db.query(User).filter(User.id == user_id).one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user
