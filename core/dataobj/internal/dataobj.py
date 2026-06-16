from __future__ import annotations

from dataclasses import dataclass, Field
from types import UnionType
from typing import Any, ClassVar, Literal, Union, get_args, get_origin, get_type_hints
from typing_extensions import dataclass_transform

DATACLASS_OPTION = Literal[
    "init",
    "repr",
    "eq",
    "order",
    "unsafe_hash",
    "frozen",
    "atch_args",
    "kw_only",
    "slots",
    "weakref_slot"
]


@dataclass_transform()
class DataObj:
    """
    이 클래스를 상속하면 서브클래스 정의 시점에 자동으로 @dataclass를 적용합니다.
    - 서브클래스에서 __dataclass_config__ = dict(slots=True, kw_only=True, frozen=False, ...) 로 옵션 조절
    - 특정 서브클래스에서 자동화를 끄려면 __auto_dataclass__ = False

    idea -> default를 freeze and slots 적용
    """
    __auto_dataclass__: ClassVar[bool] = True
    __dataclass_config__: ClassVar[dict[DATACLASS_OPTION, bool]] = {}
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
            if type(item) is list:
                return [
                    __item_parsing(v)
                    for v in item
                ]
            if type(item) is dict:
                return {
                    k: __item_parsing(v)
                    for k, v in item.items()
                }

            return item

        return {
            key: __item_parsing(self.get_attr(key))
            for key in self.my_fields()
        }

    @classmethod
    def from_dict(cls, raw: dict):
        # raw __annotations__는 `from __future__ import annotations` 모듈에서
        # 문자열이 되고 상속 필드도 누락되므로 get_type_hints로 해석한다
        hints = get_type_hints(cls)

        def parse(field_type: Any, value: Any) -> Any:
            origin = get_origin(field_type)
            if origin is list and isinstance(value, list):
                (item_type,) = get_args(field_type)
                return [parse(item_type, v) for v in value]
            if origin in (Union, UnionType):
                args = [a for a in get_args(field_type) if a is not type(None)]
                if value is None or len(args) != 1:
                    return value
                return parse(args[0], value)
            if hasattr(field_type, "from_dict") and isinstance(value, dict):
                return field_type.from_dict(value)
            return value

        return cls(**{
            key: parse(hints[key], raw[key])
            for key in cls.__dataclass_fields__.keys()
        })


def copy(item):
    if hasattr(item, "copy"):
        return item.copy()
    return item
