from unittest.mock import patch
from unittest import IsolatedAsyncioTestCase
from config import BoardConfig
import tempfile
import os
from handler.board.storage import (
    _get_db,
    set_table,
)
from datetime import datetime

from freezegun import freeze_time


class IntegrationTestCase(IsolatedAsyncioTestCase):
    """Base class for integration tests that need database access"""

    def setUp(self) -> None:
        self.fd, self.path = tempfile.mkstemp(suffix=".db")
        self.db_patch = patch.object(BoardConfig, "DB_PATH", new=self.path)
        self.db_patch.start()

        self.now = datetime.now()
        self.freezer_context = freeze_time(self.now)
        self.freezer = self.freezer_context.__enter__()

    def tearDown(self) -> None:
        self.freezer_context.__exit__()
        self.db_patch.stop()
        os.close(self.fd)
        os.remove(self.path)

    async def asyncSetUp(self) -> None:
        """Initialize database for tests"""
        self.db_context = _get_db()
        self.db = await self.db_context.__aenter__()
        await set_table(self.db)

    async def asyncTearDown(self) -> None:
        """Clean up database after tests"""
        if self.db_context:
            await self.db_context.__aexit__(None, None, None)
