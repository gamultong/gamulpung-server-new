from typing import Any
from loguru import logger


class BaseExp(Exception):
    def __str__(self) -> str:
        return f"[Exception] {self.__class__.__name__}: {self.data}"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.data = {
            "args": args,
            "kwargs": kwargs
        }
        logger.error(self)
