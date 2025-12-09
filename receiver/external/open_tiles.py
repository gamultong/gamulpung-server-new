from collections import deque
from loguru import logger

from core.event import Event
from core.broker import EventBroker

from data.payload import IdDataPayload, ClientMessage
from data.board import Point, Section, abs_to_sec, PointRange

from handler.board import BoardHandler
from handler.cursor import CursorHandler

OPEN_TILES_EVENT = Event[IdDataPayload[str, ClientMessage.OpenTiles]]


@EventBroker.add_receiver("OPEN-TILES")
async def open_tiles_receiver(event: OPEN_TILES_EVENT):
    id = event.payload.id
    data = event.payload.data

    point = data.position

    cursor = await CursorHandler.get_by_id(id)
    if not cursor.is_alive:
        logger.warning(f"커서가 이미 사망함 | cursor:{cursor}")
        return
    if not cursor.in_interaction_range(point):
        logger.warning(f"상호작용 범위 밖 타일 열람 시도 | cursor:{cursor}, point:{point}")
        return

    tile = await BoardHandler.fetch_tile(point)
    if tile.is_flag:
        logger.warning(f"깃발이 설치된 타일 열람 시도 | cursor:{cursor}, tile:{tile}")
        return
    if tile.is_open:
        logger.warning(f"열린 타일 열람 시도 | cursor:{cursor}, tile:{tile}")
        return
    if tile.is_mine:
        await BoardHandler.open_tiles(point)
        return

    chaining_points = await chaining(point)
    for p in chaining_points:
        await BoardHandler.open_tiles(p)
        await CursorHandler.increase_score(cursor, 100)
    # await BoardHandler.open_tiles(point)
    # await CursorHandler.increase_score(cursor, 100)


async def chaining(point: Point):
    result = set([point])
    is_open = set()
    sections: dict[Point, Section] = {}

    queue = deque([point])
    is_mine = False

    c = 10

    while len(queue) > 0:
        if len(result) > c:
            logger.warning(f"chainning 결과가 {c}개가 넘어감")
            c += 10
        p = queue.pop()

        sec_p = abs_to_sec(p)
        if sec_p not in sections:
            section = await BoardHandler.fetch_section(sec_p)
            sections[sec_p] = section

        tile = sections[sec_p].at_tile_by_abs_point(p)
        if tile.is_mine:  # 첫 번째만 가능
            logger.warning("number를 거치지 않은 mine 접근이 불가능해야함")
            continue
        if tile.is_open:
            is_open.add(p)
            continue
        if tile.number > 0:
            continue

        around = PointRange.create_by_mid(p, 1, 1)
        for ard_p in around.iter():
            if ard_p in result:
                continue
            result.add(ard_p)
            queue.append(ard_p)

    result -= is_open

    return result
