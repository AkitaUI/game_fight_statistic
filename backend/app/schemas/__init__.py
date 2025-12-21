# app/schemas/__init__.py

from .base import ORMModel, PagedResponse

from .auth import Token, UserRegister, UserPublic
from .games import GameRead

from .player import (
    PlayerCreate,
    PlayerRead,
    PlayerListItem,
    PlayerStatsSummary,
    PlayerWithStatsSummary,
)

from .battle import (
    BattleCreate,
    BattleRead,
    BattleListItem,
    BattleFinishRequest,
    BattleTeamCreate,
    BattleTeamRead,
    PlayerBattleStatsCreate,
    PlayerBattleStatsRead,
    WeaponStatsItem,
)

from .stats import (
    PlayerStatsFilter,
    GlobalStatsFilter,
    MapStatsItem,
    WeaponStatsItem as WeaponStatsAggItem,
    ModeStatsItem,
)

__all__ = [
    # base
    "ORMModel",
    "PagedResponse",
    # auth
    "Token",
    "UserRegister",
    "UserPublic",
    # games
    "GameRead",
    # player
    "PlayerCreate",
    "PlayerRead",
    "PlayerListItem",
    "PlayerStatsSummary",
    "PlayerWithStatsSummary",
    # battle
    "BattleCreate",
    "BattleRead",
    "BattleListItem",
    "BattleFinishRequest",
    "BattleTeamCreate",
    "BattleTeamRead",
    "PlayerBattleStatsCreate",
    "PlayerBattleStatsRead",
    "WeaponStatsItem",
    # stats
    "PlayerStatsFilter",
    "GlobalStatsFilter",
    "MapStatsItem",
    "WeaponStatsAggItem",
    "ModeStatsItem",
]
