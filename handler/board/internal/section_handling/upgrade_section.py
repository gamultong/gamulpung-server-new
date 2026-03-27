import asyncio

from data.board import PointRange, Point, Section, SectionFlag
from handler.board.storage import (
    create_section,
    update_section_flag,
    DB,
    update_section,
    get_dict_by_section_range,
    create_cursor_section,
    get_cursor_section
)

from .make_section import make_section
from .make_cursor_section import make_cursor_section
from .numbering import numbering

# 섹션 생성/넘버링 동시성 보호를 위한 글로벌 Lock
# SQLite single-writer + 단일 프로세스 환경에서 유효한 2차 방어
_section_creation_lock = asyncio.Lock()


def _get_surrounding_section_range(sec_point: Point) -> PointRange:
    """
    주어진 섹션 좌표를 기준으로 주위 1칸의 섹션 범위를 반환합니다.
    """
    return PointRange.create_by_mid(sec_point, 1, 1)


async def make_surround_sections(db: DB, surround_sections: dict[Point, Section], surround_range: PointRange):
    for p in surround_range.iter():
        if p in surround_sections:
            continue
        section = make_section(p)
        # INSERT OR IGNORE + re-SELECT: DB의 실제 레코드를 사용
        existing = await create_section(db, section)
        surround_sections[p] = existing
        await _sync_cursor_section(db, existing)


async def _sync_cursor_section(db: DB, section: Section):
    cursor_section = await get_cursor_section(db, section.point)
    if cursor_section is None:
        cursor_section = make_cursor_section(section.point)
        # INSERT OR IGNORE + re-SELECT
        await create_cursor_section(db, cursor_section)


async def _sync_cursor_sections(db: DB, sections: dict[Point, Section]):
    for section in sections.values():
        await _sync_cursor_section(db, section)


async def _upgrade_numbering_sections(db: DB, sec_point: Point, surround_sections: dict[Point, Section]):
    center = surround_sections[sec_point]
    assert center.flag == SectionFlag.CLOSED

    numbering(sec_point, surround_sections)

    await update_section(db, center)
    await update_section_flag(db, center)
    await _sync_cursor_section(db, center)


async def upgrade_numbering_section(db: DB, sec_point: Point):
    async with _section_creation_lock:
        surround_range = _get_surrounding_section_range(sec_point)
        surround_sections = await get_dict_by_section_range(db, surround_range)

        await make_surround_sections(db, surround_sections, surround_range)
        await _upgrade_numbering_sections(db, sec_point, surround_sections)


async def _upgrade_interaction_sections(db: DB, sec_point: Point, surround_sections: dict[Point, Section]):
    """section upgrade | numbering -> interaction"""
    center = surround_sections[sec_point]
    assert center.flag == SectionFlag.NUMBERING

    center.flag = SectionFlag.INTERACTIONAL
    await update_section_flag(db, center)
    await _sync_cursor_section(db, center)


async def _numbering_surround_section(db: DB, sec_point: Point, surround_sections: dict[Point, Section]):
    """주변 section numbering"""
    surrounding_range = _get_surrounding_section_range(sec_point)
    for p in surrounding_range.iter():
        if p == sec_point:
            continue

        section = surround_sections[p]
        if SectionFlag.CLOSED < section.flag:
            continue

        await upgrade_numbering_section(db, p)


async def upgrade_interaction_section(db: DB, sec_point: Point):
    """
    interaction section으로 upgrade

    1. 주변 section 받아오기
        - 주위 section이 이미 생성 되어 있다는 가정
    2. section upgrade | numbering -> interaction
    3. 주변 section upgrade | closed -> numbering
    """
    surround_range = _get_surrounding_section_range(sec_point)
    surround_sections = await get_dict_by_section_range(db, surround_range)
    assert surround_range.extent == len(surround_sections)

    await _upgrade_interaction_sections(db, sec_point, surround_sections)
    await _numbering_surround_section(db, sec_point, surround_sections)
