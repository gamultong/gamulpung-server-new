from dataclasses import dataclass
from contextlib import ExitStack
from fastapi import WebSocket, FastAPI
from fastapi.testclient import TestClient
from starlette.testclient import WebSocketTestSession

from unittest.mock import patch, AsyncMock
from handler.connection import Conn


class MockConn(Conn):
    send: AsyncMock


@dataclass
class Client:
    ws: WebSocketTestSession
    conn: MockConn


@dataclass
class TCM:
    """
    Test Client Manager
    """
    app: FastAPI

    def __post_init__(self):
        self.client_name: list[str] = []
        self.client_dict: dict[str, Client] = {}
        self.conn_dict: dict[str, MockConn] = {}
        self.conn_create_mock: AsyncMock

    def append_client(self, name):
        assert name not in self.client_name
        self.client_name.append(name)

        return self

    def get_client(self, name):
        return self.client_dict[name]

    def __call__(self, func):
        """
        integration test를 위해 제작되었습니다.
        반드시 tcm을 **kwargs로 받아주세요.
        """
        origin_create = Conn.create

        names_iter = iter(self.client_name)

        async def _side_effect(ws: WebSocket):
            name = next(names_iter)
            conn = await origin_create(ws, name)
            conn.send = AsyncMock()
            self.conn_dict[name] = conn  # type:ignore
            return conn

        @patch("handler.connection.Conn.create", side_effect=_side_effect)
        def wrapper(test, *args, **kwargs):
            # patch:Conn.create
            self.conn_create_mock = args[0]
            with TestClient(self.app) as client:
                with ExitStack() as stack:
                    sockets = {
                        name: stack.enter_context(client.websocket_connect("/session"))
                        for name in self.client_name
                    }

                    self.client_dict = {
                        name: Client(ws=sockets[name], conn=self.conn_dict[name])
                        for name in self.client_name
                    }

                    kwargs["tcm"] = self

                    # patch:Conn.create 제거 -> tcm으로 접근 가능
                    return func(test, *args[1:], **kwargs)

        return wrapper


@dataclass
class PytestTCM:
    """Test Client Manager (pytest용 context manager)"""
    app: FastAPI

    def __post_init__(self):
        self.client_name: list[str] = []
        self.client_dict: dict[str, Client] = {}
        self.conn_dict: dict[str, MockConn] = {}
        self._test_client = None
        self._patch = None
        self._exit_stack = None

    def append_client(self, name: str):
        """클라이언트 추가"""
        assert name not in self.client_name
        self.client_name.append(name)
        return self

    def get_client(self, name: str) -> Client:
        """클라이언트 조회"""
        return self.client_dict[name]

    def __enter__(self):
        """Context manager 진입"""
        origin_create = Conn.create
        names_iter = iter(self.client_name)

        async def _side_effect(ws: WebSocket, id: str = None):
            if id is None:
                name = next(names_iter)
            else:
                name = id
            conn = await origin_create(ws, name)
            conn.send = AsyncMock()
            self.conn_dict[name] = conn  # type:ignore
            return conn

        # Conn.create patch 시작
        self._patch = patch("handler.connection.Conn.create", side_effect=_side_effect)
        self._patch.__enter__()

        # TestClient 생성
        self._test_client = TestClient(self.app)
        self._test_client.__enter__()

        # WebSocket 연결 생성
        self._exit_stack = ExitStack()
        self._exit_stack.__enter__()

        sockets = {
            name: self._exit_stack.enter_context(
                self._test_client.websocket_connect("/session")
            )
            for name in self.client_name
        }

        # Client 객체 생성
        self.client_dict = {
            name: Client(ws=sockets[name], conn=self.conn_dict[name])
            for name in self.client_name
        }

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        # 역순으로 정리
        if self._exit_stack:
            self._exit_stack.__exit__(exc_type, exc_val, exc_tb)
        if self._test_client:
            self._test_client.__exit__(exc_type, exc_val, exc_tb)
        if self._patch:
            self._patch.__exit__(exc_type, exc_val, exc_tb)
