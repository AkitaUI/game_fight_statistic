"""
Пакет работы с БД:
- config: настройки подключения
- base: engine, Session, Base
- models: ORM-модели
- repositories: репозитории для доступа к данным
"""

from .base import Base, engine, SessionLocal
