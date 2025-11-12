from unittest.mock import patch
from unittest import IsolatedAsyncioTestCase
from config import BoardConfig
import tempfile
import os
from handler.board.storage import (
    _get_db,
    set_table,
)


class UseDB_TestCase(IsolatedAsyncioTestCase):
    """DB를 사용하는 TC"""

    def setUp(self) -> None:
        super().setUp()
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.db_patch = patch.object(BoardConfig, "DB_PATH", new=self.db_path)
        self.db_patch.start()

    def tearDown(self) -> None:
        super().tearDown()
        self.db_patch.stop()
        os.close(self.db_fd)
        os.remove(self.db_path)


class UseTable_TestCase(UseDB_TestCase):
    async def asyncSetUp(self) -> None:
        """Initialize database for tests"""
        await super().asyncSetUp()
        self.db_context = _get_db()
        self.db = await self.db_context.__aenter__()
        await set_table(self.db)

    async def asyncTearDown(self) -> None:
        """Clean up database after tests"""
        await super().asyncTearDown()
        if self.db_context:
            await self.db_context.__aexit__(None, None, None)
