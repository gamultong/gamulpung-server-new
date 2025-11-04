from __future__ import annotations

from dataclasses import dataclass, Field
from typing import Any, ClassVar
from typing_extensions import dataclass_transform


@dataclass_transform()
class DataObj:
    """
    이 클래스를 상속하면 서브클래스 정의 시점에 자동으로 @dataclass를 적용합니다.
    - 서브클래스에서 __dataclass_config__ = dict(slots=True, kw_only=True, frozen=False, ...) 로 옵션 조절
    - 특정 서브클래스에서 자동화를 끄려면 __auto_dataclass__ = False

    idea -> default를 freeze and slots 적용
    """
    __auto_dataclass__: ClassVar[bool] = True
    __dataclass_config__: ClassVar[dict] = {}
    __dataclass_fields__: ClassVar[dict[str, Field[Any]]]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # 자신(DataObj) 생성 시엔 적용하지 않음
        if cls is DataObj:
            return

        # 원하면 쉽게 opt-out
        if not cls.__auto_dataclass__:
            return

        # 재생성(슬롯 추가)으로 재진입했을 때는 스킵
        if "__dataclass_params__" in cls.__dict__:
            return

        dataclass(**cls.__dataclass_config__)(cls)

    def my_fields(self):
        return self.__class__.__dataclass_fields__

    def get_attr(self, key):
        return getattr(self, key)  # dataclass(slots=True)시 __dict__ 없음

    def copy(self):
        return self.__class__(
            **{
                key: copy(self.get_attr(key))
                for key in self.my_fields()
            }
        )

    def to_dict(self):
        def __item_parsing(item):
            if isinstance(item, DataObj):
                return item.to_dict()
            return item

        return {
            key: __item_parsing(self.get_attr(key))
            for key in self.my_fields()
        }

    @classmethod
    def from_dict(cls, dict: dict):
        def parse(key):
            type = cls.__annotations__[key]
            if hasattr(type, "from_dict"):
                return type.from_dict(dict[key])
            return dict[key]

        return cls(**{
            key: parse(key)
            for key in cls.__dataclass_fields__.keys()
        })


def copy(item):
    if hasattr(item, "copy"):
        return item.copy()
    return item
