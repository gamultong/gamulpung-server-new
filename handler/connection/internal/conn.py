from fastapi.websockets import WebSocket, WebSocketState, WebSocketDisconnect
from websockets.exceptions import ConnectionClosed
from data.conn import Message
from data.payload import IdDataPayload
from core.event import Event

from dataclasses import dataclass
from uuid import uuid4
import json
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
        row = await self.conn.receive_text()
        logger.debug(f"[{self.id}]client-message row: \n{row}")

        message = Message[Event].from_string(row)
        message.event.payload = IdDataPayload(id=self.id, data=message.event.payload)

        return message

    async def send(self, msg: Message):
        logger.debug(f"[{self.id}]server-message: \n{msg}")
        if self.conn.application_state == WebSocketState.DISCONNECTED:
            return

        # comment : https://github.com/gamultong/gamulpung-server-new/pull/1#discussion_r2492845020
        try:
            message = msg.to_dict()
            logger.debug(f"[{self.id}]server-message row: \n{message}")
            await self.conn.send_json(message)
        except (ConnectionClosed, WebSocketDisconnect):
            # 커넥션이 종료되었는데도 타이밍 문제로 인해 커넥션을 가져왔을 수 있음.
            return
