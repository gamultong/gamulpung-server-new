import pytest
import pytest_asyncio
import asyncio
from server import app
from data.event import ServerEvent, ClientEvent
from data.payload import ServerMessage
from data.conn import Message
from data.board import Point
from data.board.cursorboard import Color
from core.event import Event
from handler.cursor import CursorHandler
from handler.connection import ConnectionHandler
from tests.utils.internal.conn_mock import PytestTCM
from tests.utils.internal.wait_call import assert_wait_event, assert_wait_message
from config import BoardConfig
from unittest.mock import patch

CL_A = "TestClient_A"  # 송신자
CL_B = "TestClient_B"  # 시야 내 수신자
CL_C = "TestClient_C"  # 시야 밖 사용자


@pytest.mark.asyncio
async def test_ft001_chat_scenario():
    """
    FT-001 채팅 시나리오 검증:
    1. 사용자가 채팅 메시지를 전송한다.
    2. 해당 사용자의 cursor를 시야 내에 두고 있는 다른 사용자들이 메시지를 수신한다.
    """
    with PytestTCM(app).append_client(CL_A).append_client(CL_B) as tcm:
        cl_a = tcm.get_client(CL_A)
        cl_b = tcm.get_client(CL_B)

        # 접속: CREATE_CURSOR로 cursor 생성 (FT-006 의존)
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.CREATE_CURSOR.value},
            "payload": {"width": 10, "height": 10, "color": Color.RED.value}
        })
        cl_b.ws.send_json({
            "header": {"event": ClientEvent.CREATE_CURSOR.value},
            "payload": {"width": 10, "height": 10, "color": Color.BLUE.value}
        })

        # cursor 생성 완료 대기
        assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)
        assert_wait_event(cl_b.conn.send, ServerEvent.CURSORS_STATE)

        # 시나리오 1: 사용자 A가 채팅 메시지 전송
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.CHAT.value},
            "payload": {"message": "Hello, World!"}
        })

        # 시나리오 2: 사용자 B가 메시지 수신 검증
        expected_chat = Message(
            event=Event(
                event_name=ServerEvent.CHAT,
                payload=ServerMessage.Chat(
                    id=CL_A,
                    message="Hello, World!"
                )
            )
        )
        assert_wait_message(cl_b.conn.send, expected_chat)


@pytest.mark.asyncio
async def test_ft001_business_rule_visibility():
    """
    비즈니스 규칙 검증:
    - 메시지는 발신자의 cursor를 볼 수 있는 사용자에게만 전달된다.
    """
    with PytestTCM(app).append_client(CL_A).append_client(CL_B).append_client(CL_C) as tcm:
        cl_a = tcm.get_client(CL_A)
        cl_b = tcm.get_client(CL_B)
        cl_c = tcm.get_client(CL_C)

        # 접속: 모든 클라이언트 cursor 생성
        for idx, cl in enumerate([cl_a, cl_b, cl_c], start=1):
            cl.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 5, "height": 5, "color": idx}
            })

        # cursor 생성 완료 대기
        assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)
        assert_wait_event(cl_b.conn.send, ServerEvent.CURSORS_STATE)
        assert_wait_event(cl_c.conn.send, ServerEvent.CURSORS_STATE)

        # 커서 위치 설정:
        # A: (0, 0) - 기본 위치
        # B: (3, 3) - A의 시야 범위 내 (window: x±5, y±5)
        # C: (20, 20) - A의 시야 범위 밖
        cursor_b = await CursorHandler.get_by_id(CL_B)
        cursor_b.position = Point(3, 3)
        CursorHandler.cursor_dict[CL_B] = cursor_b

        cursor_c = await CursorHandler.get_by_id(CL_C)
        cursor_c.position = Point(20, 20)
        CursorHandler.cursor_dict[CL_C] = cursor_c

        # 사용자 A가 채팅 메시지 전송
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.CHAT.value},
            "payload": {"message": "Test Message"}
        })

        # B는 메시지 수신 (시야 범위 내)
        expected_chat = Message(
            event=Event(
                event_name=ServerEvent.CHAT,
                payload=ServerMessage.Chat(
                    id=CL_A,
                    message="Test Message"
                )
            )
        )
        assert_wait_message(cl_b.conn.send, expected_chat)

        # C는 메시지 미수신 (시야 범위 밖)
        chat_events = [
            call[0][0].event.event_name
            for call in cl_c.conn.send.await_args_list
            if call[0]
        ]
        assert ServerEvent.CHAT not in chat_events, "시야 범위 밖 사용자가 메시지를 수신함"
