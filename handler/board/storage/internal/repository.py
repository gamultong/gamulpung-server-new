from functools import cache
import aiosqlite
from contextlib import asynccontextmanager
from data.board import Point, PointRange, Tiles, Section
from config import BoardConfig
import os

SQL_PATH = os.path.join(os.path.dirname(__file__), "sql") + os.sep

TABLE_SET = "table.sql"
SECTION_GET = "get_section.sql"
SECTION_GET_BY_RANGE = "get_section_range.sql"
SECTION_UPDATE = "update_section.sql"
SECTION_FLAG_UPDATE = "update_section_flag.sql"
SECTION_CREATE = "create_section.sql"

DB = aiosqlite.Connection


@cache
def get_sql(path: str):
    with open(f"{SQL_PATH}{path}", "r", encoding="utf-8") as f:
        query = f.read()
    return query


@asynccontextmanager
async def _get_db():
    db = await aiosqlite.connect(BoardConfig.DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()


# async def get_db(func):
#     @wraps(func)
#     async def wrapper(*args, **kwargs):
#         async with _get_db() as db:
#             return await func(db, *args, **kwargs)
#     return wrapper

async def set_table(db: DB):
    query = get_sql(TABLE_SET)

    await db.execute(query)
    await db.commit()


async def get_section(db: DB, point: Point):
    query = get_sql(SECTION_GET)

    async with db.execute(query, (point.x, point.y)) as cur:
        row = await cur.fetchone()
    if row is None:
        return None

    length = BoardConfig.LENGTH
    tiles = Tiles(
        bytearray(row[0]),
        length,
        length
    )

    return Section(
        point=point,
        tiles=tiles,
        flag=row[1]
    )


async def get_section_range(db: DB, point_range: PointRange):
    query = get_sql(SECTION_GET_BY_RANGE)
    pr = point_range

    async with db.execute(query, (pr.left, pr.right, pr.bottom, pr.top)) as cur:
        seq = await cur.fetchall()

    length = BoardConfig.LENGTH

    def make_tiles(data: bytes):
        return Tiles(
            bytearray(data),
            length,
            length
        )

    return [
        Section(
            point=Point(row["x"], row["y"]),
            tiles=make_tiles(row["data"]),
            flag=row["flag"]
        )
        for row in seq
    ]


async def create_section(db: DB, section: Section):
    point = section.point
    tiles = section.tiles
    flag = section.flag

    query = get_sql(SECTION_CREATE)

    await db.execute(query, (point.x, point.y, tiles.data, flag))
    await db.commit()


async def update_section(db: DB, section: Section):
    point = section.point
    tiles = section.tiles

    query = get_sql(SECTION_UPDATE)

    await db.execute(query, (tiles.data, point.x, point.y))
    await db.commit()


async def update_section_flag(db: DB, section: Section):
    point = section.point
    flag = section.flag

    query = get_sql(SECTION_FLAG_UPDATE)

    await db.execute(query, (flag, point.x, point.y))
    await db.commit()
