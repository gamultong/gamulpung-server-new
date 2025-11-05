from core.event import Event
from data.payload import ServerMessage
from data.cursor import Cursor
from data.conn import Message
from unittest import TestCase
from server import app
from typing import cast
from unittest.mock import AsyncMock, call
from tests.utils import assert_wait_call, TestClientManager

EXAMPLE_MSG = {
    "header": {"event": "SET-WINDOW"},
    "payload": {"width": 10, "height": 10},
}
CL_A = "Example_A"

clinetmanager = (
    TestClientManager(app)
    .append_client(CL_A)
)


class SetWindowScenario(TestCase):
    @clinetmanager
    def test_normal(self, tcm: TestClientManager):
        cl_a = tcm.get_client(CL_A)
        cl_a.ws.send_json(EXAMPLE_MSG)

        conn_a_send_mock = cast(AsyncMock, cl_a.conn.send)

        event = Message(
            Event(
                event_name="CURSORS-STATE",
                payload=ServerMessage.CursorsState(
                    [Cursor(id=CL_A, width=10, height=10)]
                )
            )
        )

        assert_wait_call(
            conn_a_send_mock,
            call=call(event)
        )


if __name__ == "__main__":
    from unittest import main
    main()
