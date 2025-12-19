from __future__ import annotations
from contextvars import ContextVar
from functools import wraps
from utils.id import get_uuid
from core.dataobj import DataObj
from typing import Callable, Self

_lifecycle_var: ContextVar[LifeCycle] = ContextVar("lifecycle")


class LifeCycle(DataObj):
    id: str

    def close(self):
        pass

    @classmethod
    def create(cls, *args, **kwargs):
        if 'id' not in kwargs:
            kwargs['id'] = get_uuid()
        return cls(*args, **kwargs)

    @classmethod
    def with_lifecycle(
        cls,
        factory: Callable[[], Self] | None = None
    ):
        """함수에 lifecycle을 바인딩하는 decorator

        Args:
            factory: lifecycle 인스턴스를 생성하는 함수. None이면 cls.create() 사용

        Returns:
            함수를 래핑하는 decorator
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                lc = factory() if factory else cls.create()
                token = _lifecycle_var.set(lc)
                try:
                    return func(*args, **kwargs)
                finally:
                    lc.close()
                    _lifecycle_var.reset(token)
            return wrapper
        return decorator

    @classmethod
    def get_lifecycle(cls) -> Self:
        """현재 실행 중인 함수의 lifecycle 가져오기

        Returns:
            현재 ContextVar에 저장된 lifecycle 인스턴스

        Raises:
            LookupError: lifecycle이 설정되지 않은 컨텍스트에서 호출 시
        """
        return _lifecycle_var.get()  # type:ignore
