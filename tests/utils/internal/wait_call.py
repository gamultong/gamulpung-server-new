import time
from unittest.mock import AsyncMock, _Call


def assert_wait_call(mock: AsyncMock, call: _Call, timeout=1.5, step=0.01):
    """
    integration test에서 mock call을 확인할 경우 사용

    이는 TestClient의 동작이 끝나기 전 assert를 확인하는 경우를 위해 만들어짐
    integration test에 mock call시 사용 권장
    """

    end = 0
    while end < timeout:
        if call in mock.await_args_list:
            return
        time.sleep(step)
        end += step
    print(mock.await_args_list)
    raise AssertionError(f"TimeOut : {call}이 {timeout}초 동안 호출되지 않음")
