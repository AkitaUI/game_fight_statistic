# app/core/seed.py
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.models import User
from app.db.models.user import UserRole


def seed_initial_admin(db: Session) -> None:
    """
    Создаёт первого администратора при старте приложения, если:
    - включён флаг SEED_ADMIN
    - есть ADMIN_USERNAME/ADMIN_PASSWORD
    - в БД ещё нет ни одного admin
    """

    if not getattr(settings, "SEED_ADMIN", False):
        return

    username = getattr(settings, "ADMIN_USERNAME", "") or ""
    password = getattr(settings, "ADMIN_PASSWORD", "") or ""

    if not username or not password:
        # Без кредов — не создаём никого
        return

    # bcrypt limitation
    if len(password.encode("utf-8")) > 72:
        raise ValueError("ADMIN_PASSWORD too long (max 72 bytes for bcrypt)")

    # Если уже есть админ — ничего не делаем
    existing_admin = db.query(User).filter(User.role == UserRole.admin).first()
    if existing_admin:
        return

    # Если юзер с таким username уже есть — повышаем до admin и (опционально) обновляем пароль
    existing_user = db.query(User).filter(User.username == username).one_or_none()
    if existing_user:
        existing_user.role = UserRole.admin
        # Если хочешь НЕ менять пароль существующему юзеру — удали следующую строку:
        existing_user.password_hash = hash_password(password)
        db.commit()
        return

    # Создаём нового админа
    user = User(
        username=username,
        password_hash=hash_password(password),
        role=UserRole.admin,
    )
    db.add(user)
    db.commit()
