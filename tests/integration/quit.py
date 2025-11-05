from core.event import Event
from data.payload import IdPayload
from unittest import TestCase
from server import app
from unittest.mock import AsyncMock, call, patch
from tests.utils import assert_wait_call, TestClientManager

CL_A = "Example_A"

clinetmanager = (
    TestClientManager(app)
    .append_client(CL_A)
)


class QuitScenario(TestCase):
    @clinetmanager
    @patch("core.broker.EventBroker.publish")
    def test_normal(self, event_broker: AsyncMock, tcm: TestClientManager):
        """
        현재 quit시 external 없음
        그래서 broker mock 이후 quit 호출 test
        """
        cl_a = tcm.get_client(CL_A)

        cl_a.ws.close()

        event = Event(
            event_name="QUIT",
            payload=IdPayload(id=CL_A)
        )

        assert_wait_call(
            event_broker,
            call(event)
        )


if __name__ == "__main__":
    from unittest import main
    main()
