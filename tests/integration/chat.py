from unittest import TestCase
from unittest.mock import AsyncMock, call
from typing import cast

from server import app
from core.event import Event

from data.payload import ServerMessage
from data.conn import Message

from tests.utils import TestClientManager, assert_wait_call

EXAMPLE_MSG = {
    "header": {"event": "CHAT"},
    "payload": {"message": "Hi"},
}

CL_A = "Example_A"
CL_B = "Example_B"

clinetmanager = (
    TestClientManager(app)
    .append_client(CL_A)
    .append_client(CL_B)
)


class ChatScenario(TestCase):
    @clinetmanager
    def test_normal(self, tcm: TestClientManager):
        # TODO : Cursor window를 반영하지 않음
        cl_a = tcm.get_client(CL_A)
        cl_b = tcm.get_client(CL_B)

        cl_a.ws.send_json(EXAMPLE_MSG)

        conn_b_send_mock = cast(AsyncMock, cl_b.conn.send)

        message = Message(
            event=Event(
                event_name="CHAT",
                payload=ServerMessage.Chat(
                    id=CL_A,
                    message="Hi"
                )
            )
        )

        assert_wait_call(conn_b_send_mock, call(message), timeout=3)


if __name__ == "__main__":
    from unittest import main
    main()
