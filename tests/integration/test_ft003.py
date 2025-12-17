import pytest
from tests.utils import TCM, assert_wait_message, assert_wait_event, set_board
from server import app
from data.event import ServerEvent, ClientEvent
from data.payload import ServerMessage
from data.conn import Message
from data.board import Point, Tile, Tiles, Section, SectionFlag, PointRange
from core.event import Event
from handler.cursor import CursorHandler
from handler.board import BoardHandler
from unittest.mock import AsyncMock, patch
from typing import cast
from config import BoardConfig
from datetime import datetime, timedelta

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
    CLSE CLSE CLSE CLSE
    NUM1 NUM1 NUM1 CLSE
    OPEN CLSE NUM1 CLSE
    NUM1 NUM1 NUM1 CLSE
    """
    data = [
        CLSE, CLSE, CLSE, CLSE,
        NUM1, NUM1, NUM1, CLSE,
        OPEN, CLSE, NUM1, CLSE,
        NUM1, NUM1, NUM1, CLSE,
    ]
    tiles = Tiles(bytearray(data), 4, 4)
    sections = [Section(Point(0, 0), tiles.copy(), flag=SectionFlag.INTERACTIONAL)]
    from handler.board.storage import create_section
    for section in sections:
        await create_section(db, section)


async def mine_board_map(db):
    """
    Board with mine at (1, 1):
    CLSE CLSE CLSE CLSE
    NUM1 MINE NUM1 CLSE
    CLSE CLSE CLSE CLSE
    CLSE CLSE CLSE CLSE
    """
    data = [
        CLSE, CLSE, CLSE, CLSE,
        NUM1, MINE, NUM1, CLSE,
        CLSE, CLSE, CLSE, CLSE,
        CLSE, CLSE, CLSE, CLSE,
    ]
    tiles = Tiles(bytearray(data), 4, 4)
    sections = [Section(Point(0, 0), tiles.copy(), flag=SectionFlag.INTERACTIONAL)]
    from handler.board.storage import create_section
    for section in sections:
        await create_section(db, section)


async def flagged_board_map(db):
    """
    Board with flagged tile at (1, 1):
    CLSE CLSE CLSE CLSE
    NUM1 FLAG NUM1 CLSE
    CLSE CLSE CLSE CLSE
    CLSE CLSE CLSE CLSE
    """
    data = [
        CLSE, CLSE, CLSE, CLSE,
        NUM1, FLAG, NUM1, CLSE,
        CLSE, CLSE, CLSE, CLSE,
        CLSE, CLSE, CLSE, CLSE,
    ]
    tiles = Tiles(bytearray(data), 4, 4)
    sections = [Section(Point(0, 0), tiles.copy(), flag=SectionFlag.INTERACTIONAL)]
    from handler.board.storage import create_section
    for section in sections:
        await create_section(db, section)


def create_cursor_at_position(position: Point):
    """Cursor를 특정 위치에 생성하는 헬퍼"""
    origin_create = CursorHandler.cursor_create

    def create_cursor_effect(id: str, position_arg: Point, width: int = 0, height: int = 0):
        return origin_create(id, width=width, height=height, position=position)

    return create_cursor_effect


@pytest.fixture
def tcm_one_client():
    """1명 클라이언트 (시나리오 테스트용)"""
    return TCM(app).append_client(CL_A)


@pytest.fixture
def tcm_two_clients():
    """2명 클라이언트 (explosion 테스트용)"""
    return TCM(app).append_client(CL_A).append_client(CL_B)


@pytest.mark.asyncio
@set_board(simple_board_map)
@patch.object(BoardConfig, "LENGTH", new=4)
async def test_ft003_open_tile_scenario(tcm_one_client: TCM):
    """
    FT-003 타일 열기 시나리오 검증:
    1. 사용자가 closed-tile을 클릭하여 열기를 요청한다.
    2. tile이 opened 상태로 변경되고 지뢰 정보가 표시된다.
    """
    async with tcm_one_client:
        cl_a = tcm_one_client.get_client(CL_A)
        conn_a_send_mock = cast(AsyncMock, cl_a.conn.send)

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
            assert_wait_event(conn_a_send_mock, ServerEvent.CURSORS_STATE, timeout=3.0)

        # 시나리오 1: 사용자가 closed-tile (1,1) 클릭
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.OPEN_TILES.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        # 시나리오 2: tile이 opened 상태로 변경되고 지뢰 정보 표시
        # TILES_STATE 이벤트 수신 검증
        assert_wait_event(conn_a_send_mock, ServerEvent.TILES_STATE, timeout=3.0)

        # 서버 상태 검증: tile이 opened 상태로 변경됨
        tile = await BoardHandler.fetch_tile(Point(1, 1))
        assert tile.is_open == True, "타일이 열린 상태여야 함"


@pytest.mark.asyncio
@set_board(flagged_board_map)
@patch.object(BoardConfig, "LENGTH", new=4)
async def test_ft003_business_rule_flagged_tile(tcm_one_client: TCM):
    """
    비즈니스 규칙 검증:
    - flag가 설치된 tile은 열 수 없다.
    """
    async with tcm_one_client:
        cl_a = tcm_one_client.get_client(CL_A)
        conn_a_send_mock = cast(AsyncMock, cl_a.conn.send)

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

            assert_wait_event(conn_a_send_mock, ServerEvent.CURSORS_STATE, timeout=3.0)

        # 깃발이 설치된 타일 (1,1) 열기 시도
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.OPEN_TILES.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        # 타일이 열리지 않았는지 검증
        import time
        time.sleep(0.5)

        tile = await BoardHandler.fetch_tile(Point(1, 1))
        assert tile.is_open == False, "깃발이 설치된 타일은 열리지 않아야 함"
        assert tile.is_flag == True, "깃발이 여전히 설치되어 있어야 함"


@pytest.mark.asyncio
@set_board(simple_board_map)
@patch.object(BoardConfig, "LENGTH", new=4)
async def test_ft003_business_rule_closed_tile_only(tcm_one_client: TCM):
    """
    비즈니스 규칙 검증:
    - closed-tile만 열기 가능하다.
    """
    async with tcm_one_client:
        cl_a = tcm_one_client.get_client(CL_A)
        conn_a_send_mock = cast(AsyncMock, cl_a.conn.send)

        # Cursor를 (0, 2) 위치에 생성 (이미 열린 타일 (0,2)와 상호작용 가능)
        with patch("data.cursor.Cursor.create", side_effect=create_cursor_at_position(Point(0, 2))):
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 1, "height": 1}
            })

            cl_a.ws.send_json({
                "header": {"event": ClientEvent.SET_WINDOW.value},
                "payload": {"width": 1, "height": 1}
            })

            assert_wait_event(conn_a_send_mock, ServerEvent.CURSORS_STATE, timeout=3.0)

        # 초기 점수 확인
        cursor_before = await CursorHandler.get_by_id(CL_A)
        score_before = cursor_before.score

        # 이미 열린 타일 (0,2) 열기 시도
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.OPEN_TILES.value},
            "payload": {"position": {"x": 0, "y": 2}}
        })

        # 점수가 변경되지 않았는지 검증
        import time
        time.sleep(0.5)

        cursor_after = await CursorHandler.get_by_id(CL_A)
        assert cursor_after.score == score_before, "이미 열린 타일을 다시 열면 점수가 변하지 않아야 함"


@pytest.mark.asyncio
@set_board(simple_board_map)
@patch.object(BoardConfig, "LENGTH", new=4)
async def test_ft003_business_rule_dead_cursor(tcm_one_client: TCM):
    """
    비즈니스 규칙 검증:
    - 죽은 cursor는 타일을 열 수 없다.
    """
    async with tcm_one_client:
        cl_a = tcm_one_client.get_client(CL_A)
        conn_a_send_mock = cast(AsyncMock, cl_a.conn.send)

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

            assert_wait_event(conn_a_send_mock, ServerEvent.CURSORS_STATE, timeout=3.0)

        # Cursor를 죽은 상태로 설정 (active_at을 미래 시간으로)
        cursor = await CursorHandler.get_by_id(CL_A)
        cursor.active_at = datetime.now() + timedelta(seconds=10)
        CursorHandler.cursor_dict[CL_A] = cursor

        # 죽은 상태에서 타일 열기 시도
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.OPEN_TILES.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        # 타일이 열리지 않았는지 검증
        import time
        time.sleep(0.5)

        tile = await BoardHandler.fetch_tile(Point(1, 1))
        assert tile.is_open == False, "죽은 커서는 타일을 열 수 없어야 함"


@pytest.mark.asyncio
@set_board(mine_board_map)
@patch.object(BoardConfig, "LENGTH", new=4)
async def test_ft003_state_change_tile_opened(tcm_one_client: TCM):
    """
    상태 변화 검증:
    - tile 상태: closed → opened
    """
    async with tcm_one_client:
        cl_a = tcm_one_client.get_client(CL_A)
        conn_a_send_mock = cast(AsyncMock, cl_a.conn.send)

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

            assert_wait_event(conn_a_send_mock, ServerEvent.CURSORS_STATE, timeout=3.0)

        # 상태 변화 전: closed 상태 확인
        tile_before = await BoardHandler.fetch_tile(Point(0, 1))
        assert tile_before.is_open == False, "타일이 닫혀있어야 함"

        # 타일 열기
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.OPEN_TILES.value},
            "payload": {"position": {"x": 0, "y": 1}}
        })

        # TILES_STATE 이벤트 대기
        assert_wait_event(conn_a_send_mock, ServerEvent.TILES_STATE, timeout=3.0)

        # 상태 변화 후: opened 상태 확인
        tile_after = await BoardHandler.fetch_tile(Point(0, 1))
        assert tile_after.is_open == True, "타일이 열려있어야 함"


@pytest.mark.asyncio
@set_board(mine_board_map)
@patch.object(BoardConfig, "LENGTH", new=4)
async def test_ft003_state_change_explosion(tcm_two_clients: TCM):
    """
    상태 변화 검증:
    - 지뢰 발견 시 cursor 상태 변경 (explosion)
    """
    async with tcm_two_clients:
        cl_a = tcm_two_clients.get_client(CL_A)
        cl_b = tcm_two_clients.get_client(CL_B)
        conn_a_send_mock = cast(AsyncMock, cl_a.conn.send)
        conn_b_send_mock = cast(AsyncMock, cl_b.conn.send)

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

            assert_wait_event(conn_a_send_mock, ServerEvent.CURSORS_STATE, timeout=3.0)

        # Cursor B를 (2, 1) 위치에 생성 (지뢰 폭발 범위 밖)
        with patch("data.cursor.Cursor.create", side_effect=create_cursor_at_position(Point(2, 1))):
            cl_b.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 5, "height": 5}
            })

            cl_b.ws.send_json({
                "header": {"event": ClientEvent.SET_WINDOW.value},
                "payload": {"width": 5, "height": 5}
            })

            assert_wait_event(conn_b_send_mock, ServerEvent.CURSORS_STATE, timeout=3.0)

        # Cursor A 상태 확인 (explosion 전)
        cursor_a_before = await CursorHandler.get_by_id(CL_A)
        assert cursor_a_before.is_alive == True, "커서가 살아있어야 함"

        # 지뢰 타일 (1, 1) 열기
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.OPEN_TILES.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        # EXPLOSION 이벤트 대기
        assert_wait_event(conn_a_send_mock, ServerEvent.EXPLOSION, timeout=3.0)

        # Cursor A 상태 확인 (explosion 후)
        cursor_a_after = await CursorHandler.get_by_id(CL_A)
        assert cursor_a_after.is_alive == False, "폭발 범위 내 커서는 죽어야 함"
        assert cursor_a_after.score == 0, "죽은 커서의 점수는 0이어야 함"

        # Cursor B는 폭발 범위 밖이므로 살아있어야 함
        cursor_b_after = await CursorHandler.get_by_id(CL_B)
        assert cursor_b_after.is_alive == True, "폭발 범위 밖 커서는 살아있어야 함"
