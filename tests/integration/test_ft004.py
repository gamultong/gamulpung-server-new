import pytest
import asyncio
from server import app
from data.event import ServerEvent, ClientEvent
from data.board import Point, Section, SectionFlag
from handler.board import BoardHandler
from handler.cursor import CursorHandler
from handler.connection import ConnectionHandler
from tests.utils.internal.conn_mock import PytestTCM
from tests.utils.internal.wait_call import assert_wait_event
from tests.integration.map.builder import build_tiles
from unittest.mock import patch
from config import BoardConfig
from datetime import datetime, timedelta
import time

CL_A = "TestClient_A"


async def simple_board_map(db):
    """
    Simple 4x4 board for basic tests:
    y=3: # # # #
    y=2: # # # #
    y=1: 1 # 1 #
    y=0: # # # #
    """
    map_str = """\
####
####
1#1#
####
"""
    tiles = build_tiles(map_str)
    sections = [Section(Point(0, 0), tiles.copy(), flag=SectionFlag.INTERACTIONAL)]
    from handler.board.storage import create_section
    for section in sections:
        await create_section(db, section)


async def flagged_board_map(db):
    """
    Board with flagged tile at (1, 1):
    y=3: # # # #
    y=2: # # # #
    y=1: 1 F 1 #
    y=0: # # # #
    """
    map_str = """\
####
####
1F1#
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
def test_ft004_set_flag_scenario():
    """
    FT-004 깃발 설치 시나리오 검증:
    1. 사용자가 깃발이 없는 닫힌 타일에 깃발 설치를 요청한다.
    2. 타일에 깃발이 설치된다.
    3. 변경된 타일 정보가 전달된다.
    """
    with PytestTCM(app).append_client(CL_A) as tcm:
        cl_a = tcm.get_client(CL_A)

        # Cursor를 (0, 1) 위치에 생성
        with patch("data.cursor.Cursor.create", side_effect=create_cursor_at_position(Point(0, 1))):
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 1, "height": 1}
            })

            cl_a.ws.send_json({
                "header": {"event": ClientEvent.SET_WINDOW.value},
                "payload": {"width": 1, "height": 1}
            })

            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE, timeout=3.0)
            time.sleep(0.1)

        # 시나리오 1: 닫힌 타일 (1, 1)에 깃발 설치 요청
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.SET_FLAG.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        # 시나리오 3: TILES_STATE 이벤트 수신 확인
        assert_wait_event(cl_a.conn.send, ServerEvent.TILES_STATE, timeout=3.0)
        time.sleep(0.1)

        # 시나리오 2: 서버 상태 검증 - 타일에 깃발이 설치됨
        tile = asyncio.run(BoardHandler.fetch_tile(Point(1, 1)))
        assert tile.is_flag == True, "타일에 깃발이 설치되어야 함"


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=flagged_board_map)
def test_ft004_unset_flag_scenario():
    """
    FT-004 깃발 해제 시나리오 검증:
    1. 사용자가 깃발이 있는 타일에 깃발 해제를 요청한다.
    2. 타일의 깃발이 제거된다.
    3. 변경된 타일 정보가 전달된다.
    """
    with PytestTCM(app).append_client(CL_A) as tcm:
        cl_a = tcm.get_client(CL_A)

        # Cursor를 (0, 1) 위치에 생성
        with patch("data.cursor.Cursor.create", side_effect=create_cursor_at_position(Point(0, 1))):
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 1, "height": 1}
            })

            cl_a.ws.send_json({
                "header": {"event": ClientEvent.SET_WINDOW.value},
                "payload": {"width": 1, "height": 1}
            })

            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE, timeout=3.0)
            time.sleep(0.1)

        # 시나리오 1: 깃발이 있는 타일 (1, 1)에 깃발 해제 요청
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.SET_FLAG.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        # 시나리오 3: TILES_STATE 이벤트 수신 확인
        assert_wait_event(cl_a.conn.send, ServerEvent.TILES_STATE, timeout=3.0)
        time.sleep(0.1)

        # 시나리오 2: 서버 상태 검증 - 타일의 깃발이 제거됨
        tile = asyncio.run(BoardHandler.fetch_tile(Point(1, 1)))
        assert tile.is_flag == False, "타일의 깃발이 제거되어야 함"


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=simple_board_map)
def test_ft004_business_rule_toggle_behavior():
    """
    비즈니스 규칙 검증:
    - 깃발이 있으면 해제, 없으면 설치 (토글)
    """
    with PytestTCM(app).append_client(CL_A) as tcm:
        cl_a = tcm.get_client(CL_A)

        # Cursor를 (0, 1) 위치에 생성
        with patch("data.cursor.Cursor.create", side_effect=create_cursor_at_position(Point(0, 1))):
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 1, "height": 1}
            })

            cl_a.ws.send_json({
                "header": {"event": ClientEvent.SET_WINDOW.value},
                "payload": {"width": 1, "height": 1}
            })

            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE, timeout=3.0)
            time.sleep(0.1)

        # 첫 번째 SET_FLAG: 깃발 설치
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.SET_FLAG.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        assert_wait_event(cl_a.conn.send, ServerEvent.TILES_STATE, timeout=3.0)
        time.sleep(0.1)

        tile_after_set = asyncio.run(BoardHandler.fetch_tile(Point(1, 1)))
        assert tile_after_set.is_flag == True, "깃발이 설치되어야 함"

        # 두 번째 SET_FLAG: 깃발 해제
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.SET_FLAG.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        assert_wait_event(cl_a.conn.send, ServerEvent.TILES_STATE, timeout=3.0)
        time.sleep(0.1)

        tile_after_unset = asyncio.run(BoardHandler.fetch_tile(Point(1, 1)))
        assert tile_after_unset.is_flag == False, "깃발이 해제되어야 함"


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=simple_board_map)
def test_ft004_business_rule_dead_cursor():
    """
    비즈니스 규칙 검증:
    - 죽은 cursor는 깃발을 설치/해제할 수 없다.
    """
    with PytestTCM(app).append_client(CL_A) as tcm:
        cl_a = tcm.get_client(CL_A)

        # Cursor를 (0, 1) 위치에 생성
        with patch("data.cursor.Cursor.create", side_effect=create_cursor_at_position(Point(0, 1))):
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 1, "height": 1}
            })

            cl_a.ws.send_json({
                "header": {"event": ClientEvent.SET_WINDOW.value},
                "payload": {"width": 1, "height": 1}
            })

            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE, timeout=3.0)
            time.sleep(0.1)

        # Cursor를 죽은 상태로 설정
        cursor = asyncio.run(CursorHandler.get_by_id(CL_A))
        cursor.active_at = datetime.now() + timedelta(seconds=10)
        CursorHandler.cursor_dict[CL_A] = cursor

        # 죽은 상태에서 깃발 설치 시도
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.SET_FLAG.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        time.sleep(0.5)

        # 타일 상태 확인 - 깃발이 설치되지 않아야 함
        tile = asyncio.run(BoardHandler.fetch_tile(Point(1, 1)))
        assert tile.is_flag == False, "죽은 커서는 깃발을 설치할 수 없음"


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=simple_board_map)
def test_ft004_state_change_flag_installed():
    """
    상태 변화 검증:
    - 깃발 설치: is_flag: false → true
    """
    with PytestTCM(app).append_client(CL_A) as tcm:
        cl_a = tcm.get_client(CL_A)

        # Cursor를 (0, 1) 위치에 생성
        with patch("data.cursor.Cursor.create", side_effect=create_cursor_at_position(Point(0, 1))):
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 1, "height": 1}
            })

            cl_a.ws.send_json({
                "header": {"event": ClientEvent.SET_WINDOW.value},
                "payload": {"width": 1, "height": 1}
            })

            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE, timeout=3.0)
            time.sleep(0.1)

        # Before: 깃발이 없는 상태
        tile_before = asyncio.run(BoardHandler.fetch_tile(Point(1, 1)))
        assert tile_before.is_flag == False, "초기 상태에서 깃발이 없어야 함"

        # 깃발 설치
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.SET_FLAG.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        assert_wait_event(cl_a.conn.send, ServerEvent.TILES_STATE, timeout=3.0)
        time.sleep(0.1)

        # After: 깃발이 설치된 상태
        tile_after = asyncio.run(BoardHandler.fetch_tile(Point(1, 1)))
        assert tile_after.is_flag == True, "깃발이 설치되어야 함"


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=flagged_board_map)
def test_ft004_state_change_flag_removed():
    """
    상태 변화 검증:
    - 깃발 해제: is_flag: true → false
    """
    with PytestTCM(app).append_client(CL_A) as tcm:
        cl_a = tcm.get_client(CL_A)

        # Cursor를 (0, 1) 위치에 생성
        with patch("data.cursor.Cursor.create", side_effect=create_cursor_at_position(Point(0, 1))):
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 1, "height": 1}
            })

            cl_a.ws.send_json({
                "header": {"event": ClientEvent.SET_WINDOW.value},
                "payload": {"width": 1, "height": 1}
            })

            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE, timeout=3.0)
            time.sleep(0.1)

        # Before: 깃발이 있는 상태
        tile_before = asyncio.run(BoardHandler.fetch_tile(Point(1, 1)))
        assert tile_before.is_flag == True, "초기 상태에서 깃발이 있어야 함"

        # 깃발 해제
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.SET_FLAG.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        assert_wait_event(cl_a.conn.send, ServerEvent.TILES_STATE, timeout=3.0)
        time.sleep(0.1)

        # After: 깃발이 제거된 상태
        tile_after = asyncio.run(BoardHandler.fetch_tile(Point(1, 1)))
        assert tile_after.is_flag == False, "깃발이 제거되어야 함"
