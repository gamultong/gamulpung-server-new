"""통합 테스트 공통 fixture"""
import pytest_asyncio
from unittest.mock import patch
from handler.cursor import CursorHandler
from handler.connection import ConnectionHandler
from config import BoardConfig
import tempfile
import os


@pytest_asyncio.fixture(autouse=True)
async def cleanup_db():
    """테스트 전후 핸들러 상태 정리 및 테스트당 격리된 임시 파일 DB 사용"""
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
