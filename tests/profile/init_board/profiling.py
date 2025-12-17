from tests.utils import TestCase, profile
from handler.board import initialize_board
import asyncio


class InitializeStartMap_Profile(TestCase.UseTable_TestCase):
    def setUp(self) -> None:
        loop = asyncio.get_event_loop()
        loop.set_debug(False)
        super().setUp()

    @profile("after2")
    async def test_section_layer_constraint(self):
        await initialize_board(self.db)


if __name__ == "__main__":
    from unittest import main
    main()
