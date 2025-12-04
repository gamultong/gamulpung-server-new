from .use_db_tc import UseTable_TestCase
from unittest.mock import patch, AsyncMock
from handler.board.storage import DB
from typing import Callable, Awaitable


# TODO: tcm에 편입
def set_board(init_func):
    def func_wapper(func: Callable):

        @patch("server.initialize_board", new_callable=AsyncMock, side_effect=init_func)
        def wrapper(self: UseTable_TestCase, *args, **kwargs):
            return func(self, *args[1:], **kwargs)
        return wrapper
    return func_wapper
