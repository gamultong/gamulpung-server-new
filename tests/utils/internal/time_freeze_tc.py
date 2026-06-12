from unittest import IsolatedAsyncioTestCase
from datetime import datetime

from freezegun import freeze_time


class TimeFreeze_TestCase(IsolatedAsyncioTestCase):
    """시간 흐름을 배제한 TestCase"""

    def setUp(self) -> None:
        super().setUp()
        self.now = datetime.now()
        self.freezer_context = freeze_time(self.now)
        self.freezer = self.freezer_context.__enter__()

    def tearDown(self) -> None:
        super().tearDown()
        self.freezer_context.__exit__()
