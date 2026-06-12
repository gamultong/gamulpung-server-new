import pytest
from server import app
from data.event import ServerEvent, ClientEvent
from data.board import Point, Section, SectionFlag, PointRange, Tile, Tiles
from data.cursor_board import Color
from data.payload import ServerMessage
from data.conn import Message
from core.event import Event
from handler.board import BoardHandler
from handler.cursor import CursorHandler
from tests.utils import PytestTCM, assert_wait_event, assert_wait_message, build_tiles, create_cursor_at_position
from unittest.mock import patch
from config import BoardConfig
from datetime import datetime, timedelta

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




@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=simple_board_map)
@pytest.mark.asyncio
async def test_ft004_set_flag_scenario():
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
                "payload": {"width": 1, "height": 1, "color": Color.RED.value}
            })

            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)

        # 이전 event 소비
        cl_a.conn.send.await_args_list.clear()

        # 시나리오 1: 닫힌 타일 (1, 1)에 깃발 설치 요청
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.SET_FLAG.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        # 시나리오 3: TILES_STATE 이벤트 수신 및 검증 - 깃발이 설치된 타일 정보 확인
        flagged_tile = Tile.create(is_open=False, is_mine=False, is_flag=True, number=0)
        tiles = Tiles(data=bytearray([flagged_tile.data]), width=1, height=1)

        expected_message = Message(
            event=Event(
                event_name=ServerEvent.TILES_STATE,
                payload=ServerMessage.TilesState(
                    tiles_li=[
                        ServerMessage.TilesState.Elem(
                            data=tiles.to_str(),
                            range=PointRange(Point(1, 1), Point(1, 1))
                        )
                    ]
                )
            )
        )
        assert_wait_message(cl_a.conn.send, expected_message)


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=flagged_board_map)
@pytest.mark.asyncio
async def test_ft004_unset_flag_scenario():
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
                "payload": {"width": 1, "height": 1, "color": Color.RED.value}
            })

            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)

        # 이전 event 소비
        cl_a.conn.send.await_args_list.clear()

        # 시나리오 1: 깃발이 있는 타일 (1, 1)에 깃발 해제 요청
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.SET_FLAG.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        # 시나리오 3: TILES_STATE 이벤트 수신 및 검증 - 깃발이 제거된 타일 정보 확인
        unflagged_tile = Tile.create(is_open=False, is_mine=False, is_flag=False, number=0)
        tiles = Tiles(data=bytearray([unflagged_tile.data]), width=1, height=1)

        expected_message = Message(
            event=Event(
                event_name=ServerEvent.TILES_STATE,
                payload=ServerMessage.TilesState(
                    tiles_li=[
                        ServerMessage.TilesState.Elem(
                            data=tiles.to_str(),
                            range=PointRange(Point(1, 1), Point(1, 1))
                        )
                    ]
                )
            )
        )
        assert_wait_message(cl_a.conn.send, expected_message)


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=simple_board_map)
@pytest.mark.asyncio
async def test_ft004_business_rule_toggle_behavior():
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
                "payload": {"width": 1, "height": 1, "color": Color.RED.value}
            })

            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)

        # 이전 event 소비
        cl_a.conn.send.await_args_list.clear()

        # 첫 번째 SET_FLAG: 깃발 설치
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.SET_FLAG.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        # 깃발 설치 검증
        flagged_tile = Tile.create(is_open=False, is_mine=False, is_flag=True, number=0)
        tiles_flagged = Tiles(data=bytearray([flagged_tile.data]), width=1, height=1)

        expected_message_set = Message(
            event=Event(
                event_name=ServerEvent.TILES_STATE,
                payload=ServerMessage.TilesState(
                    tiles_li=[
                        ServerMessage.TilesState.Elem(
                            data=tiles_flagged.to_str(),
                            range=PointRange(Point(1, 1), Point(1, 1))
                        )
                    ]
                )
            )
        )
        assert_wait_message(cl_a.conn.send, expected_message_set)

        # 두 번째 SET_FLAG: 깃발 해제
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.SET_FLAG.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        # 깃발 해제 검증
        unflagged_tile = Tile.create(is_open=False, is_mine=False, is_flag=False, number=0)
        tiles_unflagged = Tiles(data=bytearray([unflagged_tile.data]), width=1, height=1)

        expected_message_unset = Message(
            event=Event(
                event_name=ServerEvent.TILES_STATE,
                payload=ServerMessage.TilesState(
                    tiles_li=[
                        ServerMessage.TilesState.Elem(
                            data=tiles_unflagged.to_str(),
                            range=PointRange(Point(1, 1), Point(1, 1))
                        )
                    ]
                )
            )
        )
        assert_wait_message(cl_a.conn.send, expected_message_unset)


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=simple_board_map)
@pytest.mark.asyncio
async def test_ft004_business_rule_dead_cursor():
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
                "payload": {"width": 1, "height": 1, "color": Color.RED.value}
            })

            cl_a.ws.send_json({
                "header": {"event": ClientEvent.SET_WINDOW.value},
                "payload": {"width": 1, "height": 1}
            })

            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)

        # Cursor를 죽은 상태로 설정
        cursor = await CursorHandler.get_by_id(CL_A)
        cursor.active_at = datetime.now() + timedelta(seconds=10)
        CursorHandler.cursor_dict[CL_A] = cursor

        # 죽은 상태에서 깃발 설치 시도
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.SET_FLAG.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        # 타일 상태 확인 - 깃발이 설치되지 않아야 함
        tile = await BoardHandler.fetch_tile(Point(1, 1))
        assert not tile.is_flag, "죽은 커서는 깃발을 설치할 수 없음"


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=simple_board_map)
@pytest.mark.asyncio
async def test_ft004_state_change_flag_installed():
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
                "payload": {"width": 1, "height": 1, "color": Color.RED.value}
            })

            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)

        # Before: 깃발이 없는 상태 확인
        tile_before = await BoardHandler.fetch_tile(Point(1, 1))
        assert not tile_before.is_flag, "초기 상태에서 깃발이 없어야 함"

        # 이전 event 소비
        cl_a.conn.send.await_args_list.clear()

        # 깃발 설치
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.SET_FLAG.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        # After: 깃발이 설치된 상태를 이벤트로 검증
        flagged_tile = Tile.create(is_open=False, is_mine=False, is_flag=True, number=0)
        tiles = Tiles(data=bytearray([flagged_tile.data]), width=1, height=1)

        expected_message = Message(
            event=Event(
                event_name=ServerEvent.TILES_STATE,
                payload=ServerMessage.TilesState(
                    tiles_li=[
                        ServerMessage.TilesState.Elem(
                            data=tiles.to_str(),
                            range=PointRange(Point(1, 1), Point(1, 1))
                        )
                    ]
                )
            )
        )
        assert_wait_message(cl_a.conn.send, expected_message)


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=flagged_board_map)
@pytest.mark.asyncio
async def test_ft004_state_change_flag_removed():
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
                "payload": {"width": 1, "height": 1, "color": Color.RED.value}
            })

            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)

        # Before: 깃발이 있는 상태 확인
        tile_before = await BoardHandler.fetch_tile(Point(1, 1))
        assert tile_before.is_flag, "초기 상태에서 깃발이 있어야 함"

        # 이전 event 소비
        cl_a.conn.send.await_args_list.clear()

        # 깃발 해제
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.SET_FLAG.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        # After: 깃발이 제거된 상태를 이벤트로 검증
        unflagged_tile = Tile.create(is_open=False, is_mine=False, is_flag=False, number=0)
        tiles = Tiles(data=bytearray([unflagged_tile.data]), width=1, height=1)

        expected_message = Message(
            event=Event(
                event_name=ServerEvent.TILES_STATE,
                payload=ServerMessage.TilesState(
                    tiles_li=[
                        ServerMessage.TilesState.Elem(
                            data=tiles.to_str(),
                            range=PointRange(Point(1, 1), Point(1, 1))
                        )
                    ]
                )
            )
        )
        assert_wait_message(cl_a.conn.send, expected_message)
