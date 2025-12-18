from config import BoardConfig
from data.board import Point, Tiles, PointRange
from core.event import Event
from data.payload import ServerMessage
from data.cursor import Cursor
from data.conn import Message
from data.event import ClientEvent, ServerEvent

from .map.builder import build_tiles
from .map.helpers import setup_case_1_map
from server import app
from typing import cast
from unittest.mock import AsyncMock, call, patch
from tests.utils import assert_wait_call, TCM, TestCase, set_board

CREATE_CURSOR_MSG = {
    "header": {"event": ClientEvent.CREATE_CURSOR},
    "payload": {"width": 2, "height": 2},
}
EXAMPLE_MSG = {
    "header": {"event": ClientEvent.SET_WINDOW},
    "payload": {"width": 2, "height": 2},
}
CL_A = "Example_A"

clinetmanager = (
    TCM(app)
    .append_client(CL_A)
)

"""
CCCCC
OOOOC
OOOOC
OOOOC
OOOOC
"""

map_str = """\
#####
....#
....#
....#
....#
"""
jungdap = build_tiles(map_str)

class SetWindowScenario(TestCase.IntegrationTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.section_length_patch = patch.object(BoardConfig, "LENGTH", new=3)
        self.section_length_patch.start()

    def tearDown(self) -> None:
        self.section_length_patch.stop()
        super().tearDown()

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()

    async def asyncTearDown(self) -> None:
        await super().asyncTearDown()

    @set_board(setup_case_1_map)
    @clinetmanager
    def test_normal(self, tcm: TCM):

        cl_a = tcm.get_client(CL_A)
        cl_a.ws.send_json(CREATE_CURSOR_MSG)
        cl_a.ws.send_json(EXAMPLE_MSG)

        conn_a_send_mock = cast(AsyncMock, cl_a.conn.send)

        event = Message(
            Event(
                event_name=ServerEvent.CURSORS_STATE,
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
                event_name=ServerEvent.TILES_STATE,
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
