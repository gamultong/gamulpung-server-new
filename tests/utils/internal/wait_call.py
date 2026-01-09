import time
from typing import Callable, TYPE_CHECKING
from unittest.mock import AsyncMock, _Call
from data.conn import Message
from core.event import Event

if TYPE_CHECKING:
    from data.event import ServerEvent


def assert_wait_call_if(
    mock: AsyncMock,
    predicate: Callable[[Message[Event]], bool],
    timeout: float = 1.5,
    step: float = 0.01,
    error_msg: str | None = None
):
    """
    predicate 함수로 유연한 call 검증 (primitive)

    Args:
        mock: 검증할 AsyncMock 객체
        predicate: call의 첫 번째 인자를 받아 bool을 반환하는 함수
        timeout: 대기 시간 (초)
        step: 폴링 간격 (초)
        error_msg: 실패 시 표시할 에러 메시지

    Example:
        assert_wait_call_if(
            mock,
            lambda msg: msg.event.event_name == ServerEvent.MY_CURSOR,
            error_msg="MY_CURSOR 이벤트를 받지 못함"
        )
    """
    elapsed = 0
    while elapsed < timeout:
        for idx, call_args in enumerate(mock.await_args_list):
            if call_args[0] and predicate(call_args[0][0]):
                mock.await_args_list.pop(idx)
                return
        time.sleep(step)
        elapsed += step

    print(mock.await_args_list)
    msg = error_msg or f"predicate를 만족하는 call을 {timeout}초 동안 받지 못함"
    raise AssertionError(msg)


def assert_wait_message(mock: AsyncMock, message: Message[Event], timeout: float = 1.5):
    """
    정확한 Message 객체와 일치하는지 검증 (payload까지 완전 매칭)

    Args:
        mock: 검증할 AsyncMock 객체 (conn.send mock)
        message: 기대하는 Message 객체
        timeout: 대기 시간 (초)

    Example:
        expected = Message(
            event=Event(
                event_name=ServerEvent.MY_CURSOR,
                payload=ServerMessage.MyCursor(id="client_a")
            )
        )
        assert_wait_message(conn_send_mock, expected)
    """
    return assert_wait_call_if(
        mock,
        lambda msg: msg == message,
        timeout=timeout,
        error_msg=f"예상한 Message를 {timeout}초 동안 받지 못함: {message}"
    )


def assert_wait_call(mock: AsyncMock, call: _Call, timeout=1.5, step=0.01):
    """
    [Legacy] mock call 객체로 검증 (하위 호환성 유지)

    새 코드에서는 assert_wait_message 사용 권장
    """
    return assert_wait_call_if(
        mock,
        lambda msg: call([msg]) == call,
        timeout=timeout,
        error_msg=f"TimeOut : {call}이 {timeout}초 동안 호출되지 않음"
    )


def assert_wait_event(mock: AsyncMock, event_name: "ServerEvent", timeout: float = 1.5):
    """
    특정 ServerEvent가 수신되었는지 확인 (payload 무관)

    Args:
        mock: 검증할 AsyncMock 객체 (conn.send mock)
        event_name: 기대하는 ServerEvent
        timeout: 대기 시간 (초)

    Example:
        assert_wait_event(conn_send_mock, ServerEvent.SCOREBOARD_STATE)
    """
    return assert_wait_call_if(
        mock,
        lambda msg: msg.event.event_name == event_name,
        timeout=timeout,
        error_msg=f"{event_name.value} 이벤트를 {timeout}초 동안 받지 못함"
    )
