from handler.board import BoardHandler, Section
from config import BoardConfig
from data.board import Point, Tile, Tiles, PointRange
from core.event import Event
from data.payload import ServerMessage
from data.cursor import Cursor
from data.conn import Message
from .map.case2 import CLOSED_TILE, OPENED_TILE, FLAGED_TILE
from .map.helpers import setup_case_2_map, setup_case_2_map_f
from server import app
from typing import cast
from unittest.mock import AsyncMock, call, patch
from tests.utils import assert_wait_call, TestClientManager
from tests.integration.base import IntegrationTestCase

SET_WINDOW_MSG = {
    "header": {"event": "SET-WINDOW"},
    "payload": {"width": 1, "height": 1},
}
OPEN_TILES_MSG = {
    "header": {"event": "SET-FLAG"},
    "payload": {
        "position": {
            "x": 1,
            "y": 0
        }
    },
}
CL_A = "Example_A"

clinetmanager = (
    TestClientManager(app)
    .append_client(CL_A)
)


"""
CCC
FOO
CCC
"""
jungdap = Tiles(
    bytearray([
        FLAGED_TILE,
    ]), 1, 1
)
jungdap_2 = Tiles(
    bytearray([
        CLOSED_TILE,
    ]), 1, 1
)


class SetFlagScenario(IntegrationTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.section_length_patch = patch.object(BoardConfig, "LENGTH", new=2)
        self.section_length_patch.start()

    def tearDown(self) -> None:
        self.section_length_patch.stop()
        super().tearDown()

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        await setup_case_2_map(self.db)

    async def asyncTearDown(self) -> None:
        await super().asyncTearDown()

    @clinetmanager
    def test_set_flag(self, tcm: TestClientManager):

        cl_a = tcm.get_client(CL_A)
        cl_a.ws.send_json(SET_WINDOW_MSG)
        cl_a.ws.send_json(OPEN_TILES_MSG)

        conn_a_send_mock = cast(AsyncMock, cl_a.conn.send)

        elem = ServerMessage.TilesState.Elem(
            data=jungdap.to_str(),
            range=PointRange(Point(1, 0), Point(1, 0))
        )

        event = Message(
            Event(
                event_name="TILES-STATE",
                payload=ServerMessage.TilesState(
                    [elem]
                )
            )
        )

        assert_wait_call(
            conn_a_send_mock,
            call=call(event)
        )


class UnsetFlagScenario(IntegrationTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.section_length_patch = patch.object(BoardConfig, "LENGTH", new=2)
        self.section_length_patch.start()

    def tearDown(self) -> None:
        self.section_length_patch.stop()
        super().tearDown()

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        await setup_case_2_map_f(self.db)

    async def asyncTearDown(self) -> None:
        await super().asyncTearDown()

    @clinetmanager
    def test_unset_flag(self, tcm: TestClientManager):

        cl_a = tcm.get_client(CL_A)
        cl_a.ws.send_json(SET_WINDOW_MSG)
        cl_a.ws.send_json(OPEN_TILES_MSG)

        conn_a_send_mock = cast(AsyncMock, cl_a.conn.send)

        elem = ServerMessage.TilesState.Elem(
            data=jungdap_2.to_str(),
            range=PointRange(Point(1, 0), Point(1, 0))
        )

        event = Message(
            Event(
                event_name="TILES-STATE",
                payload=ServerMessage.TilesState(
                    [elem]
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
