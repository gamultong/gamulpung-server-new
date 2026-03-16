from __future__ import annotations

from core.dataobj import DataObj
from functools import cache

from .exceptions import InvalidCursorTileException

CURSOR_TILE_BYTES = 16
EMPTY_TILE_BYTES = b"\x00" * CURSOR_TILE_BYTES


class CursorTile(DataObj):
    __dataclass_config__ = {"frozen": True, "slots": True}
    user_id: str | None

    @property
    def data(self) -> bytes:
        if self.user_id is None:
            return EMPTY_TILE_BYTES
        return bytes.fromhex(self.user_id)

    @cache
    @staticmethod
    def create(user_id: str | None):
        if user_id is None:
            return CursorTile(user_id=None)

        if len(user_id) != 32:
            raise InvalidCursorTileException(user_id)

        try:
            raw = bytes.fromhex(user_id)
        except ValueError:
            raise InvalidCursorTileException(user_id)

        if len(raw) != CURSOR_TILE_BYTES:
            raise InvalidCursorTileException(user_id)

        return CursorTile(user_id=user_id.lower())

    @staticmethod
    def from_bytes(b: bytes):
        if b == EMPTY_TILE_BYTES:
            return CursorTile.create(None)

        return CursorTile.create(b.hex())
