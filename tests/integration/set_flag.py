from handler.board import BoardHandler
from config import BoardConfig
from data.board import Point, Tile, Tiles, PointRange, Section
from core.event import Event, ExternalC2SEvent, ExternalS2CEvent
from data.payload import ServerMessage
from data.cursor import Cursor
from data.conn import Message
from .map.case2 import CLOSED_TILE, OPENED_TILE, FLAGED_TILE
from .map.helpers import setup_case_2_map, setup_case_2_map_f
from server import app
from typing import cast
from unittest.mock import AsyncMock, call, patch
from tests.utils import assert_wait_call, TestClientManager, TestCase, set_board

SET_WINDOW_MSG = {
    "header": {"event": ExternalC2SEvent.SET_WINDOW},
    "payload": {"width": 1, "height": 1},
}
OPEN_TILES_MSG = {
    "header": {"event": ExternalC2SEvent.SET_FLAG},
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


class SetFlagScenario(TestCase.IntegrationTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.section_length_patch = patch.object(BoardConfig, "LENGTH", new=2)
        self.section_length_patch.start()

    def tearDown(self) -> None:
        self.section_length_patch.stop()
        super().tearDown()

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()

    async def asyncTearDown(self) -> None:
        await super().asyncTearDown()

    @set_board(setup_case_2_map)
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
                event_name=ExternalS2CEvent.TILES_STATE,
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
                event_name=ExternalS2CEvent.CURSORS_STATE,
                payload=ServerMessage.CursorsState(
                    [Cursor.create(id=CL_A, width=1, height=1, position=Point(0, 0), score=10)]
                )
            )
        )

        assert_wait_call(
            conn_a_send_mock,
            call=call(event)
        )

        event = Message(
            Event(
                event_name=ExternalS2CEvent.SCOREBOARD_STATE,
                payload=ServerMessage.ScoreBoardState(
                    scoreboard={
                        1: 10
                    }
                )
            )
        )

        assert_wait_call(
            conn_a_send_mock,
            call=call(event)
        )


class UnsetFlagScenario(TestCase.IntegrationTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.section_length_patch = patch.object(BoardConfig, "LENGTH", new=2)
        self.section_length_patch.start()

    def tearDown(self) -> None:
        self.section_length_patch.stop()
        super().tearDown()

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()

    async def asyncTearDown(self) -> None:
        await super().asyncTearDown()

    @set_board(setup_case_2_map_f)
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
                event_name=ExternalS2CEvent.TILES_STATE,
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
                event_name=ExternalS2CEvent.CURSORS_STATE,
                payload=ServerMessage.CursorsState(
                    [Cursor.create(id=CL_A, width=1, height=1, position=Point(0, 0), score=10)]
                )
            )
        )

        assert_wait_call(
            conn_a_send_mock,
            call=call(event)
        )

        event = Message(
            Event(
                event_name=ExternalS2CEvent.SCOREBOARD_STATE,
                payload=ServerMessage.ScoreBoardState(
                    scoreboard={
                        1: 10
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
