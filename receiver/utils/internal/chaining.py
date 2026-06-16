from collections import deque
from loguru import logger

from data.board import Point, Section, abs_to_sec, PointRange
from handler.board import BoardHandler


async def chaining(point: Point):
    result = set([point])
    is_open = set()
    sections: dict[Point, Section] = {}

    queue = deque([point])

    c = 10

    while len(queue) > 0:
        if len(result) > c:
            logger.warning(f"chainning 결과가 {c}개가 넘어감")
            c += 10
        p = queue.popleft()

        sec_p = abs_to_sec(p)
        if sec_p not in sections:
            section = await BoardHandler.fetch_section(sec_p)
            sections[sec_p] = section

        tile = sections[sec_p].at_map_tile_by_abs_point(p)
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
