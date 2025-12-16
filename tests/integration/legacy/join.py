from core.event import Event
from data.payload import ServerMessage
from data.conn import Message
from data.event import ServerEvent

from unittest import TestCase
from server import app
from typing import cast
from unittest.mock import AsyncMock, call
from tests.utils import assert_wait_call, TCM

CL_A = "Example_A"

clinetmanager = (
    TCM(app)
    .append_client(CL_A)
)


class JoinScenario(TestCase):
    @clinetmanager
    def test_normal(self, tcm: TCM):
        cl_a = tcm.get_client(CL_A)

        conn_a_send_mock = cast(AsyncMock, cl_a.conn.send)

        message = Message(
            event=Event(
                event_name=ServerEvent.MY_CURSOR,
                payload=ServerMessage.MyCursor(
                    id=CL_A,
                )
            )
        )

        assert_wait_call(conn_a_send_mock, call(message), timeout=3)


if __name__ == "__main__":
    from unittest import main
    main()
