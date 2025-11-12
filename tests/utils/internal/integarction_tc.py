from .time_freeze_tc import TimeFreeze_TestCase
from .use_db_tc import UseTable_TestCase


class IntegrationTestCase(TimeFreeze_TestCase, UseTable_TestCase):
    pass
