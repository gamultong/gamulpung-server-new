from fastapi.websockets import WebSocket, WebSocketState
from data.conn import Message
from data.payload import IdDataPayload
from core.event import Event

from dataclasses import dataclass
from uuid import uuid4
from loguru import logger

"""
{
	"header": {
		"event": <event-name>
	},
	"content": <content>
}
"""


@dataclass
class Conn():
    id: str
    conn: WebSocket

    @staticmethod
    async def create(ws: WebSocket, id: str | None = None):
        await ws.accept()
        if id is None:
            id = uuid4().hex
        return Conn(id=id, conn=ws)

    async def accept(self):
        await self.conn.accept()

    async def close(self):
        await self.conn.close()

    async def receive(self) -> Message[Event[IdDataPayload]]:
        row_json = await self.conn.receive_json()
        logger.debug(f"[{self.id}]client-message row_json: \n{row_json}")

        message = Message[Event].from_json(row_json)
        message.event.payload = IdDataPayload(id=self.id, data=message.event.payload)

        return message

    async def send(self, msg: Message):
        logger.debug(f"[{self.id}]server-message: \n{msg}")

        row_json = msg.to_dict()
        logger.debug(f"[{self.id}]server-message row: \n{row_json}")

        if not (self.conn.application_state == WebSocketState.CONNECTED):
            # 커넥션이 종료되었는데도 타이밍 문제로 인해 커넥션을 가져왔을 수 있음.
            logger.warning(f"Connection이 끊김에도 이를 send하려함 : {self}")
            return

        # comment : https://github.com/gamultong/gamulpung-server-new/pull/1#discussion_r2492845020
        try:
            await self.conn.send_json(row_json)
        except RuntimeError as e:
            # uvicorn이 던지는 그 에러인 경우만 잡아서 로그로 남기고 무시
            if "websocket.close" in str(e) or "response already completed" in str(e):
                logger.warning(f"Connection이 끊긴 뒤 send하려함(예외로 감지) : {self}; err={e}")
                return
            # 다른 RuntimeError면 그대로 올림
            raise
