import pytest
import asyncio
from unittest.mock import patch
from datetime import datetime, timedelta

from server import app
from config import BoardConfig, BombConfig

from data.event import ServerEvent, ClientEvent
from data.board import Point, PointRange, Section, SectionFlag
from data.board.cursorboard import Color
from data.cursor import ItemType, Items, Cursor
from data.payload import ServerMessage
from data.conn import Message
from core.event import Event

from tests.utils import PytestTCM, assert_wait_event, assert_wait_call_if, assert_wait_message, build_tiles

CL_A = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
CL_B = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"


# -------------------------
# 헬퍼
# -------------------------
def create_cursor_by_id(
    pos_map: dict[str, Point],
    items_map: dict[str, Items] | None = None,
    active_at_map: dict[str, datetime] | None = None
):
    """id에 따라 cursor 위치/아이템/생존 시간을 지정한다."""
    from data.cursor import Cursor
    origin_create = Cursor.create
    items_map = items_map or {}
    active_at_map = active_at_map or {}

    def create_cursor_effect(
        id: str,
        width: int = 0,
        height: int = 0,
        color: Color = Color.RED,
        **_kwargs,
    ):
        pos = pos_map.get(id, Point(0, 0))
        items = items_map.get(id, Items())
        active_at = active_at_map.get(id)
        return origin_create(
            id,
            width=width,
            height=height,
            position=pos,
            items=items,
            active_at=active_at,
            color=color,
        )

    return create_cursor_effect


def assert_no_event(conn_send, event_name: ServerEvent, timeout: float, reason: str):
    """지정 시간 동안 특정 이벤트가 오지 않아야 한다."""
    try:
        assert_wait_call_if(
            conn_send,
            lambda msg: msg.event.event_name == event_name,
            timeout=timeout,
            error_msg=f"{reason} (예상: {event_name.value} 미수신)"
        )
    except AssertionError:
        return
    pytest.fail(f"{reason} (실제: {event_name.value} 수신됨)")


async def wait_for_cursor(predicate, timeout: float, step: float, error_msg: str):
    from handler.cursor import CursorHandler
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        cursor = await CursorHandler.get_by_id(CL_A)
        if predicate(cursor):
            return
        await asyncio.sleep(step)
    pytest.fail(error_msg)


# -------------------------
# 보드 맵
# -------------------------
async def empty_board_map(db):
    """4x4 열린 타일 보드."""
    map_str = """\
....
....
....
....
"""
    tiles = build_tiles(map_str)
    sections = [Section(Point(0, 0), tiles.copy(), flag=SectionFlag.INTERACTIONAL)]
    from handler.board.storage import create_section
    for s in sections:
        await create_section(db, s)


# -------------------------
# FT-008: 시나리오
# -------------------------
@patch.object(BombConfig, "DEFAULT_DELAY_SECONDS", new=0.2)
@patch.object(BombConfig, "EXPLOSION_RANGE", new=1)
@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=empty_board_map)
@pytest.mark.asyncio
async def test_ft008_scenario_install_bomb():
    """
    시나리오
    1. 사용자가 보유한 폭탄을 사용하여 특정 tile에 지뢰 설치를 요청한다.
    2. 변경된 cursor 정보가 전달된다.
    3. 해당 타일에서 일정 시간이 지나면 지뢰가 폭발하여 explosion이 발생한다.
    """
    with PytestTCM(app).append_client(CL_A).append_client(CL_B) as tcm:
        cl_a = tcm.get_client(CL_A)
        cl_b = tcm.get_client(CL_B)

        positions = {
            CL_A: Point(0, 0),
            CL_B: Point(1, 1),
        }
        items_a = Items()
        items_a.grant_item(ItemType.BOMB, 1)
        fixed_active_at = datetime(2025, 1, 1, 0, 0, 0)

        with patch(
            "data.cursor.Cursor.create",
            side_effect=create_cursor_by_id(
                positions,
                items_map={CL_A: items_a},
                active_at_map={CL_A: fixed_active_at, CL_B: fixed_active_at}
            )
        ):
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 1, "height": 1, "color": Color.RED.value}
            })
            cl_b.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 1, "height": 1, "color": Color.BLUE.value}
            })

            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)
            assert_wait_event(cl_b.conn.send, ServerEvent.CURSORS_STATE)

        cl_a.conn.send.await_args_list.clear()
        cl_b.conn.send.await_args_list.clear()

        bomb_point = Point(1, 1)
        draw_range = PointRange.create_by_mid(
            mid=bomb_point,
            height=BombConfig.EXPLOSION_RANGE,
            width=BombConfig.EXPLOSION_RANGE,
        )
        expected_tile_count = draw_range.width * draw_range.height
        expected_color_data = bytes([Color.RED.value]) * expected_tile_count

        # 지뢰 설치 요청(폭탄 사용)
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.INSTALL_BOMB.value},
            "payload": {"position": {"x": bomb_point.x, "y": bomb_point.y}}
        })

        # 변경된 cursor 정보 전달 확인(폭탄 보유량 감소)
        expected_cursor = Cursor.create(
            CL_A,
            position=Point(0, 0),
            width=1,
            height=1,
            active_at=fixed_active_at,
            items=Items(),
            color=Color.RED,
        )
        expected_msg = Message(
            event=Event(
                event_name=ServerEvent.CURSORS_STATE,
                payload=ServerMessage.CursorsState([expected_cursor])
            )
        )
        assert_wait_message(
            cl_a.conn.send,
            expected_msg,
            timeout=1.5
        )

        # 설치 요청 이후 폭발 이벤트 수신(설치 후 약 2초)
        assert_wait_call_if(
            cl_a.conn.send,
            lambda msg: msg.event.event_name == ServerEvent.EXPLOSION,
            timeout=3.5,
            error_msg="폭탄 설치 후 A 클라이언트가 EXPLOSION을 받지 못함"
        )
        assert_wait_call_if(
            cl_b.conn.send,
            lambda msg: msg.event.event_name == ServerEvent.EXPLOSION,
            timeout=3.5,
            error_msg="폭탄 설치 후 B 클라이언트가 EXPLOSION을 받지 못함"
        )

        # 설치자 색상과 변경 범위가 A/B 모두에게 전달되었는지 확인
        assert_wait_call_if(
            cl_a.conn.send,
            lambda msg: (
                msg.event.event_name == ServerEvent.COLORED_TILES_STATE and
                len(msg.event.payload.colored_tiles_li) == 1 and
                msg.event.payload.colored_tiles_li[0].range == draw_range and
                len(bytes.fromhex(msg.event.payload.colored_tiles_li[0].data)) == expected_tile_count and
                bytes.fromhex(msg.event.payload.colored_tiles_li[0].data) == expected_color_data
            ),
            timeout=3.5,
            error_msg="폭탄 설치 후 A 클라이언트가 COLORED_TILES_STATE를 받지 못했거나 RED 색상 반영이 없음"
        )
        assert_wait_call_if(
            cl_b.conn.send,
            lambda msg: (
                msg.event.event_name == ServerEvent.COLORED_TILES_STATE and
                len(msg.event.payload.colored_tiles_li) == 1 and
                msg.event.payload.colored_tiles_li[0].range == draw_range and
                len(bytes.fromhex(msg.event.payload.colored_tiles_li[0].data)) == expected_tile_count and
                bytes.fromhex(msg.event.payload.colored_tiles_li[0].data) == expected_color_data
            ),
            timeout=3.5,
            error_msg="폭탄 설치 후 B 클라이언트가 COLORED_TILES_STATE를 받지 못했거나 RED 색상 반영이 없음"
        )


# -------------------------
# FT-008: 비즈니스 규칙
# -------------------------


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=empty_board_map)
@pytest.mark.asyncio
async def test_ft008_business_rule_dead_cursor_cannot_install():
    """
    비즈니스 규칙
    - 죽은 cursor는 지뢰를 설치할 수 없다.
    """
    with PytestTCM(app).append_client(CL_A) as tcm:
        cl_a = tcm.get_client(CL_A)

        items_a = Items()
        items_a.grant_item(ItemType.BOMB, 1)
        dead_at = datetime.now() + timedelta(hours=1)

        with patch(
            "data.cursor.Cursor.create",
            side_effect=create_cursor_by_id(
                {CL_A: Point(0, 0)},
                items_map={CL_A: items_a},
                active_at_map={CL_A: dead_at}
            )
        ):
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 1, "height": 1, "color": Color.RED.value}
            })
            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)

        cl_a.conn.send.await_args_list.clear()

        # 지뢰 설치 요청(실패해야 함)
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.INSTALL_BOMB.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        # 폭발 이벤트가 오지 않아야 함(설치 실패)
        assert_no_event(
            cl_a.conn.send,
            ServerEvent.EXPLOSION,
            timeout=2.5,
            reason="죽은 cursor는 설치가 불가하므로 EXPLOSION이 오면 안됨"
        )


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=empty_board_map)
@pytest.mark.asyncio
async def test_ft008_business_rule_need_bomb_item():
    """
    비즈니스 규칙
    - 폭탄 보유량이 1 미만이면 지뢰를 설치할 수 없다.
    """
    with PytestTCM(app).append_client(CL_A) as tcm:
        cl_a = tcm.get_client(CL_A)

        with patch("data.cursor.Cursor.create", side_effect=create_cursor_by_id({CL_A: Point(0, 0)})):
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 1, "height": 1, "color": Color.RED.value}
            })
            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)

        cl_a.conn.send.await_args_list.clear()

        # 폭탄 없이 지뢰 설치 요청(실패해야 함)
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.INSTALL_BOMB.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        # 폭발 이벤트가 오지 않아야 함(설치 실패)
        assert_no_event(
            cl_a.conn.send,
            ServerEvent.EXPLOSION,
            timeout=2.5,
            reason="폭탄 보유량 부족 시 EXPLOSION이 오면 안됨"
        )


# -------------------------
# FT-008: 상태 변화
# -------------------------
@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=empty_board_map)
@pytest.mark.asyncio
async def test_ft008_state_change_bomb_decrease():
    """
    상태 변화
    - cursor 폭탄 보유량: n → n-1
    """
    with PytestTCM(app).append_client(CL_A) as tcm:
        cl_a = tcm.get_client(CL_A)

        items_a = Items()
        items_a.grant_item(ItemType.BOMB, 1)
        with patch(
            "data.cursor.Cursor.create",
            side_effect=create_cursor_by_id({CL_A: Point(0, 0)}, items_map={CL_A: items_a})
        ):
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 1, "height": 1, "color": Color.RED.value}
            })
            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)

        # 지뢰 설치
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.INSTALL_BOMB.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        # 폭탄 보유량 감소가 handler 기준 반영될 때까지 대기
        await wait_for_cursor(
            lambda cursor: cursor.items.bomb == 0,
            timeout=5.0,
            step=0.05,
            error_msg="폭탄 설치 후 bomb 감소가 handler 기준 반영되지 않음"
        )


@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=empty_board_map)
@pytest.mark.asyncio
async def test_ft008_state_change_cursor_death():
    """
    상태 변화
    - 폭발 범위 내 cursor 상태: alive → dead
    """
    with PytestTCM(app).append_client(CL_A) as tcm:
        cl_a = tcm.get_client(CL_A)

        items_a = Items()
        items_a.grant_item(ItemType.BOMB, 1)
        with patch(
            "data.cursor.Cursor.create",
            side_effect=create_cursor_by_id({CL_A: Point(0, 0)}, items_map={CL_A: items_a})
        ):
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 1, "height": 1, "color": Color.RED.value}
            })
            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)

        # 지뢰 설치
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.INSTALL_BOMB.value},
            "payload": {"position": {"x": 1, "y": 1}}
        })

        await wait_for_cursor(
            lambda cursor: not cursor.is_alive,
            timeout=5.0,
            step=0.05,
            error_msg="폭탄 폭발 후 cursor가 사망하지 않음"
        )


@patch.object(BombConfig, "DEFAULT_DELAY_SECONDS", new=0.1)
@patch.object(BombConfig, "EXPLOSION_RANGE", new=0)
@patch.object(BoardConfig, "LENGTH", new=4)
@patch("server.initialize_board", new=empty_board_map)
@pytest.mark.asyncio
async def test_ft008_state_change_tile_color():
    """
    상태 변화
    - 폭발 범위 내 tile 색: 기존 색 → 설치자 색
    """
    from handler.cursor_board.internal.cursor_board import CursorBoardHandler

    with PytestTCM(app).append_client(CL_A) as tcm:
        cl_a = tcm.get_client(CL_A)

        items_a = Items()
        items_a.grant_item(ItemType.BOMB, 1)
        with patch(
            "data.cursor.Cursor.create",
            side_effect=create_cursor_by_id(
                {CL_A: Point(0, 0)},
                items_map={CL_A: items_a},
            )
        ):
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 2, "height": 2, "color": Color.RED.value}
            })
            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)

        cl_a.conn.send.await_args_list.clear()

        target = Point(1, 1)

        cl_a.ws.send_json({
            "header": {"event": ClientEvent.INSTALL_BOMB.value},
            "payload": {"position": {"x": target.x, "y": target.y}}
        })

        deadline = asyncio.get_event_loop().time() + 2.0
        while asyncio.get_event_loop().time() < deadline:
            cursor_tiles = await CursorBoardHandler.fetch(PointRange(target, target))
            colored_cursor = cursor_tiles.cursor_tile_at(Point(0, 0))
            if colored_cursor.user_id == CL_A:
                return
            await asyncio.sleep(0.05)

        pytest.fail("폭발 이후 cursor_board의 target tile 색이 설치자 색으로 변경되지 않음")
