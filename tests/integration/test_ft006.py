import pytest
from tests.utils import TestClientManager, assert_wait_message, assert_wait_event, assert_wait_call_if
from server import app
from data.event import ServerEvent, ClientEvent
from data.payload import ServerMessage, ClientMessage
from data.conn import Message
from data.board import Point
from data.cursor import Cursor
from core.event import Event
from unittest.mock import AsyncMock
from typing import cast

CL_A = "TestClient_A"


@pytest.fixture
def tcm():
    """단일 클라이언트 테스트용 TestClientManager"""
    return (
        TestClientManager(app)
        .append_client(CL_A)
    )


@pytest.mark.asyncio
async def test_ft006_join_scenario(tcm: TestClientManager):
    """
    FT-006 접속 시나리오 검증:
    1. scoreboard를 보여준다. (JOIN 시)
    2. 사용자의 cursor를 생성한다. (CREATE_CURSOR → MY_CURSOR)
    3. 시야 범위 내의 board를 보여준다. (CREATE_CURSOR → TILES_STATE)
    4. 사용자의 cursor와 시야 범위 내의 cursor를 보여준다. (CREATE_CURSOR → CURSORS_STATE)
    """
    async with tcm:
        cl_a = tcm.get_client(CL_A)
        conn_a_send_mock = cast(AsyncMock, cl_a.conn.send)

        # 시나리오 1: JOIN 시 SCOREBOARD_STATE 수신 검증
        expected_scoreboard = Message(
            event=Event(
                event_name=ServerEvent.SCOREBOARD_STATE,
                payload=ServerMessage.ScoreBoardState(scoreboard={})
            )
        )
        assert_wait_message(conn_a_send_mock, expected_scoreboard, timeout=3.0)

        # CREATE_CURSOR 이벤트 전송
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.CREATE_CURSOR.value},
            "payload": {"width": 10, "height": 10}
        })

        # 시나리오 2: MY_CURSOR 수신 검증
        expected_my_cursor = Message(
            event=Event(
                event_name=ServerEvent.MY_CURSOR,
                payload=ServerMessage.MyCursor(id=CL_A)
            )
        )
        assert_wait_message(conn_a_send_mock, expected_my_cursor, timeout=3.0)

        # 시나리오 4: CURSORS_STATE 수신 검증 (position은 비즈니스 규칙 테스트에서 검증)
        assert_wait_call_if(
            conn_a_send_mock,
            lambda msg: (
                msg.event.event_name == ServerEvent.CURSORS_STATE and
                len(msg.event.payload.cursors) == 1 and
                msg.event.payload.cursors[0].id == CL_A
            ),
            timeout=3.0,
            error_msg="CURSORS_STATE에 올바른 cursor가 없음"
        )

        # 시나리오 3: TILES_STATE 수신 검증 (10x10 window)
        assert_wait_call_if(
            conn_a_send_mock,
            lambda msg: (
                msg.event.event_name == ServerEvent.TILES_STATE and
                len(msg.event.payload.tiles) > 0  # tiles가 존재하는지만 확인
            ),
            timeout=3.0,
            error_msg="TILES_STATE를 받지 못함"
        )


@pytest.mark.asyncio
async def test_ft006_business_rule_initial_position(tcm: TestClientManager):
    """
    비즈니스 규칙 검증:
    - cursor는 항상 시작 지점(0, 0)에 생성된다.
    """
    async with tcm:
        cl_a = tcm.get_client(CL_A)
        conn_a_send_mock = cast(AsyncMock, cl_a.conn.send)

        # CREATE_CURSOR 전송
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.CREATE_CURSOR.value},
            "payload": {"width": 5, "height": 5}
        })

        # CURSORS_STATE에서 cursor가 (0, 0) 위치에 생성되는지 검증
        # active_at은 timestamp라서 정확한 값을 예측할 수 없으므로 중요한 필드만 검증
        assert_wait_call_if(
            conn_a_send_mock,
            lambda msg: (
                msg.event.event_name == ServerEvent.CURSORS_STATE and
                len(msg.event.payload.cursors) == 1 and
                msg.event.payload.cursors[0].id == CL_A and
                msg.event.payload.cursors[0].position == Point(0, 0) and
                msg.event.payload.cursors[0].width == 5 and
                msg.event.payload.cursors[0].height == 5 and
                msg.event.payload.cursors[0].score == 0
            ),
            timeout=3.0,
            error_msg="CURSORS_STATE의 cursor 정보가 올바르지 않음"
        )


@pytest.mark.asyncio
async def test_ft006_state_change_cursor_creation(tcm: TestClientManager):
    """
    상태 변화 검증:
    - 없음 → cursor 생성
    """
    async with tcm:
        cl_a = tcm.get_client(CL_A)
        conn_a_send_mock = cast(AsyncMock, cl_a.conn.send)

        # CREATE_CURSOR 전송
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.CREATE_CURSOR.value},
            "payload": {"width": 5, "height": 5}
        })

        # cursor 생성 확인: MY_CURSOR 수신
        expected_my_cursor = Message(
            event=Event(
                event_name=ServerEvent.MY_CURSOR,
                payload=ServerMessage.MyCursor(id=CL_A)
            )
        )
        assert_wait_message(conn_a_send_mock, expected_my_cursor, timeout=3.0)

        # cursor 생성 확인: CURSORS_STATE에 cursor 존재
        assert_wait_call_if(
            conn_a_send_mock,
            lambda msg: (
                msg.event.event_name == ServerEvent.CURSORS_STATE and
                len(msg.event.payload.cursors) == 1 and
                msg.event.payload.cursors[0].id == CL_A and
                msg.event.payload.cursors[0].width == 5 and
                msg.event.payload.cursors[0].height == 5
            ),
            timeout=3.0,
            error_msg="cursor가 올바르게 생성되지 않음"
        )
