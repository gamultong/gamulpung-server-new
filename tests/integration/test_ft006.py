import pytest
import pytest_asyncio
import asyncio
from server import app
from data.event import ServerEvent, ClientEvent
from data.payload import ServerMessage
from data.conn import Message
from data.board import Point
from data.board.cursorboard import Color
from data.cursor import Cursor
from core.event import Event
from handler.cursor import CursorHandler
from handler.connection import ConnectionHandler
from tests.utils import PytestTCM, assert_wait_event, assert_wait_message, assert_wait_call_if
from unittest.mock import patch
from datetime import datetime
from freezegun import freeze_time
import time

CL_A = "TestClient_A"
CL_B = "TestClient_B"


@pytest.fixture
def frozen_time():
    """시간 고정용 fixture"""
    now = datetime(2025, 1, 1, 0, 0, 0)
    with freeze_time(now):
        yield now


@pytest.mark.asyncio
async def test_ft006_join_scenario():
    """
    FT-006 접속 시나리오 검증:
    1. scoreboard를 보여준다. (JOIN 시)
    2. 사용자의 cursor를 생성한다. (CREATE_CURSOR → MY_CURSOR)
    3. 시야 범위 내의 board를 보여준다. (CREATE_CURSOR → TILES_STATE)
    4. 사용자의 cursor와 시야 범위 내의 cursor를 보여준다. (CREATE_CURSOR → CURSORS_STATE)
    """
    with PytestTCM(app).append_client(CL_A) as tcm:
        cl_a = tcm.get_client(CL_A)

        # 시나리오 1: JOIN 시 SCOREBOARD_STATE 수신 검증
        expected_scoreboard = Message(
            event=Event(
                event_name=ServerEvent.SCOREBOARD_STATE,
                payload=ServerMessage.ScoreBoardState(scoreboard={})
            )
        )
        assert_wait_message(cl_a.conn.send, expected_scoreboard)

        # CREATE_CURSOR 이벤트 전송
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.CREATE_CURSOR.value},
            "payload": {"width": 10, "height": 10, "color": Color.RED.value}
        })

        # 시나리오 2: MY_CURSOR 수신 검증
        expected_my_cursor = Message(
            event=Event(
                event_name=ServerEvent.MY_CURSOR,
                payload=ServerMessage.MyCursor(id=CL_A)
            )
        )
        assert_wait_message(cl_a.conn.send, expected_my_cursor)

        # 시나리오 4: CURSORS_STATE 수신 검증 (position은 비즈니스 규칙 테스트에서 검증)
        assert_wait_call_if(
            cl_a.conn.send,
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
            cl_a.conn.send,
            lambda msg: (
                msg.event.event_name == ServerEvent.TILES_STATE and
                len(msg.event.payload.tiles_li) > 0  # tiles가 존재하는지만 확인
            ),
            timeout=3.0,
            error_msg="TILES_STATE를 받지 못함"
        )


@pytest.mark.asyncio
async def test_ft006_business_rule_initial_position(frozen_time):
    """
    비즈니스 규칙 검증:
    - cursor는 항상 시작 지점(0, 0)에 생성된다.
    """
    with PytestTCM(app).append_client(CL_A) as tcm:
        cl_a = tcm.get_client(CL_A)

        # CREATE_CURSOR 전송
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.CREATE_CURSOR.value},
            "payload": {"width": 5, "height": 5, "color": Color.RED.value}
        })

        # CURSORS_STATE 수신 대기 (cursor 생성 완료 확인)
        assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)

        # Server 내부 상태 확인: 예상 cursor 객체와 완전히 일치하는지 검증
        expected_cursor = Cursor.create(CL_A, width=5, height=5, color=Color.RED)
        actual_cursor = await CursorHandler.get_by_id(CL_A)
        assert actual_cursor == expected_cursor


@pytest.mark.asyncio
async def test_ft006_business_rule_color_must_be_unique(frozen_time):
    """
    비즈니스 규칙 검증:
    - color는 중복될 수 없다.
    """
    with PytestTCM(app).append_client(CL_A).append_client(CL_B) as tcm:
        cl_a = tcm.get_client(CL_A)
        cl_b = tcm.get_client(CL_B)

        # 기준 cursor 생성
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.CREATE_CURSOR.value},
            "payload": {"width": 5, "height": 5, "color": Color.RED.value}
        })
        assert_wait_call_if(
            cl_a.conn.send,
            lambda msg: (
                msg.event.event_name == ServerEvent.MY_CURSOR and
                msg.event.payload.id == CL_A
            ),
            timeout=3.0,
            error_msg="기준 cursor 생성(MY_CURSOR) 실패"
        )

        # 중복 color 생성 시도
        cl_b.conn.send.await_args_list.clear()
        cl_b.ws.send_json({
            "header": {"event": ClientEvent.CREATE_CURSOR.value},
            "payload": {"width": 5, "height": 5, "color": Color.RED.value}
        })

        # 중복 color 요청자는 MY_CURSOR를 받지 않아야 함
        with pytest.raises(AssertionError):
            assert_wait_call_if(
                cl_b.conn.send,
                lambda msg: (
                    msg.event.event_name == ServerEvent.MY_CURSOR and
                    msg.event.payload.id == CL_B
                ),
                timeout=0.8,
                error_msg="중복 color인데 MY_CURSOR가 발행됨"
            )

        # 중복 color 요청자는 본인 CURSORS_STATE를 받지 않아야 함
        with pytest.raises(AssertionError):
            assert_wait_call_if(
                cl_b.conn.send,
                lambda msg: (
                    msg.event.event_name == ServerEvent.CURSORS_STATE and
                    any(cur.id == CL_B for cur in msg.event.payload.cursors)
                ),
                timeout=0.8,
                error_msg="중복 color인데 본인 CURSORS_STATE가 발행됨"
            )


@pytest.mark.asyncio
async def test_ft006_state_change_cursor_creation(frozen_time):
    """
    상태 변화 검증:
    - 없음 → cursor 생성 (Server 내부 상태 기준)
    """
    with PytestTCM(app).append_client(CL_A) as tcm:
        cl_a = tcm.get_client(CL_A)

        # Before: cursor 없음
        try:
            await CursorHandler.get_by_id(CL_A)
            assert False, "cursor가 이미 존재함 (초기 상태가 잘못됨)"
        except KeyError:
            pass  # 예상된 동작: cursor 없음

        # CREATE_CURSOR 전송
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.CREATE_CURSOR.value},
            "payload": {"width": 5, "height": 5, "color": Color.RED.value}
        })

        # CURSORS_STATE 수신 대기 (cursor 생성 완료 확인)
        assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)

        # After: cursor 생성됨 (Server 내부 상태 검증)
        expected_cursor = Cursor.create(CL_A, width=5, height=5, color=Color.RED)
        actual_cursor = await CursorHandler.get_by_id(CL_A)
        assert actual_cursor == expected_cursor
