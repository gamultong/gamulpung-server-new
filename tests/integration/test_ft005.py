import pytest
from server import app
from data.event import ServerEvent, ClientEvent
from data.board import Point, Section, SectionFlag, PointRange
from data.cursor_board import Color
from handler.cursor import CursorHandler
from tests.utils import PytestTCM, assert_wait_event, assert_wait_call_if, build_tiles, create_cursor_at_position
from unittest.mock import patch
from config import BoardConfig

CL_A = "TestClient_A"


async def simple_board_map(db):
    """
    Simple 4x4 board for basic tests:
    y=3: # # # #
    y=2: # # # #
    y=1: # # # #
    y=0: # # # #
    """
    map_str = """\
####
####
####
####
"""
    tiles = build_tiles(map_str)
    sections = [Section(Point(0, 0), tiles.copy(), flag=SectionFlag.INTERACTIONAL)]
    from handler.board.storage import create_section
    for section in sections:
        await create_section(db, section)




@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=simple_board_map)
@pytest.mark.asyncio
async def test_ft005_set_window_scenario():
    """
    FT-005 시야 설정 시나리오 검증:
    1. 사용자가 시야 크기(width, height)를 설정한다.
    2. 변경된 시야 범위에 따라 tile 정보가 업데이트된다.
    """
    with PytestTCM(app).append_client(CL_A) as tcm:
        cl_a = tcm.get_client(CL_A)

        # Cursor를 (0, 0) 위치에 생성 (초기 window 1x1)
        with patch("data.cursor.Cursor.create", side_effect=create_cursor_at_position(Point(0, 0))):
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 1, "height": 1, "color": Color.RED.value}
            })

            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)

        # 이전 event 소비
        cl_a.conn.send.await_args_list.clear()

        # 시나리오 1: 시야 크기를 3x3으로 설정
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.SET_WINDOW.value},
            "payload": {"width": 3, "height": 3}
        })

        # 시나리오 2: TILES_STATE 이벤트 수신 및 검증 - 변경된 시야 범위 확인
        # position (0, 0), width=3, height=3 → range: Point(-3, 3) to Point(3, -3)
        expected_range = PointRange(
            top_left=Point(-3, 3),
            bottom_right=Point(3, -3)
        )

        assert_wait_call_if(
            cl_a.conn.send,
            lambda msg: (
                msg.event.event_name == ServerEvent.TILES_STATE and
                len(msg.event.payload.tiles_li) > 0 and
                msg.event.payload.tiles_li[0].range == expected_range
            ),
            timeout=3.0,
            error_msg="TILES_STATE의 range가 변경된 window 크기를 반영하지 않음"
        )


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=simple_board_map)
@pytest.mark.asyncio
async def test_ft005_business_rule_connected_users_only():
    """
    비즈니스 규칙 검증:
    - 접속중인 사용자만 가능 (Cursor가 없으면 시야 설정 불가)
    """
    with PytestTCM(app).append_client(CL_A) as tcm:
        cl_a = tcm.get_client(CL_A)

        # Cursor 생성 없이 바로 SET_WINDOW 요청
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.SET_WINDOW.value},
            "payload": {"width": 5, "height": 5}
        })

        # Cursor가 생성되지 않았는지 확인
        try:
            await CursorHandler.get_by_id(CL_A)
            assert False, "Cursor가 생성되지 않아야 함"
        except KeyError:
            pass  # 예상된 동작: Cursor 없음


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=simple_board_map)
@pytest.mark.asyncio
async def test_ft005_state_change_window_size():
    """
    상태 변화 검증:
    - cursor의 시야 범위 설정이 변경된다 (width, height)
    """
    with PytestTCM(app).append_client(CL_A) as tcm:
        cl_a = tcm.get_client(CL_A)

        # Cursor를 (0, 0) 위치에 생성 (초기 window 2x2)
        with patch("data.cursor.Cursor.create", side_effect=create_cursor_at_position(Point(0, 0))):
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 2, "height": 2, "color": Color.RED.value}
            })

            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)

        # Before: 시야 크기 확인
        cursor_before = await CursorHandler.get_by_id(CL_A)
        assert cursor_before.width == 2, "초기 width가 2여야 함"
        assert cursor_before.height == 2, "초기 height가 2여야 함"

        # 이전 event 소비
        cl_a.conn.send.await_args_list.clear()

        # SET_WINDOW 요청
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.SET_WINDOW.value},
            "payload": {"width": 5, "height": 5}
        })

        # After: TILES_STATE 이벤트의 range로 시야 크기 변경 검증
        # position (0, 0), width=5, height=5 → range: Point(-5, 5) to Point(5, -5)
        expected_range = PointRange(
            top_left=Point(-5, 5),
            bottom_right=Point(5, -5)
        )

        assert_wait_call_if(
            cl_a.conn.send,
            lambda msg: (
                msg.event.event_name == ServerEvent.TILES_STATE and
                len(msg.event.payload.tiles_li) > 0 and
                msg.event.payload.tiles_li[0].range == expected_range
            ),
            timeout=3.0,
            error_msg="TILES_STATE의 range가 변경된 window 크기를 반영하지 않음"
        )


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=simple_board_map)
@pytest.mark.asyncio
async def test_ft005_state_change_tiles_state_updated():
    """
    상태 변화 검증:
    - 변경된 시야 범위에 따라 tile 정보가 업데이트된다 (TILES_STATE의 range 확인)
    """
    with PytestTCM(app).append_client(CL_A) as tcm:
        cl_a = tcm.get_client(CL_A)

        # Cursor를 (0, 0) 위치에 생성 (초기 window 1x1)
        with patch("data.cursor.Cursor.create", side_effect=create_cursor_at_position(Point(0, 0))):
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 1, "height": 1, "color": Color.RED.value}
            })

            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)

        # SET_WINDOW 요청 (3x3으로 변경)
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.SET_WINDOW.value},
            "payload": {"width": 3, "height": 3}
        })

        # TILES_STATE 이벤트의 range 검증
        # position (0, 0), width=3, height=3 → range: Point(-3, 3) to Point(3, -3)
        expected_range = PointRange(
            top_left=Point(-3, 3),
            bottom_right=Point(3, -3)
        )

        assert_wait_call_if(
            cl_a.conn.send,
            lambda msg: (
                msg.event.event_name == ServerEvent.TILES_STATE and
                len(msg.event.payload.tiles_li) > 0 and
                msg.event.payload.tiles_li[0].range == expected_range
            ),
            timeout=3.0,
            error_msg="TILES_STATE의 range가 변경된 window 크기를 반영하지 않음"
        )


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=simple_board_map)
@pytest.mark.asyncio
async def test_ft005_cursor_state_on_window_change():
    """
    상태 변화 검증:
    - 시야 변경 시 새로운 시야 범위의 커서 정보가 전달된다 (CURSORS_STATE)
    """
    with PytestTCM(app).append_client(CL_A) as tcm:
        cl_a = tcm.get_client(CL_A)

        # Cursor를 (0, 0) 위치에 생성 (초기 window 1x1)
        with patch("data.cursor.Cursor.create", side_effect=create_cursor_at_position(Point(0, 0))):
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 1, "height": 1, "color": Color.RED.value}
            })

            assert_wait_event(cl_a.conn.send, ServerEvent.TILES_STATE)

        # 이전 event 소비
        cl_a.conn.send.await_args_list.clear()

        # 시야 크기를 3x3으로 설정
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.SET_WINDOW.value},
            "payload": {"width": 3, "height": 3}
        })

        # TILES_STATE 이벤트 수신 확인
        assert_wait_event(cl_a.conn.send, ServerEvent.TILES_STATE, timeout=3.0)

        # CURSORS_STATE 이벤트 수신 확인
        assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE, timeout=3.0)


async def mine_board_map(db):
    """
    Closed mine board (X 주변 closed 타일에 number가 자동 계산됨):
    y=3: # # # #
    y=2: # X # #
    y=1: # # # #
    y=0: # # # #
    """
    map_str = """\
####
#X##
####
####
"""
    tiles = build_tiles(map_str)
    sections = [Section(Point(0, 0), tiles.copy(), flag=SectionFlag.INTERACTIONAL)]
    from handler.board.storage import create_section
    for section in sections:
        await create_section(db, section)


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=mine_board_map)
@pytest.mark.asyncio
async def test_ft005_business_rule_closed_tile_info_is_masked():
    """
    비즈니스 규칙 검증 (RFC-006):
    - 닫힌 타일의 mine·number 정보는 클라이언트로 전송되지 않아야 함
    """
    with PytestTCM(app).append_client(CL_A) as tcm:
        cl_a = tcm.get_client(CL_A)

        # Cursor를 (1, 1) 위치에 생성 후 시야를 1x1로 설정 → 지뢰 (1, 2) 포함
        with patch("data.cursor.Cursor.create", side_effect=create_cursor_at_position(Point(1, 1))):
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 1, "height": 1, "color": Color.RED.value}
            })
            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)

        cl_a.conn.send.await_args_list.clear()

        cl_a.ws.send_json({
            "header": {"event": ClientEvent.SET_WINDOW.value},
            "payload": {"width": 1, "height": 1}
        })

        received = {}

        def capture_tiles_state(msg):
            if msg.event.event_name == ServerEvent.TILES_STATE and len(msg.event.payload.tiles_li) > 0:
                received["data"] = msg.event.payload.tiles_li[0].data
                return True
            return False

        assert_wait_call_if(
            cl_a.conn.send,
            capture_tiles_state,
            timeout=3.0,
            error_msg="TILES_STATE 이벤트를 받지 못함"
        )

        # 비트 구조는 RFC-006 참고: open(7) mine(6) flag(5) color(4-3) number(2-0)
        opened = 0b10000000
        mine_or_number = 0b01000111
        for idx, b in enumerate(bytes.fromhex(received["data"])):
            if b & opened:
                continue
            assert b & mine_or_number == 0, \
                f"닫힌 타일의 mine·number가 전송됨 | idx:{idx}, byte:{b:08b}"
