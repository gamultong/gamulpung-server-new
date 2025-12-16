from handler.board import BoardHandler
from config import BoardConfig
from data.board import Point, Tile, Tiles, PointRange, Section
from core.event import Event
from data.payload import ServerMessage
from data.cursor import Cursor
from data.conn import Message
from data.event import ClientEvent, ServerEvent

from .map.builder import build_tiles
from .map.open_tiles import case_open_tiles_map
from server import app
from typing import cast
from unittest.mock import AsyncMock, call, patch
from tests.utils import assert_wait_call, TestClientManager, TestCase, set_board
from data.cursor import Cursor

SET_WINDOW_MSG = {
    "header": {"event": ClientEvent.SET_WINDOW},
    "payload": {"width": 1, "height": 1},
}
OPEN_TILES_MSG = {
    "header": {"event": ClientEvent.OPEN_TILES},
    "payload": {
        "position": {
            "x": 1,
            "y": 1
        }
    },
}
CL_A = "Example_A"

clinetmanager = (
    TestClientManager(app)
    .append_client(CL_A)
)

# TODO
# - chaining open 된 곳 확인 해야함

"""
CCC
COO
CCC
"""

map_str = """\
.
"""
jungdap = build_tiles(map_str)

origin_create = Cursor.create


def create_cursor_effect(id: str, width: int = 0, height: int = 0):
    return origin_create(id, width=width, height=height, position=Point(0, 1))


class OpenTilesScenario(TestCase.IntegrationTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.section_length_patch = patch.object(BoardConfig, "LENGTH", new=4)
        self.section_length_patch.start()

    def tearDown(self) -> None:
        self.section_length_patch.stop()
        super().tearDown()

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()

    async def asyncTearDown(self) -> None:
        await super().asyncTearDown()

    @set_board(case_open_tiles_map)
    @patch("data.cursor.Cursor.create", side_effect=create_cursor_effect)
    @clinetmanager
    def test_normal(self, a, tcm: TestClientManager):
        cl_a = tcm.get_client(CL_A)
        cl_a.ws.send_json(SET_WINDOW_MSG)
        cl_a.ws.send_json(OPEN_TILES_MSG)

        conn_a_send_mock = cast(AsyncMock, cl_a.conn.send)

        elem = ServerMessage.TilesState.Elem(
            data=jungdap.to_str(),
            range=PointRange(Point(1, 1), Point(1, 1))
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

        event = Message(
            Event(
                event_name=ServerEvent.CURSORS_STATE,
                payload=ServerMessage.CursorsState(
                    [origin_create(id=CL_A, width=1, height=1, position=Point(0, 1), score=800)]
                )
            )
        )

        assert_wait_call(
            conn_a_send_mock,
            call=call(event)
        )

        event = Message(
            Event(
                event_name=ServerEvent.SCOREBOARD_STATE,
                payload=ServerMessage.ScoreBoardState(
                    scoreboard={
                        1: 800
                    }
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
