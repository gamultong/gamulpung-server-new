from data.board import PointRange, Tiles, Point, Tile
from handler.board.storage import _get_db, get_section_range, Section, create_section, update_section_flag, SectionFlag, DB

from config import BoardConfig
from random import randint

MINE = Tile(
    is_open=False,
    is_mine=True,
    is_flag=False,
    number=0
).data
TILE = Tile(
    is_open=False,
    is_mine=False,
    is_flag=False,
    number=0
).data


def rand_tile():
    rand = randint(1, 100)
    if 1 <= rand <= BoardConfig.MINE_RATIO * 100:
        return MINE
    else:
        return TILE


def rand_tiles():
    count = 0

    def f():
        nonlocal count
        tile = rand_tile()
        if tile is MINE:
            count += 1
        return tile

    length = BoardConfig.LENGTH
    return Tiles(
        bytearray([
            (f())
            for _ in range(length)
            for _ in range(length)
        ]), length, length
    ), count


def make_section(point: Point):
    length = BoardConfig.LENGTH
    m = (length**2)/BoardConfig.MINE_RATIO

    tiles, count = rand_tiles()
    while count < m/2 or m*2 < count:
        tiles, count = rand_tiles()

    return Section(point, tiles)


def number_section(section: Section):
    """
    섹션의 각 타일에 대해 인접한 지뢰의 개수를 계산합니다.
    """
    length = BoardConfig.LENGTH

    # 각 타일에 대해 순회
    for y in range(length):
        for x in range(length):
            # 현재 타일의 좌표
            tile_point = Point(x, y)
            tile = section.tiles.at_tile(tile_point)

            # 지뢰 타일은 숫자를 계산하지 않음
            if tile.is_mine:
                continue

            # 인접한 8개 위치의 지뢰 개수 계산
            mine_count = 0
            for offset in [Point(-1, -1), Point(-1, 0), Point(-1, 1),
                           Point(0, -1),              Point(0, 1),
                           Point(1, -1),  Point(1, 0), Point(1, 1)]:
                # 인접 위치
                neighbor_point = Point(tile_point.x + offset.x, tile_point.y + offset.y)

                # 섹션 범위 내인지 확인
                if 0 <= neighbor_point.x < length and 0 <= neighbor_point.y < length:
                    neighbor = section.tiles.at_tile(neighbor_point)
                    if neighbor.is_mine:
                        mine_count += 1

            # 계산된 숫자로 타일 업데이트
            new_tile = tile.copy()
            new_tile.number = mine_count
            section.tiles.update_at(tile_point, new_tile)

    # 섹션 상태를 NUMBERING으로 설정
    section.flag = SectionFlag.NUMBERING


def _get_surrounding_section_range(sec_point: Point) -> PointRange:
    """
    주어진 섹션 좌표를 기준으로 주위 1칸의 섹션 범위를 반환합니다.
    """
    return PointRange(
        top_left=Point(sec_point.x - 1, sec_point.y + 1),
        bottom_right=Point(sec_point.x + 1, sec_point.y - 1)
    )


async def upgrade_numbering_sections(db: DB, sec_point: Point):
    surrounding_range = _get_surrounding_section_range(sec_point)
    surrounding_sections = await get_section_range(db, surrounding_range)
    surrounding_dict = {sec.point: sec for sec in surrounding_sections}

    center = surrounding_dict[sec_point]
    assert center.flag == SectionFlag.CLOSED
    center.flag = SectionFlag.NUMBERING

    number_section(center)
    await update_section_flag(db, center)

    # 주위 1칙의 8개 섹션 좌표
    for y in range(surrounding_range.bottom, surrounding_range.top + 1):
        for x in range(surrounding_range.left, surrounding_range.right + 1):
            neighbor_point = Point(x, y)

            if neighbor_point in surrounding_dict:
                continue

            section = make_section(neighbor_point)
            await create_section(db, section)


async def upgrade_interaction_sections(db: DB, sec_point: Point):
    # 주위 1칸의 섹션 범위 조회
    surrounding_range = _get_surrounding_section_range(sec_point)
    surrounding_sections = await get_section_range(db, surrounding_range)
    surrounding_dict = {sec.point: sec for sec in surrounding_sections}

    center = surrounding_dict[sec_point]
    assert center.flag == SectionFlag.NUMBERING
    center.flag = SectionFlag.INTERACTIONAL
    await update_section_flag(db, center)

    # 주위 1칙의 8개 섹션 좌표
    for y in range(surrounding_range.bottom, surrounding_range.top + 1):
        for x in range(surrounding_range.left, surrounding_range.right + 1):
            neighbor_point = Point(x, y)

            # 중심 섹션은 스킵
            if neighbor_point == sec_point:
                continue

            # 이미 있는 섹션
            existing_section = surrounding_dict[neighbor_point]

            # CLOSED 상태면 numbering으로 격상
            if existing_section.flag == SectionFlag.CLOSED:
                existing_section = await upgrade_numbering_sections(db, neighbor_point)
