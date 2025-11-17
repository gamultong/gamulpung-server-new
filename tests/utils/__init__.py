from .internal.profile import profile
from .internal.conn_mock import TestClientManager
from .internal.wait_call import assert_wait_call
from .internal.set_board import set_board


class TestCase:
    from .internal.use_db_tc import (
        UseDB_TestCase,
        UseTable_TestCase
    )
    from .internal.time_freeze_tc import (
        TimeFreeze_TestCase
    )
    from .internal.integarction_tc import (
        IntegrationTestCase
    )
