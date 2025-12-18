import pytest
import asyncio
from server import app
from data.event import ServerEvent, ClientEvent
from data.board import Point, Section, SectionFlag, PointRange
from handler.board import BoardHandler
from handler.cursor import CursorHandler
from handler.connection import ConnectionHandler
from tests.utils import PytestTCM, assert_wait_event, assert_wait_call_if, build_tiles
from unittest.mock import patch
from config import BoardConfig
import time

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


def create_cursor_at_position(pos: Point):
    """Cursor를 특정 위치에 생성하는 헬퍼"""
    from data.cursor import Cursor
    origin_create = Cursor.create

    def create_cursor_effect(id: str, width: int = 0, height: int = 0, **kwargs):
        return origin_create(id, width=width, height=height, position=pos)

    return create_cursor_effect


@pytest.fixture(autouse=True)
def cleanup_db():
    """테스트 전후 DB 파일 및 핸들러 상태 정리"""
    import os
    db_path = "board.db"
    # 테스트 전 정리
    if os.path.exists(db_path):
        os.remove(db_path)
    CursorHandler.cursor_dict.clear()
    ConnectionHandler.conn_dict.clear()
    yield
    # 테스트 후 정리 - aiosqlite 스레드 정리 대기
    time.sleep(0.1)
    if os.path.exists(db_path):
        os.remove(db_path)
    CursorHandler.cursor_dict.clear()
    ConnectionHandler.conn_dict.clear()


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=simple_board_map)
def test_ft005_set_window_scenario():
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
                "payload": {"width": 1, "height": 1}
            })

            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE, timeout=3.0)
            time.sleep(0.1)

        # 시나리오 1: 시야 크기를 3x3으로 설정
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.SET_WINDOW.value},
            "payload": {"width": 3, "height": 3}
        })

        # 시나리오 2: TILES_STATE 이벤트 수신 확인
        assert_wait_event(cl_a.conn.send, ServerEvent.TILES_STATE, timeout=3.0)
        time.sleep(0.1)

        # 서버 상태 검증 - 시야 크기가 변경됨
        cursor = asyncio.run(CursorHandler.get_by_id(CL_A))
        assert cursor.width == 3, "시야 width가 3으로 설정되어야 함"
        assert cursor.height == 3, "시야 height가 3으로 설정되어야 함"


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=simple_board_map)
def test_ft005_business_rule_connected_users_only():
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

        time.sleep(0.5)

        # Cursor가 생성되지 않았는지 확인
        try:
            asyncio.run(CursorHandler.get_by_id(CL_A))
            assert False, "Cursor가 생성되지 않아야 함"
        except KeyError:
            pass  # 예상된 동작: Cursor 없음


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=simple_board_map)
def test_ft005_state_change_window_size():
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
                "payload": {"width": 2, "height": 2}
            })

            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE, timeout=3.0)
            time.sleep(0.1)

        # Before: 시야 크기 확인
        cursor_before = asyncio.run(CursorHandler.get_by_id(CL_A))
        assert cursor_before.width == 2, "초기 width가 2여야 함"
        assert cursor_before.height == 2, "초기 height가 2여야 함"

        # SET_WINDOW 요청
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.SET_WINDOW.value},
            "payload": {"width": 5, "height": 5}
        })

        assert_wait_event(cl_a.conn.send, ServerEvent.TILES_STATE, timeout=3.0)
        time.sleep(0.1)

        # After: 시야 크기 확인
        cursor_after = asyncio.run(CursorHandler.get_by_id(CL_A))
        assert cursor_after.width == 5, "변경된 width가 5여야 함"
        assert cursor_after.height == 5, "변경된 height가 5여야 함"


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=simple_board_map)
def test_ft005_state_change_tiles_state_updated():
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
                "payload": {"width": 1, "height": 1}
            })

            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE, timeout=3.0)
            time.sleep(0.1)

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
