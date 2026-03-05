import pytest
import asyncio
from unittest.mock import patch
from datetime import datetime, timedelta

from server import app
from config import BoardConfig

from data.event import ServerEvent, ClientEvent
from data.board import Point, Section, SectionFlag, PointRange
from data.board.cursorboard import Color

from handler.board import BoardHandler
from handler.cursor import CursorHandler
from tests.utils import PytestTCM, assert_wait_event, assert_wait_call_if, build_tiles

CL_A = "TestClient_A"


# -------------------------
# Helpers
# -------------------------
def create_cursor_at_position(pos: Point):
    """Cursor를 특정 위치에 생성하는 헬퍼"""
    from data.cursor import Cursor
    origin_create = Cursor.create

    def create_cursor_effect(
        id: str,
        width: int = 0,
        height: int = 0,
        color: Color = Color.RED,
        **_kwargs,
    ):
        return origin_create(
            id,
            width=width,
            height=height,
            position=pos,
            color=color,
        )

    return create_cursor_effect


FLAG_BIT = 0b00100000
OPEN_BIT = 0b10000000
MINE_BIT = 0b01000000


def tile_state_matches(msg, point: Point, *, flag: bool | None = None, opened: bool | None = None, mine: bool | None = None):
    if msg.event.event_name != ServerEvent.TILES_STATE:
        return False
    for elem in msg.event.payload.tiles_li:
        if elem.range != PointRange(point, point):
            continue
        if len(elem.data) != 2:
            continue
        value = int(elem.data, 16)
        if flag is not None and bool(value & FLAG_BIT) != flag:
            return False
        if opened is not None and bool(value & OPEN_BIT) != opened:
            return False
        if mine is not None and bool(value & MINE_BIT) != mine:
            return False
        return True
    return False


def ignore_tile_state(conn_send, point: Point, *, flag: bool | None = None, opened: bool | None = None, mine: bool | None = None):
    """지뢰 해체 과정에서 발생하는 특정 TILES_STATE 1회를 소모한다."""
    assert_wait_call_if(
        conn_send,
        lambda msg: tile_state_matches(msg, point, flag=flag, opened=opened, mine=mine),
        timeout=3.0,
        error_msg="추가 TILES_STATE 이벤트를 받지 못함"
    )


# -------------------------
# Board maps
# -------------------------
async def mine_board_map(db):
    """
    Mine at (1, 1)
    """
    map_str = """\
####
####
#X##
####
"""
    tiles = build_tiles(map_str)
    sections = [Section(Point(0, 0), tiles.copy(), flag=SectionFlag.INTERACTIONAL)]
    from handler.board.storage import create_section
    for s in sections:
        await create_section(db, s)


async def chaining_board_map(db):
    """
    number=0 tile 포함 (1,1) - FT-003 map과 동일
    """
    map_str = """\
####
111#
.#1#
111#
"""
    tiles = build_tiles(map_str)
    sections = [Section(Point(0, 0), tiles.copy(), flag=SectionFlag.INTERACTIONAL)]
    from handler.board.storage import create_section
    for s in sections:
        await create_section(db, s)


# -------------------------
# FT-007
# -------------------------
@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=mine_board_map)
@pytest.mark.asyncio
async def test_ft007_dismantle_mine_scenario():
    """
    시나리오
    1) 사용자가 flag-tile을 홀딩(hold) 하여 지뢰 해체를 요청한다.
    2) tile이 opened 상태로 변경되고 지뢰 정보가 표시된다.
    3) 해체 완료 시 깃발이 자동 해제된다.
    4) 변경된 tile 정보가 전달된다.

    상태 변화
    - tile 상태: closed → opened
    - tile flag 상태: true → false
    """
    with PytestTCM(app).append_client(CL_A) as tcm:
        cl_a = tcm.get_client(CL_A)

        # Cursor를 (0, 1) 위치에 생성 (타일 (1,1)과 상호작용 가능)
        with patch("data.cursor.Cursor.create", side_effect=create_cursor_at_position(Point(0, 1))):
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 1, "height": 1, "color": Color.RED.value}
            })
            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)

        # 이전 event 소비
        cl_a.conn.send.await_args_list.clear()

        # (1,1) flag 설치
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.SET_FLAG.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        assert_wait_call_if(
            cl_a.conn.send,
            lambda msg: tile_state_matches(msg, Point(1, 1), flag=True, opened=False),
            timeout=3.0,
            error_msg="깃발 설치 후 (1,1) 타일의 flag 상태가 반영된 TILES_STATE를 받지 못함"
        )

        # 지뢰 해체 요청
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.DISMANTLE_MINE.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        # 깃발 해제로 인한 (1,1) 닫힌 타일 TILES_STATE 1회 무시
        ignore_tile_state(cl_a.conn.send, Point(1, 1), flag=False, opened=False, mine=True)

        assert_wait_call_if(
            cl_a.conn.send,
            lambda msg: tile_state_matches(msg, Point(1, 1), flag=False, opened=True, mine=True),
            timeout=3.0,
            error_msg="지뢰 해체 후 (1,1) 타일 opened/mine/flag 상태가 반영된 TILES_STATE를 받지 못함"
        )

        await asyncio.sleep(0.1)

        # 서버 내부 상태 확인
        tile_after = await BoardHandler.fetch_tile(Point(1, 1))
        assert tile_after.is_open is True
        assert tile_after.is_flag is False
        assert tile_after.is_mine is True


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=mine_board_map)
@pytest.mark.asyncio
async def test_ft007_grant_bomb_on_dismantle_mine():
    """
    지뢰 해체 시 cursor의 bomb 아이템이 1 증가한다.
    """
    with PytestTCM(app).append_client(CL_A) as tcm:
        cl_a = tcm.get_client(CL_A)

        with patch("data.cursor.Cursor.create", side_effect=create_cursor_at_position(Point(0, 1))):
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 1, "height": 1, "color": Color.RED.value}
            })
            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)

        cursor_before = await CursorHandler.get_by_id(CL_A)
        assert cursor_before.items.bomb == 0

        cl_a.conn.send.await_args_list.clear()

        cl_a.ws.send_json({
            "header": {"event": ClientEvent.SET_FLAG.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        assert_wait_call_if(
            cl_a.conn.send,
            lambda msg: tile_state_matches(msg, Point(1, 1), flag=True, opened=False),
            timeout=3.0,
            error_msg="깃발 설치 후 (1,1) 타일의 flag 상태가 반영된 TILES_STATE를 받지 못함"
        )

        cl_a.ws.send_json({
            "header": {"event": ClientEvent.DISMANTLE_MINE.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        ignore_tile_state(cl_a.conn.send, Point(1, 1), flag=False, opened=False, mine=True)

        assert_wait_call_if(
            cl_a.conn.send,
            lambda msg: tile_state_matches(msg, Point(1, 1), flag=False, opened=True, mine=True),
            timeout=3.0,
            error_msg="지뢰 해체 후 (1,1) 타일 opened/mine/flag 상태가 반영된 TILES_STATE를 받지 못함"
        )

        # grant_item 후 bomb=1인 CURSORS_STATE 대기
        # SET_FLAG에서도 CURSORS_STATE가 발생하므로 bomb 값으로 구분
        def cursors_state_with_bomb(msg):
            if msg.event.event_name != ServerEvent.CURSORS_STATE:
                return False
            for cursor in msg.event.payload.cursors:
                if cursor.id == CL_A and cursor.items.bomb == 1:
                    return True
            return False

        assert_wait_call_if(
            cl_a.conn.send,
            cursors_state_with_bomb,
            timeout=3.0,
            error_msg="bomb=1인 CURSORS_STATE를 받지 못함"
        )


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=chaining_board_map)
@pytest.mark.asyncio
async def test_ft007_chaining_when_number_zero():
    """
    시나리오
    - number가 0인 타일이 opened 되는 경우 chaining이 발생한다.
    - chaining에 포함된 타일들의 상태가 전달된다.

    상태 변화
    - tile flag 상태: true → false
    - chaining 범위 내 타일들이 opened 된다.
    """
    with PytestTCM(app).append_client(CL_A) as tcm:
        cl_a = tcm.get_client(CL_A)

        # Cursor를 (0, 1) 위치에 생성 (타일 (1,1)과 상호작용 가능)
        with patch("data.cursor.Cursor.create", side_effect=create_cursor_at_position(Point(0, 1))):
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 1, "height": 1, "color": Color.RED.value}
            })
            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)

        cl_a.conn.send.await_args_list.clear()

        # (1,1) flag 설치
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.SET_FLAG.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        assert_wait_call_if(
            cl_a.conn.send,
            lambda msg: tile_state_matches(msg, Point(1, 1), flag=True, opened=False),
            timeout=3.0,
            error_msg="깃발 설치 후 (1,1) 타일의 flag 상태가 반영된 TILES_STATE를 받지 못함"
        )

        # 해체 요청 → chaining
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.DISMANTLE_MINE.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        # 깃발 해제로 인한 (1,1) 닫힌 타일 TILES_STATE 1회 무시
        ignore_tile_state(cl_a.conn.send, Point(1, 1), flag=False, opened=False, mine=False)

        expected_points = [
            Point(1, 2),
            Point(0, 0),
            Point(1, 1),
            Point(1, 0),
            Point(0, 2),
        ]

        for p in expected_points:
            assert_wait_call_if(
                cl_a.conn.send,
                lambda msg, p=p: tile_state_matches(msg, p, flag=False, opened=True, mine=False),
                timeout=3.0,
                error_msg=f"chaining 결과 타일 {p}에 대한 TILES_STATE를 받지 못함"
            )

        await asyncio.sleep(0.1)

        center = await BoardHandler.fetch_tile(Point(1, 1))
        assert center.is_open is True
        assert center.is_flag is False


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=mine_board_map)
@pytest.mark.asyncio
async def test_ft007_business_rule_dead_cursor_cannot_dismantle():
    """
    비즈니스 규칙
    - 죽은 cursor는 지뢰 해체를 수행할 수 없다.

    상태 변화
    - 규칙 위반 시 타일 상태는 변하지 않는다.
    """
    with PytestTCM(app).append_client(CL_A) as tcm:
        cl_a = tcm.get_client(CL_A)

        # Cursor를 (0, 1) 위치에 생성
        with patch("data.cursor.Cursor.create", side_effect=create_cursor_at_position(Point(0, 1))):
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 1, "height": 1, "color": Color.RED.value}
            })
            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)

        cl_a.conn.send.await_args_list.clear()

        # (1,1) flag 설치
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.SET_FLAG.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        assert_wait_call_if(
            cl_a.conn.send,
            lambda msg: tile_state_matches(msg, Point(1, 1), flag=True, opened=False),
            timeout=3.0,
            error_msg="깃발 설치 후 (1,1) 타일의 flag 상태가 반영된 TILES_STATE를 받지 못함"
        )

        # Cursor를 죽은 상태로 변경
        cursor = await CursorHandler.get_by_id(CL_A)
        cursor.active_at = datetime.now() + timedelta(hours=1)
        await CursorHandler.update(cursor)

        before = await BoardHandler.fetch_tile(Point(1, 1))

        # 지뢰 해체 요청
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.DISMANTLE_MINE.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        await asyncio.sleep(0.1)

        after = await BoardHandler.fetch_tile(Point(1, 1))
        assert after == before


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=mine_board_map)
@pytest.mark.asyncio
async def test_ft007_business_rule_flag_tile_only():
    """
    비즈니스 규칙
    - flag-tile에서만 지뢰 해체를 요청할 수 있다.

    상태 변화
    - 규칙 위반 시 타일 상태는 변하지 않는다.
    """
    with PytestTCM(app).append_client(CL_A) as tcm:
        cl_a = tcm.get_client(CL_A)

        # Cursor를 (0, 1) 위치에 생성
        with patch("data.cursor.Cursor.create", side_effect=create_cursor_at_position(Point(0, 1))):
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 1, "height": 1, "color": Color.RED.value}
            })
            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)

        cl_a.conn.send.await_args_list.clear()

        before = await BoardHandler.fetch_tile(Point(1, 1))
        assert before.is_flag is False
        assert before.is_open is False

        # flag 없이 지뢰 해체 요청
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.DISMANTLE_MINE.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        await asyncio.sleep(0.1)

        after = await BoardHandler.fetch_tile(Point(1, 1))
        assert after == before
