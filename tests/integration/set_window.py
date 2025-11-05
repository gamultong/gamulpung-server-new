from handler.board import BoardHandler, Section
from handler.board.internal.section import Config
from data.board import Point, Tile, Tiles, PointRange
from core.event import Event
from data.payload import ServerMessage
from data.cursor import Cursor
from data.conn import Message
from unittest import TestCase
from .map.case1 import case_1_map, CLOSED_TILE, OPENED_TILE
from server import app
from typing import cast
from unittest.mock import AsyncMock, call, patch
from tests.utils import assert_wait_call, TestClientManager

EXAMPLE_MSG = {
    "header": {"event": "SET-WINDOW"},
    "payload": {"width": 2, "height": 2},
}
CL_A = "Example_A"

clinetmanager = (
    TestClientManager(app)
    .append_client(CL_A)
)

"""
CCCCC
OOOOC
OOOOC
OOOOC
OOOOC
"""
jungdap = Tiles(
    bytearray([
        CLOSED_TILE, CLOSED_TILE, CLOSED_TILE, CLOSED_TILE, CLOSED_TILE,
        OPENED_TILE, OPENED_TILE, OPENED_TILE, OPENED_TILE, CLOSED_TILE,
        OPENED_TILE, OPENED_TILE, OPENED_TILE, OPENED_TILE, CLOSED_TILE,
        OPENED_TILE, OPENED_TILE, OPENED_TILE, OPENED_TILE, CLOSED_TILE,
        OPENED_TILE, OPENED_TILE, OPENED_TILE, OPENED_TILE, CLOSED_TILE,
    ]), 5, 5
)


class SetWindowScenario(TestCase):
    def setUp(self) -> None:
        BoardHandler.section_dict = case_1_map()
        Config.LENGTH = 3  # type:ignore

    def tearDown(self) -> None:
        BoardHandler.section_dict = {}
        Config.LENGTH = 100

    @clinetmanager
    def test_normal(self, tcm: TestClientManager):

        cl_a = tcm.get_client(CL_A)
        cl_a.ws.send_json(EXAMPLE_MSG)

        conn_a_send_mock = cast(AsyncMock, cl_a.conn.send)

        event = Message(
            Event(
                event_name="CURSORS-STATE",
                payload=ServerMessage.CursorsState(
                    [Cursor.create(id=CL_A, width=2, height=2)]
                )
            )
        )

        assert_wait_call(
            conn_a_send_mock,
            call=call(event)
        )

        elem = ServerMessage.TilesState.Elem(
            data=jungdap.to_str(),
            range=PointRange(Point(-2, 2), Point(2, -2))
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
