from fastapi.websockets import WebSocket, WebSocketState, WebSocketDisconnect
from websockets.exceptions import ConnectionClosed
from data.conn import Message
from data.payload import IdDataPayload
from core.event import Event

from dataclasses import dataclass
from uuid import uuid4
import json

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

        message = Message[Event].from_string(row)
        message.event.payload = IdDataPayload(id=self.id, data=message.event.payload)

        return message

    async def send(self, msg: Message):
        if self.conn.application_state == WebSocketState.DISCONNECTED:
            return

        # comment : https://github.com/gamultong/gamulpung-server-new/pull/1#discussion_r2492845020
        try:
            await self.conn.send_json(msg.to_dict())
        except (ConnectionClosed, WebSocketDisconnect):
            # 커넥션이 종료되었는데도 타이밍 문제로 인해 커넥션을 가져왔을 수 있음.
            return
