import pytest
import asyncio
from server import app
from data.event import ServerEvent, ClientEvent
from data.board import Point, Tile, Tiles, Section, SectionFlag
from handler.cursor import CursorHandler
from handler.connection import ConnectionHandler
from handler.board import BoardHandler
from tests.utils.internal.conn_mock import PytestTCM
from tests.utils.internal.wait_call import assert_wait_event
from unittest.mock import patch
from config import BoardConfig
from datetime import datetime, timedelta
import time

CL_A = "TestClient_A"
CL_B = "TestClient_B"

# 테스트용 타일 정의
TILE = Tile.create(is_flag=False, is_mine=False, is_open=False, number=0)
CLSE = TILE.data  # Closed tile
OPEN = TILE.changed(is_open=True).data  # Opened tile
NUM1 = TILE.changed(number=1).data  # Numbered tile
MINE = TILE.changed(is_mine=True).data  # Mine tile
FLAG = TILE.changed(is_flag=True).data  # Flagged tile


async def simple_board_map(db):
    """
    Simple 4x4 board for basic tests:
    y=3: CLSE CLSE CLSE CLSE
    y=2: NUM1 NUM1 NUM1 CLSE
    y=1: OPEN CLSE NUM1 CLSE
    y=0: NUM1 NUM1 NUM1 CLSE
    """
    data = [
        CLSE, CLSE, CLSE, CLSE,  # y=3 (맨 위)
        NUM1, NUM1, NUM1, CLSE,  # y=2
        OPEN, CLSE, NUM1, CLSE,  # y=1 (OPEN이 여기)
        NUM1, NUM1, NUM1, CLSE,  # y=0 (맨 아래)
    ]
    tiles = Tiles(bytearray(data), 4, 4)
    sections = [Section(Point(0, 0), tiles.copy(), flag=SectionFlag.INTERACTIONAL)]
    from handler.board.storage import create_section
    for section in sections:
        await create_section(db, section)


async def mine_board_map(db):
    """
    Board with mine at (1, 1):
    y=3: CLSE CLSE CLSE CLSE
    y=2: CLSE CLSE CLSE CLSE
    y=1: NUM1 MINE NUM1 CLSE
    y=0: CLSE CLSE CLSE CLSE
    """
    data = [
        CLSE, CLSE, CLSE, CLSE,  # y=3 (맨 위)
        CLSE, CLSE, CLSE, CLSE,  # y=2
        NUM1, MINE, NUM1, CLSE,  # y=1 (MINE이 여기)
        CLSE, CLSE, CLSE, CLSE,  # y=0 (맨 아래)
    ]
    tiles = Tiles(bytearray(data), 4, 4)
    sections = [Section(Point(0, 0), tiles.copy(), flag=SectionFlag.INTERACTIONAL)]
    from handler.board.storage import create_section
    for section in sections:
        await create_section(db, section)


async def flagged_board_map(db):
    """
    Board with flagged tile at (1, 1):
    y=3: CLSE CLSE CLSE CLSE
    y=2: CLSE CLSE CLSE CLSE
    y=1: NUM1 FLAG NUM1 CLSE
    y=0: CLSE CLSE CLSE CLSE
    """
    data = [
        CLSE, CLSE, CLSE, CLSE,  # y=3 (맨 위)
        CLSE, CLSE, CLSE, CLSE,  # y=2
        NUM1, FLAG, NUM1, CLSE,  # y=1 (FLAG이 여기)
        CLSE, CLSE, CLSE, CLSE,  # y=0 (맨 아래)
    ]
    tiles = Tiles(bytearray(data), 4, 4)
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
    # 테스트 후 정리
    if os.path.exists(db_path):
        os.remove(db_path)
    CursorHandler.cursor_dict.clear()
    ConnectionHandler.conn_dict.clear()


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=simple_board_map)
def test_ft003_open_tile_scenario():
    """
    FT-003 타일 열기 시나리오 검증:
    1. 사용자가 closed-tile을 클릭하여 열기를 요청한다.
    2. tile이 opened 상태로 변경되고 지뢰 정보가 표시된다.
    """
    with PytestTCM(app).append_client(CL_A) as tcm:
        cl_a = tcm.get_client(CL_A)

        # Cursor를 (0, 1) 위치에 생성 (타일 (1,1)과 상호작용 가능)
        with patch("data.cursor.Cursor.create", side_effect=create_cursor_at_position(Point(0, 1))):
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 1, "height": 1}
            })

            cl_a.ws.send_json({
                "header": {"event": ClientEvent.SET_WINDOW.value},
                "payload": {"width": 1, "height": 1}
            })

            # Cursor 생성 완료 대기
            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE, timeout=3.0)
            time.sleep(0.1)

        # 시나리오 1: 사용자가 closed-tile (1,1) 클릭
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.OPEN_TILES.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        # 시나리오 2: tile이 opened 상태로 변경되고 지뢰 정보 표시
        # TILES_STATE 이벤트 수신 검증
        assert_wait_event(cl_a.conn.send, ServerEvent.TILES_STATE, timeout=3.0)
        time.sleep(0.5)

        # 서버 상태 검증: tile이 opened 상태로 변경됨
        tile = asyncio.run(BoardHandler.fetch_tile(Point(1, 1)))
        assert tile.is_open == True, "타일이 열린 상태여야 함"


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=flagged_board_map)
def test_ft003_business_rule_flagged_tile():
    """
    비즈니스 규칙 검증:
    - flag가 설치된 tile은 열 수 없다.
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

        # 깃발이 설치된 타일 (1,1) 열기 시도
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.OPEN_TILES.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        # 타일이 열리지 않았는지 검증
        time.sleep(0.5)

        tile = asyncio.run(BoardHandler.fetch_tile(Point(1, 1)))
        assert tile.is_open == False, "깃발이 설치된 타일은 열리지 않아야 함"
        assert tile.is_flag == True, "깃발이 여전히 설치되어 있어야 함"


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=simple_board_map)
def test_ft003_business_rule_closed_tile_only():
    """
    비즈니스 규칙 검증:
    - closed-tile만 열기 가능하다.
    """
    with PytestTCM(app).append_client(CL_A) as tcm:
        cl_a = tcm.get_client(CL_A)

        # Cursor를 (0, 1) 위치에 생성 (이미 열린 타일 (0,1)와 상호작용 가능)
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

        # 초기 점수 확인
        cursor_before = asyncio.run(CursorHandler.get_by_id(CL_A))
        score_before = cursor_before.score

        # 이미 열린 타일 (0,1) 열기 시도
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.OPEN_TILES.value},
            "payload": {"position": {"x": 0, "y": 1}}
        })

        # 점수가 변경되지 않았는지 검증
        time.sleep(0.5)

        cursor_after = asyncio.run(CursorHandler.get_by_id(CL_A))
        assert cursor_after.score == score_before, "이미 열린 타일을 다시 열면 점수가 변하지 않아야 함"


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=simple_board_map)
def test_ft003_business_rule_dead_cursor():
    """
    비즈니스 규칙 검증:
    - 죽은 cursor는 타일을 열 수 없다.
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

        # Cursor를 죽은 상태로 설정 (active_at을 미래 시간으로)
        cursor = asyncio.run(CursorHandler.get_by_id(CL_A))
        cursor.active_at = datetime.now() + timedelta(seconds=10)
        CursorHandler.cursor_dict[CL_A] = cursor

        # 죽은 상태에서 타일 열기 시도
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.OPEN_TILES.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        # 타일이 열리지 않았는지 검증
        time.sleep(0.5)

        tile = asyncio.run(BoardHandler.fetch_tile(Point(1, 1)))
        assert tile.is_open == False, "죽은 커서는 타일을 열 수 없어야 함"


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=mine_board_map)
def test_ft003_state_change_tile_opened():
    """
    상태 변화 검증:
    - tile 상태: closed → opened
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

        # 상태 변화 전: closed 상태 확인
        tile_before = asyncio.run(BoardHandler.fetch_tile(Point(0, 1)))
        assert tile_before.is_open == False, "타일이 닫혀있어야 함"

        # 타일 열기
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.OPEN_TILES.value},
            "payload": {"position": {"x": 0, "y": 1}}
        })

        # TILES_STATE 이벤트 대기
        assert_wait_event(cl_a.conn.send, ServerEvent.TILES_STATE, timeout=3.0)
        time.sleep(0.5)

        # 상태 변화 후: opened 상태 확인
        tile_after = asyncio.run(BoardHandler.fetch_tile(Point(0, 1)))
        assert tile_after.is_open == True, "타일이 열려있어야 함"


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=mine_board_map)
def test_ft003_state_change_explosion():
    """
    상태 변화 검증:
    - 지뢰 발견 시 cursor 상태 변경 (explosion)
    """
    with PytestTCM(app).append_client(CL_A).append_client(CL_B) as tcm:
        cl_a = tcm.get_client(CL_A)
        cl_b = tcm.get_client(CL_B)

        # Cursor A를 (0, 1) 위치에 생성 (지뢰 옆)
        with patch("data.cursor.Cursor.create", side_effect=create_cursor_at_position(Point(0, 1))):
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 5, "height": 5}
            })

            cl_a.ws.send_json({
                "header": {"event": ClientEvent.SET_WINDOW.value},
                "payload": {"width": 5, "height": 5}
            })

            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE, timeout=3.0)
            time.sleep(0.1)

        # Cursor B를 (3, 3) 위치에 생성 (지뢰 폭발 범위 밖)
        with patch("data.cursor.Cursor.create", side_effect=create_cursor_at_position(Point(3, 3))):
            cl_b.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 5, "height": 5}
            })

            cl_b.ws.send_json({
                "header": {"event": ClientEvent.SET_WINDOW.value},
                "payload": {"width": 5, "height": 5}
            })

            assert_wait_event(cl_b.conn.send, ServerEvent.CURSORS_STATE, timeout=3.0)
            time.sleep(0.1)

        # Cursor A 상태 확인 (explosion 전)
        cursor_a_before = asyncio.run(CursorHandler.get_by_id(CL_A))
        assert cursor_a_before.is_alive == True, "커서가 살아있어야 함"

        # 지뢰 타일 (1, 1) 열기
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.OPEN_TILES.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        # EXPLOSION 이벤트 대기
        assert_wait_event(cl_a.conn.send, ServerEvent.EXPLOSION, timeout=3.0)
        time.sleep(0.5)

        # Cursor A 상태 확인 (explosion 후)
        cursor_a_after = asyncio.run(CursorHandler.get_by_id(CL_A))
        assert cursor_a_after.is_alive == False, "폭발 범위 내 커서는 죽어야 함"
        assert cursor_a_after.score == 0, "죽은 커서의 점수는 0이어야 함"

        # Cursor B는 폭발 범위 밖이므로 살아있어야 함
        cursor_b_after = asyncio.run(CursorHandler.get_by_id(CL_B))
        assert cursor_b_after.is_alive == True, "폭발 범위 밖 커서는 살아있어야 함"
