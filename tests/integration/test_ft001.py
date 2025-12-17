import pytest
from tests.utils import TCM, assert_wait_message, assert_wait_event
from server import app
from data.event import ServerEvent, ClientEvent
from data.payload import ServerMessage
from data.conn import Message
from data.board import Point
from core.event import Event
from handler.cursor import CursorHandler
from unittest.mock import AsyncMock
from typing import cast

CL_A = "TestClient_A"  # 송신자
CL_B = "TestClient_B"  # 시야 내 수신자
CL_C = "TestClient_C"  # 시야 밖 사용자


@pytest.fixture
def tcm_two_clients():
    """2명 클라이언트 (시나리오 테스트용)"""
    return TCM(app).append_client(CL_A).append_client(CL_B)


@pytest.fixture
def tcm_three_clients():
    """3명 클라이언트 (비즈니스 규칙 테스트용)"""
    return (
        TCM(app)
        .append_client(CL_A)
        .append_client(CL_B)
        .append_client(CL_C)
    )


@pytest.mark.asyncio
async def test_ft001_chat_scenario(tcm_two_clients: TCM):
    """
    FT-001 채팅 시나리오 검증:
    1. 사용자가 채팅 메시지를 전송한다.
    2. 해당 사용자의 cursor를 시야 내에 두고 있는 다른 사용자들이 메시지를 수신한다.
    """
    async with tcm_two_clients:
        cl_a = tcm_two_clients.get_client(CL_A)
        cl_b = tcm_two_clients.get_client(CL_B)
        conn_a_send_mock = cast(AsyncMock, cl_a.conn.send)
        conn_b_send_mock = cast(AsyncMock, cl_b.conn.send)

        # 접속: CREATE_CURSOR로 cursor 생성 (FT-006 의존)
        cl_a.ws.send_json({
            "header": {"event": ClientEvent.CREATE_CURSOR.value},
            "payload": {"width": 10, "height": 10}
        })
        cl_b.ws.send_json({
            "header": {"event": ClientEvent.CREATE_CURSOR.value},
            "payload": {"width": 10, "height": 10}
        })

        # cursor 생성 완료 대기
        assert_wait_event(conn_a_send_mock, ServerEvent.CURSORS_STATE, timeout=3.0)
        assert_wait_event(conn_b_send_mock, ServerEvent.CURSORS_STATE, timeout=3.0)

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
        assert_wait_message(conn_b_send_mock, expected_chat, timeout=3.0)


@pytest.mark.asyncio
async def test_ft001_business_rule_visibility(tcm_three_clients: TCM):
    """
    비즈니스 규칙 검증:
    - 메시지는 발신자의 cursor를 볼 수 있는 사용자에게만 전달된다.
    """
    async with tcm_three_clients:
        cl_a = tcm_three_clients.get_client(CL_A)
        cl_b = tcm_three_clients.get_client(CL_B)
        cl_c = tcm_three_clients.get_client(CL_C)
        conn_a_send_mock = cast(AsyncMock, cl_a.conn.send)
        conn_b_send_mock = cast(AsyncMock, cl_b.conn.send)
        conn_c_send_mock = cast(AsyncMock, cl_c.conn.send)

        # 접속: 모든 클라이언트 cursor 생성
        for cl in [cl_a, cl_b, cl_c]:
            cl.ws.send_json({
                "header": {"event": ClientEvent.CREATE_CURSOR.value},
                "payload": {"width": 5, "height": 5}
            })

        # cursor 생성 완료 대기
        assert_wait_event(conn_a_send_mock, ServerEvent.CURSORS_STATE, timeout=3.0)
        assert_wait_event(conn_b_send_mock, ServerEvent.CURSORS_STATE, timeout=3.0)
        assert_wait_event(conn_c_send_mock, ServerEvent.CURSORS_STATE, timeout=3.0)

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
        assert_wait_message(conn_b_send_mock, expected_chat, timeout=3.0)

        # C는 메시지 미수신 (시야 범위 밖)
        import time
        time.sleep(0.5)  # 충분히 대기
        chat_events = [
            call[0][0].event.event_name
            for call in conn_c_send_mock.await_args_list
            if call[0]
        ]
        assert ServerEvent.CHAT not in chat_events, "시야 범위 밖 사용자가 메시지를 수신함"
