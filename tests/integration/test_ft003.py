import pytest
from server import app
from data.event import ServerEvent, ClientEvent
from data.board import Point, Section, SectionFlag, PointRange, Tile, Tiles
from data.board.cursorboard import Color
from data.payload import ServerMessage
from data.conn import Message
from core.event import Event
from handler.cursor import CursorHandler
from handler.board import BoardHandler
from tests.utils import PytestTCM, assert_wait_event, assert_wait_message, build_tiles, create_cursor_at_position
from unittest.mock import patch
from config import BoardConfig
from datetime import datetime, timedelta
from loguru import logger

CL_A = "TestClient_A"
CL_B = "TestClient_B"


async def simple_board_map(db):
    """
    Simple 4x4 board for basic tests:
    y=3: # # # #
    y=2: 1 1 1 #
    y=1: . # 1 #
    y=0: 1 1 1 #
    """
    map_str = """\
####
111#
.#1#
111#
"""
    tiles = build_tiles(map_str)
    logger.debug("afadsfd")
    sections = [Section(Point(0, 0), tiles.copy(), flag=SectionFlag.INTERACTIONAL)]
    from handler.board.storage import create_section, get_section
    for section in sections:
        await create_section(db, section)
        logger.debug(await get_section(db, Point(0, 0)))


async def mine_board_map(db):
    """
    Board with mine at (1, 1):
    y=3: # # # #
    y=2: # # # #
    y=1: # X # #
    y=0: # # # #
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
    for section in sections:
        await create_section(db, section)


async def flagged_board_map(db):
    """
    Board with flagged tile at (1, 1):
    y=3: # # # #
    y=2: # # # #
    y=1: # F # #
    y=0: # # # #
    """
    map_str = """\
####
####
#F##
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
async def test_ft003_open_tile_scenario():
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
                "payload": {"width": 1, "height": 1, "color": Color.RED.value}
            })

            # Cursor 생성 완료 대기
            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)
            assert_wait_event(cl_a.conn.send, ServerEvent.TILES_STATE)

        # 시나리오 1: 사용자가 closed-tile (1,1) 클릭
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.OPEN_TILES.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        # 시나리오 2: chaining으로 주변 타일들이 열림
        # (1,1)이 number=0이므로 주변 8칸으로 전파
        # 커서 window: PointRange(top_left=Point(x=-1, y=2), bottom_right=Point(x=1, y=0))
        # window 내 타일만 TILES-STATE 이벤트 수신

        # 열린 타일 payload 검증
        # chaining 순서는 구현에 의존하므로, 각 메시지를 개별 검증

        # 타일 (1,2): number=1, 열림
        tile_1_2 = Tile.create(is_open=True, is_mine=False, is_flag=False, number=1)
        tiles_1_2 = Tiles(data=bytearray([tile_1_2.data]), width=1, height=1)
        msg_1_2 = Message(
            event=Event(
                event_name=ServerEvent.TILES_STATE,
                payload=ServerMessage.TilesState(
                    tiles_li=[
                        ServerMessage.TilesState.Elem(
                            data=tiles_1_2.to_str(),
                            range=PointRange(Point(1, 2), Point(1, 2))
                        )
                    ]
                )
            )
        )
        assert_wait_message(cl_a.conn.send, msg_1_2)

        # 타일 (0,0): number=1, 열림
        tile_0_0 = Tile.create(is_open=True, is_mine=False, is_flag=False, number=1)
        tiles_0_0 = Tiles(data=bytearray([tile_0_0.data]), width=1, height=1)
        msg_0_0 = Message(
            event=Event(
                event_name=ServerEvent.TILES_STATE,
                payload=ServerMessage.TilesState(
                    tiles_li=[
                        ServerMessage.TilesState.Elem(
                            data=tiles_0_0.to_str(),
                            range=PointRange(Point(0, 0), Point(0, 0))
                        )
                    ]
                )
            )
        )
        assert_wait_message(cl_a.conn.send, msg_0_0)

        # 타일 (1,1): number=0, 열림
        tile_1_1 = Tile.create(is_open=True, is_mine=False, is_flag=False, number=0)
        tiles_1_1 = Tiles(data=bytearray([tile_1_1.data]), width=1, height=1)
        msg_1_1 = Message(
            event=Event(
                event_name=ServerEvent.TILES_STATE,
                payload=ServerMessage.TilesState(
                    tiles_li=[
                        ServerMessage.TilesState.Elem(
                            data=tiles_1_1.to_str(),
                            range=PointRange(Point(1, 1), Point(1, 1))
                        )
                    ]
                )
            )
        )
        assert_wait_message(cl_a.conn.send, msg_1_1)

        # 타일 (1,0): number=1, 열림
        tile_1_0 = Tile.create(is_open=True, is_mine=False, is_flag=False, number=1)
        tiles_1_0 = Tiles(data=bytearray([tile_1_0.data]), width=1, height=1)
        msg_1_0 = Message(
            event=Event(
                event_name=ServerEvent.TILES_STATE,
                payload=ServerMessage.TilesState(
                    tiles_li=[
                        ServerMessage.TilesState.Elem(
                            data=tiles_1_0.to_str(),
                            range=PointRange(Point(1, 0), Point(1, 0))
                        )
                    ]
                )
            )
        )
        assert_wait_message(cl_a.conn.send, msg_1_0)

        # 타일 (0,2): number=1, 열림
        tile_0_2 = Tile.create(is_open=True, is_mine=False, is_flag=False, number=1)
        tiles_0_2 = Tiles(data=bytearray([tile_0_2.data]), width=1, height=1)
        msg_0_2 = Message(
            event=Event(
                event_name=ServerEvent.TILES_STATE,
                payload=ServerMessage.TilesState(
                    tiles_li=[
                        ServerMessage.TilesState.Elem(
                            data=tiles_0_2.to_str(),
                            range=PointRange(Point(0, 2), Point(0, 2))
                        )
                    ]
                )
            )
        )
        assert_wait_message(cl_a.conn.send, msg_0_2)


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=flagged_board_map)
@pytest.mark.asyncio
async def test_ft003_business_rule_flagged_tile():
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
                "payload": {"width": 1, "height": 1, "color": Color.RED.value}
            })

            cl_a.ws.send_json({
                "header": {"event": ClientEvent.SET_WINDOW.value},
                "payload": {"width": 1, "height": 1}
            })

            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)

        # 깃발이 설치된 타일 (1,1) 열기 시도
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.OPEN_TILES.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        # 타일이 열리지 않았는지 검증

        tile = await BoardHandler.fetch_tile(Point(1, 1))
        assert not tile.is_open, "깃발이 설치된 타일은 열리지 않아야 함"
        assert tile.is_flag, "깃발이 여전히 설치되어 있어야 함"


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=simple_board_map)
@pytest.mark.asyncio
async def test_ft003_business_rule_closed_tile_only():
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
                "payload": {"width": 1, "height": 1, "color": Color.RED.value}
            })

            cl_a.ws.send_json({
                "header": {"event": ClientEvent.SET_WINDOW.value},
                "payload": {"width": 1, "height": 1}
            })

            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)

        # 초기 점수 확인
        cursor_before = await CursorHandler.get_by_id(CL_A)
        score_before = cursor_before.score

        # 이미 열린 타일 (0,1) 열기 시도
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.OPEN_TILES.value},
            "payload": {"position": {"x": 0, "y": 1}}
        })

        # 점수가 변경되지 않았는지 검증

        cursor_after = await CursorHandler.get_by_id(CL_A)
        assert cursor_after.score == score_before, "이미 열린 타일을 다시 열면 점수가 변하지 않아야 함"


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=simple_board_map)
@pytest.mark.asyncio
async def test_ft003_business_rule_dead_cursor():
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
                "payload": {"width": 1, "height": 1, "color": Color.RED.value}
            })

            cl_a.ws.send_json({
                "header": {"event": ClientEvent.SET_WINDOW.value},
                "payload": {"width": 1, "height": 1}
            })

            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)

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

        tile = await BoardHandler.fetch_tile(Point(1, 1))
        assert not tile.is_open, "죽은 커서는 타일을 열 수 없어야 함"


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=mine_board_map)
@pytest.mark.asyncio
async def test_ft003_state_change_tile_opened():
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
                "payload": {"width": 1, "height": 1, "color": Color.RED.value}
            })

            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)
            assert_wait_event(cl_a.conn.send, ServerEvent.TILES_STATE)

        # 상태 변화 전: closed 상태 확인
        tile_before = await BoardHandler.fetch_tile(Point(0, 1))
        assert not tile_before.is_open, "타일이 닫혀있어야 함"

        # 이전 event 소비
        cl_a.conn.send.await_args_list.clear()

        # 타일 열기
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.OPEN_TILES.value},
            "payload": {"position": {"x": 0, "y": 1}}
        })

        # TILES_STATE 이벤트 대기
        # 시아에 보이는 Tile 들
        assert_wait_event(cl_a.conn.send, ServerEvent.TILES_STATE)

        # 상태 변화 후: opened 상태 확인
        tile_after = await BoardHandler.fetch_tile(Point(0, 1))
        assert tile_after.is_open, "타일이 열려있어야 함"


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=mine_board_map)
@pytest.mark.asyncio
async def test_ft003_state_change_explosion():
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
                "payload": {"width": 5, "height": 5, "color": Color.RED.value}
            })

            cl_a.ws.send_json({
                "header": {"event": ClientEvent.SET_WINDOW.value},
                "payload": {"width": 5, "height": 5}
            })

            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)

        # Cursor B를 (3, 3) 위치에 생성 (지뢰 폭발 범위 밖)
        with patch("data.cursor.Cursor.create", side_effect=create_cursor_at_position(Point(3, 3))):
            cl_b.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 5, "height": 5, "color": Color.BLUE.value}
            })

            cl_b.ws.send_json({
                "header": {"event": ClientEvent.SET_WINDOW.value},
                "payload": {"width": 5, "height": 5}
            })

            assert_wait_event(cl_b.conn.send, ServerEvent.CURSORS_STATE)

        # Cursor A 상태 확인 (explosion 전)
        cursor_a_before = await CursorHandler.get_by_id(CL_A)
        assert cursor_a_before.is_alive, "커서가 살아있어야 함"

        # 지뢰 타일 (1, 1) 열기
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.OPEN_TILES.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        # EXPLOSION 이벤트 대기
        assert_wait_event(cl_a.conn.send, ServerEvent.EXPLOSION)

        # Cursor A 상태 확인 (explosion 후)
        cursor_a_after = await CursorHandler.get_by_id(CL_A)
        assert not cursor_a_after.is_alive, "폭발 범위 내 커서는 죽어야 함"
        assert cursor_a_after.score == 0, "죽은 커서의 점수는 0이어야 함"

        # Cursor B는 폭발 범위 밖이므로 살아있어야 함
        cursor_b_after = await CursorHandler.get_by_id(CL_B)
        assert cursor_b_after.is_alive, "폭발 범위 밖 커서는 살아있어야 함"
