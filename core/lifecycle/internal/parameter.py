"""함수 파라미터 저장용 DataObj"""
from __future__ import annotations
from typing import Any
from core.dataobj import DataObj


class Parameter(DataObj):
    """함수 호출 파라미터

    args: 위치 인자 tuple
    kwargs: 키워드 인자 dict
    """
    args: tuple[Any, ...]
    kwargs: dict[str, Any]
