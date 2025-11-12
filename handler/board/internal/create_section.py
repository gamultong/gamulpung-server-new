from data.board import PointRange, Tiles, Point, Tile, get_overlap
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


async def make_closed_section(db: DB, point: Point):
    length = BoardConfig.LENGTH
    tiles = Tiles(
        bytearray([
            TILE
            for _ in range(length)
            for _ in range(length)
        ]), length, length
    )
    section = Section(point, tiles)
    await create_section(db, section)

    return section


def make_section(point: Point):
    length = BoardConfig.LENGTH
    m = (length**2)/BoardConfig.MINE_RATIO

    tiles, count = rand_tiles()
    while m/2 <= count <= m*2:
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


def merge_sections(center: Point, sections: dict[Point, Section]):
    """3*3 크기의 section의 tiles merge 후 return"""
    length = BoardConfig.LENGTH

    result = Tiles(bytearray(), length*3, 0)
    for y in range(center.y-1, center.y+2):
        line = Tiles(bytearray(), 0, length)
        for x in range(center.x-1, center.x+2):
            point = Point(x, y)
            section = sections[point]

            line = line.h_append(section.tiles)
        result = result.v_append(line)

    return result


def count_mine(tiles: Tiles):
    """3*3의 tiles의 가운데 제외 지뢰 갯수"""
    assert tiles.width == tiles.height == 3

    count = 0
    point_range = PointRange(Point(0, 2), Point(2, 0))

    for point in point_range.iter():
        if point == Point(1, 1):
            continue
        tile = tiles.at_tile(point)
        count += tile.is_mine

    return count


def numbering_tiles(tiles: Tiles):
    """merge된 section의 tiles를 받아 가운데 section tiles만 numbering 후 return"""
    length = BoardConfig.LENGTH
    around_range = PointRange(Point(length-1, length*2), Point(length*2, length-1))
    point_range = PointRange(Point(1, length), Point(length, 1))

    around_tiles = tiles.at_tiles(around_range)

    for point in point_range.iter():
        pr = PointRange.create_by_mid(point, 1, 1)
        tiles = around_tiles.at_tiles(pr)
        tile = around_tiles.at_tile(point)
        tile.number = count_mine(tiles)

        around_tiles.update_at(point, tile)

    result = around_tiles.at_tiles(point_range)
    assert result.width == result.height == length
    return result


def numbering(center: Point, sections: dict[Point, Section]):
    """3*3 section이 주어지면 가운데 section numbering"""
    tiles = merge_sections(center, sections)
    tiles = numbering_tiles(tiles)
    sections[center].tiles = tiles


def set_start_point(section: Section):
    """start point 설정"""
    tile = section.tiles.at_tile(Point(0, 0))

    tile.is_mine = False
    tile.is_open = True
    section.tiles.update_at(Point(0, 0), tile)


async def check_is_init(db: DB):
    range = PointRange.create_by_mid(Point(0, 0), 2, 2)

    li = await get_section_range(db, range)
    if len(li) > 0:
        return True

    return False


async def initialize_start_map(db: DB):
    """
    초기 맵 설정

    CCC
    CNC
    CCC
    C -> CLOSED_SECTION
    N -> NUMBERING_SECTION
    의 초기 맵 구성 후 N을 INTERACTION_SECTION으로 upgrade 진행
    """
    if await check_is_init(db):
        return

    sections = {}

    center_p = Point(0, 0)
    center_sec = make_section(center_p)
    sections[center_p] = center_sec
    set_start_point(center_sec)

    numbering_range = PointRange.create_by_mid(center_p, 1, 1)

    for point in numbering_range.iter():
        if point == center_p:
            continue
        section = make_section(point)
        sections[point] = section

    # Numbering 계산
    numbering(center_p, sections)

    # 상태 설정 및 저장
    center_sec.flag = SectionFlag.NUMBERING

    for _, section in sections.items():
        await create_section(db, section)

    # upgrade_interaction_sections 호출로 자동 격상 및 테두리 생성
    await upgrade_interaction_sections(db, Point(0, 0))
