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
    assert cursor.in_interaction_range(point)

    chaining_points = await chaining(point)
    for p in chaining_points:
        await BoardHandler.open_tiles(p)
        await CursorHandler.increase_score(cursor, 100)


async def chaining(point: Point):
    result = set([point])
    is_open = set()
    sections: dict[Point, Section] = {}

    queue = deque([point])
    is_mine = False

    while len(queue) > 0:
        p = queue.pop()

        sec_p = abs_to_sec(p)
        if sec_p not in sections:
            section = await BoardHandler.fetch_section(sec_p)
            sections[sec_p] = section

        tile = sections[sec_p].at_tile_by_abs_point(p)
        if tile.is_mine:  # 첫 번째만 가능
            is_mine = True
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

    if is_mine:
        assert len(result) == 1

    result -= is_open

    return result
