import pytest
import asyncio
from server import app
from data.event import ServerEvent, ClientEvent
from data.board import Point, Tile, Tiles, Section, SectionFlag
from handler.cursor import CursorHandler
from handler.connection import ConnectionHandler
from tests.utils.internal.conn_mock import PytestTCM
from tests.utils.internal.wait_call import assert_wait_event
from unittest.mock import patch
from config import BoardConfig
from datetime import datetime, timedelta

CL_A = "TestClient_A"

# 테스트용 타일 정의
TILE = Tile.create(is_flag=False, is_mine=False, is_open=False, number=0)
CLSE = TILE.data  # Closed tile
OPEN = TILE.changed(is_open=True).data  # Opened tile


async def opened_board_map(db):
    """
    열린 타일로 구성된 5x5 보드:
    CLSE CLSE CLSE CLSE CLSE
    CLSE OPEN OPEN OPEN CLSE
    CLSE OPEN OPEN OPEN CLSE
    CLSE OPEN OPEN OPEN CLSE
    CLSE CLSE CLSE CLSE CLSE
    """
    data = [
        CLSE, CLSE, CLSE, CLSE, CLSE,
        CLSE, OPEN, OPEN, OPEN, CLSE,
        CLSE, OPEN, OPEN, OPEN, CLSE,
        CLSE, OPEN, OPEN, OPEN, CLSE,
        CLSE, CLSE, CLSE, CLSE, CLSE,
    ]
    tiles = Tiles(bytearray(data), 5, 5)
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


@patch.object(BoardConfig, "LENGTH", new=5)
@patch("server.initialize_board", new=opened_board_map)
def test_ft002_move_scenario():
    """
    FT-002 커서 이동 시나리오 검증:
    1. 사용자가 특정 위치로 이동을 요청한다.
    2. cursor 위치가 변경되고 점수가 1 증가한다.
    3. 변경된 위치 기준으로 새로운 tile 및 cursor 정보가 전달된다.
    """
    with PytestTCM(app).append_client(CL_A) as tcm:
        cl_a = tcm.get_client(CL_A)

        # Cursor를 (1, 1)에 생성
        with patch("data.cursor.Cursor.create", side_effect=create_cursor_at_position(Point(1, 1))):
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 1, "height": 1}
            })
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.SET_WINDOW.value},
                "payload": {"width": 1, "height": 1}
            })
            import time
            time.sleep(0.1)

        # Before: 초기 상태 확인
        cursor_before = asyncio.run(CursorHandler.get_by_id(CL_A))
        assert cursor_before.position == Point(1, 1)
        assert cursor_before.score == 0

        # 열린 타일 (2, 1)로 이동
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.MOVE.value},
            "payload": {"position": {"x": 2, "y": 1}}
        })

        # CURSORS_STATE 이벤트 수신 확인
        assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE, timeout=3.0)
        time.sleep(0.1)

        # After: 변경된 상태 확인
        cursor_after = asyncio.run(CursorHandler.get_by_id(CL_A))
        assert cursor_after.position == Point(2, 1), "cursor 위치가 변경되어야 함"
        assert cursor_after.score == 1, "score가 1 증가해야 함"


@patch.object(BoardConfig, "LENGTH", new=5)
@patch("server.initialize_board", new=opened_board_map)
def test_ft002_business_rule_opened_tile_only():
    """
    비즈니스 규칙 검증:
    - opened-tile로만 이동 가능하다.
    """
    with PytestTCM(app).append_client(CL_A) as tcm:
        cl_a = tcm.get_client(CL_A)

        # Cursor를 (1, 1)에 생성
        with patch("data.cursor.Cursor.create", side_effect=create_cursor_at_position(Point(1, 1))):
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 1, "height": 1}
            })
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.SET_WINDOW.value},
                "payload": {"width": 1, "height": 1}
            })
            import time
            time.sleep(0.1)

        # Before: 초기 위치
        cursor_before = asyncio.run(CursorHandler.get_by_id(CL_A))
        assert cursor_before.position == Point(1, 1)

        # 닫힌 타일 (0, 0)로 이동 시도
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.MOVE.value},
            "payload": {"position": {"x": 0, "y": 0}}
        })
        time.sleep(0.1)

        # After: 위치 변경 없음
        cursor_after = asyncio.run(CursorHandler.get_by_id(CL_A))
        assert cursor_after.position == Point(1, 1), "닫힌 타일로는 이동할 수 없음"


@patch.object(BoardConfig, "LENGTH", new=5)
@patch("server.initialize_board", new=opened_board_map)
def test_ft002_business_rule_dead_cursor():
    """
    비즈니스 규칙 검증:
    - 죽은 cursor는 이동할 수 없다.
    """
    with PytestTCM(app).append_client(CL_A) as tcm:
        cl_a = tcm.get_client(CL_A)

        # Cursor를 (1, 1)에 생성
        with patch("data.cursor.Cursor.create", side_effect=create_cursor_at_position(Point(1, 1))):
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 1, "height": 1}
            })
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.SET_WINDOW.value},
                "payload": {"width": 1, "height": 1}
            })
            import time
            time.sleep(0.1)

        # Cursor를 죽은 상태로 변경
        cursor = asyncio.run(CursorHandler.get_by_id(CL_A))
        future_time = datetime.now() + timedelta(hours=1)
        cursor.active_at = future_time
        asyncio.run(CursorHandler.update(cursor))

        # Before: 초기 위치
        cursor_before = asyncio.run(CursorHandler.get_by_id(CL_A))
        assert cursor_before.position == Point(1, 1)

        # 이동 시도
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.MOVE.value},
            "payload": {"position": {"x": 2, "y": 1}}
        })
        time.sleep(0.1)

        # After: 위치 변경 없음
        cursor_after = asyncio.run(CursorHandler.get_by_id(CL_A))
        assert cursor_after.position == Point(1, 1), "죽은 cursor는 이동할 수 없음"


@patch.object(BoardConfig, "LENGTH", new=5)
@patch("server.initialize_board", new=opened_board_map)
def test_ft002_state_change_position_and_score():
    """
    상태 변화 검증:
    - cursor의 position이 변경된다.
    - cursor의 score가 1 증가한다.
    """
    with PytestTCM(app).append_client(CL_A) as tcm:
        cl_a = tcm.get_client(CL_A)

        # Cursor를 (1, 1)에 생성
        with patch("data.cursor.Cursor.create", side_effect=create_cursor_at_position(Point(1, 1))):
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 1, "height": 1}
            })
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.SET_WINDOW.value},
                "payload": {"width": 1, "height": 1}
            })
            import time
            time.sleep(0.1)

        # Before: 초기 상태
        cursor_before = asyncio.run(CursorHandler.get_by_id(CL_A))
        pos_before = cursor_before.position
        score_before = cursor_before.score

        # 이동
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.MOVE.value},
            "payload": {"position": {"x": 2, "y": 2}}
        })
        assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE, timeout=3.0)
        time.sleep(0.5)

        # After: 상태 변화 확인
        cursor_after = asyncio.run(CursorHandler.get_by_id(CL_A))
        pos_after = cursor_after.position
        score_after = cursor_after.score

        assert pos_before != pos_after, "position 변경됨"
        assert pos_after == Point(2, 2), "새 위치로 이동"
        assert score_after == score_before + 1, "score 1 증가"
