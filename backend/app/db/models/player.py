# app/db/models/player.py
from __future__ import annotations

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

if TYPE_CHECKING:
    from .user import User
    from .game import Game
    from .battle import PlayerBattleStats


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)

    # NEW: игрок в контексте игры (изоляция данных по игре)
    game_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("games.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # связь с аккаунтом (если игрок привязан к пользователю)
    user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    nickname: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Связи
    game: Mapped["Game"] = relationship(back_populates="players")

    user: Mapped[Optional["User"]] = relationship(back_populates="players")

    battle_stats: Mapped[List["PlayerBattleStats"]] = relationship(
        back_populates="player",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("game_id", "nickname", name="uq_player_game_nickname"),
    )
