from dataclasses import field
from enum import StrEnum, auto

from core.dataobj import DataObj


class ItemType(StrEnum):
    BOMB = auto()


class Items(DataObj):
    # 1) __init__ 대신 field(default_factory=...)로 기본값 정책을 dataclass 방식으로
    counts: dict[ItemType, int] = field(default_factory=lambda: {ItemType.BOMB: 0})

    @property
    def bomb(self) -> int:
        return self.counts.get(ItemType.BOMB, 0)

    def grant_item(self, item_type: ItemType, amount: int):
        assert item_type in self.counts
        self.counts[item_type] += amount

    def to_dict(self):
        return {k.value: v for k, v in self.counts.items()}

    @classmethod
    def from_dict(cls, raw: dict):
        obj = cls()
        obj.counts = {ItemType(k): int(v) for k, v in raw.items()}
        obj.counts.setdefault(ItemType.BOMB, 0)
        return obj
