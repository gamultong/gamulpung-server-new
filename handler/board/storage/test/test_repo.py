from unittest.mock import patch
from unittest import IsolatedAsyncioTestCase
from config import BoardConfig
import tempfile
import os
from handler.board.storage import _get_db, set_table, get_section, create_section, update_section, get_section_range
from data.board import Tile, Tiles, Point, PointRange

OPENED_TILE = Tile(
    is_open=True,
    is_mine=False,
    is_flag=False,
    number=0
).data
CLOSED_TILE = Tile(
    is_open=False,
    is_mine=False,
    is_flag=False,
    number=0
).data

EXAMPLE_TILES = Tiles(
    data=bytearray([
        OPENED_TILE, OPENED_TILE,
        OPENED_TILE, OPENED_TILE,
    ]),
    width=2, height=2
)
CHANGED_TILES = Tiles(
    data=bytearray([
        OPENED_TILE, CLOSED_TILE,
        CLOSED_TILE, OPENED_TILE,
    ]),
    width=2, height=2
)


class DB_TestCase(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.fd, self.path = tempfile.mkstemp(suffix=".db")
        self.db_patch = patch.object(BoardConfig, "DB_PATH", new=self.path)
        self.db_patch.start()

    def tearDown(self) -> None:
        self.db_patch.stop()
        os.close(self.fd)
        os.remove(self.path)


class GetDB_TestCase(DB_TestCase):
    async def test_normal(self):
        async with _get_db() as db:
            async with db.execute("SELECT 1") as cur:
                row = await cur.fetchone()

                self.assertEqual(row[0], 1)  # type:ignore


class TableSet_TestCase(DB_TestCase):
    async def test_normal(self):
        query = "SELECT name FROM sqlite_master WHERE type='table';"
        async with _get_db() as db:
            await set_table(db)

            async with db.execute(query) as cur:
                res = await cur.fetchall()
                table_names = [row["name"] for row in res]
                self.assertIn("section", table_names)


class Repo_TestCase(DB_TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.section_length_patch = patch.object(BoardConfig, "LENGTH", new=2)
        self.section_length_patch.start()
        self.db_context = None

    def tearDown(self) -> None:
        self.section_length_patch.stop()
        super().tearDown()

    async def asyncSetUp(self) -> None:
        self.db_context = _get_db()
        self.db = await self.db_context.__aenter__()
        await set_table(self.db)

    async def asyncTearDown(self) -> None:
        if self.db_context:
            await self.db_context.__aexit__(None, None, None)


class SectionRepo_TestCase(Repo_TestCase):
    async def test_normal(self):
        await create_section(self.db, EXAMPLE_TILES, Point(0, 0))
        tiles = await get_section(self.db, Point(0, 0))
        self.assertEqual(EXAMPLE_TILES, tiles)

        await update_section(self.db, CHANGED_TILES, Point(0, 0))
        tiles = await get_section(self.db, Point(0, 0))
        self.assertEqual(CHANGED_TILES, tiles)

    async def test_get_range(self):
        await create_section(self.db, EXAMPLE_TILES, Point(0, 0))
        await create_section(self.db, EXAMPLE_TILES, Point(1, 0))
        await create_section(self.db, EXAMPLE_TILES, Point(2, 0))
        await create_section(self.db, EXAMPLE_TILES, Point(3, 0))

        tiles_d = await get_section_range(self.db, PointRange(Point(1, 1), Point(2, 0)))
        self.assertDictEqual(
            tiles_d,
            {
                Point(1, 0): EXAMPLE_TILES,
                Point(2, 0): EXAMPLE_TILES,
            }
        )


if __name__ == "__main__":
    from unittest import main
    main()
