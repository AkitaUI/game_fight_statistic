from __future__ import annotations


class AppError(Exception):
    """Базовая доменная ошибка приложения."""

    def __init__(self, message: str = "") -> None:
        super().__init__(message)
        self.message = message or self.__class__.__name__


# --- Игроки ---


class PlayerNotFoundError(AppError):
    pass


class PlayerAlreadyExistsError(AppError):
    pass


# --- Бои ---


class BattleNotFoundError(AppError):
    pass


class BattleAlreadyFinishedError(AppError):
    pass


class InvalidBattleOperationError(AppError):
    """Некорректная операция над боем (например, команда не принадлежит бою)."""
    pass


# --- Статистика ---


class StatsNotFoundError(AppError):
    pass
