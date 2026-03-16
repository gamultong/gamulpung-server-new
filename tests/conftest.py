"""통합 테스트 공통 fixture"""
import pytest
import pytest_asyncio
import aiosqlite
from contextlib import asynccontextmanager
from unittest.mock import patch
from handler.cursor import CursorHandler
from handler.connection import ConnectionHandler
from config import BoardConfig
import tempfile
import os
from prometheus_client import REGISTRY


@pytest.fixture(autouse=True)
def cleanup_prometheus():
    """테스트 전후 Prometheus 메트릭 정리

    메트릭이 중복 등록되는 것을 방지한다.
    """
    # 테스트 전 lifecycle 관련 메트릭 정리
    collectors_to_unregister = []
    for collector in list(REGISTRY._collector_to_names.keys()):
        if hasattr(collector, '_name') and collector._name.startswith('lifecycle_'):
            collectors_to_unregister.append(collector)

    for collector in collectors_to_unregister:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass

    yield

    # 테스트 후 정리
    collectors_to_unregister = []
    for collector in list(REGISTRY._collector_to_names.keys()):
        if hasattr(collector, '_name') and collector._name.startswith('lifecycle_'):
            collectors_to_unregister.append(collector)

    for collector in collectors_to_unregister:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass


@pytest_asyncio.fixture(autouse=True)
async def cleanup_db():
    """테스트 전후 핸들러 상태 정리 및 테스트당 단일 공유 인메모리 DB 사용"""
    # 테스트 전 정리
    CursorHandler.cursor_dict.clear()
    ConnectionHandler.conn_dict.clear()

    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    db_patch = patch.object(BoardConfig, "DB_PATH", new=db_path)
    db_patch.start()

    yield

    db_patch.stop()
    os.close(db_fd)
    os.remove(db_path)
    # 테스트 후 정리
    CursorHandler.cursor_dict.clear()
    ConnectionHandler.conn_dict.clear()
