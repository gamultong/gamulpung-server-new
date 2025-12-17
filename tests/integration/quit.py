from core.event import Event
from data.payload import IdPayload
from unittest import TestCase
from server import app
from unittest.mock import AsyncMock, call, patch
from tests.utils import assert_wait_call, TestClientManager, TestCase
from data.payload import ServerMessage
from data.conn import Message
from data.event import ClientEvent, ServerEvent

from config import BoardConfig
from typing import cast

CL_A = "Example_A"
CL_B = "Example_B"

CREATE_CURSOR_MSG = {
    "header": {"event": ClientEvent.CREATE_CURSOR},
    "payload": {"width": 1, "height": 1},
}
SET_WINDOW_MSG = {
    "header": {"event": ClientEvent.SET_WINDOW},
    "payload": {"width": 1, "height": 1},
}

clinetmanager = (
    TestClientManager(app)
    .append_client(CL_A)
    .append_client(CL_B)
)


class QuitScenario(TestCase.IntegrationTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.section_length_patch = patch.object(BoardConfig, "LENGTH", new=3)
        self.section_length_patch.start()

    def tearDown(self) -> None:
        self.section_length_patch.stop()
        super().tearDown()

    @clinetmanager
    def test_normal(self, tcm: TestClientManager):
        """
        현재 quit시 external 없음
        그래서 broker mock 이후 quit 호출 test
        """
        cl_a = tcm.get_client(CL_A)
        cl_b = tcm.get_client(CL_B)

        cl_a.ws.close()

        conn_b_send_mock = cast(AsyncMock, cl_b.conn.send)

        event = Message(
            Event(
                event_name=ServerEvent.QUIT_CURSOR,
                payload=ServerMessage.QuitCursor(
                    id=CL_A
                )
            )
        )

        assert_wait_call(
            conn_b_send_mock,
            call=call(event)
        )


if __name__ == "__main__":
    from unittest import main
    main()
