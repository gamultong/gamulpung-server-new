from handler.board import BoardHandler, Section
from handler.board.internal.section import Config
from data.board import Point, Tile, Tiles, PointRange
from core.event import Event
from data.payload import ServerMessage
from data.cursor import Cursor
from data.conn import Message
from unittest import TestCase
from unittest.mock import MagicMock
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


OPENED_TILE = Tile(
    is_open=True,
    is_mine=False,
    is_flag=False,
    number=0
).data

CLOSED_TILE = Tile(
    is_open=False,
    is_mine=False,
    is_flag=False,
    number=0
).data

data1 = bytearray([
    CLOSED_TILE, CLOSED_TILE, CLOSED_TILE,
    CLOSED_TILE, OPENED_TILE, OPENED_TILE,
    CLOSED_TILE, OPENED_TILE, OPENED_TILE,
])
data2 = bytearray([
    CLOSED_TILE, CLOSED_TILE, CLOSED_TILE,
    OPENED_TILE, OPENED_TILE, CLOSED_TILE,
    OPENED_TILE, OPENED_TILE, CLOSED_TILE,
])
data3 = bytearray([
    CLOSED_TILE, OPENED_TILE, OPENED_TILE,
    CLOSED_TILE, OPENED_TILE, OPENED_TILE,
    CLOSED_TILE, CLOSED_TILE, CLOSED_TILE,
])
data4 = bytearray([
    OPENED_TILE, OPENED_TILE, CLOSED_TILE,
    OPENED_TILE, OPENED_TILE, CLOSED_TILE,
    CLOSED_TILE, CLOSED_TILE, CLOSED_TILE,
])

tiles1 = Tiles(data1, 3, 3)
tiles2 = Tiles(data2, 3, 3)
tiles3 = Tiles(data3, 3, 3)
tiles4 = Tiles(data4, 3, 3)

point1 = Point(-1, 0)
point2 = Point(0, 0)
point3 = Point(-1, -1)
point4 = Point(0, -1)

"""
CCC|CCC
COO|OOC
COO|OOC
-------
COO|OOC
COO|OOC
CCC|CCC
"""
BoardHandler.section_dict = {
    point1: Section(point1, tiles1),
    point2: Section(point2, tiles2),
    point3: Section(point3, tiles3),
    point4: Section(point4, tiles4)
}


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
    @clinetmanager
    def test_normal(self, tcm: TestClientManager):
        Config.LENGTH = 3

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
