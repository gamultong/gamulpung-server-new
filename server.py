from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, Response, WebSocketDisconnect
from websockets.exceptions import ConnectionClosed
from handler.connection import ConnectionHandler, Conn
from handler.board import initialize_start_map
from handler.board.storage import _get_db, set_table

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    # setup

    # TODO : is table 같은거 구현 S
    async with _get_db() as db:
        try:
            await set_table(db)
        except:
            pass

        await initialize_start_map(db)

    yield  # app 실행

    # teardown

app = FastAPI(lifespan=lifespan)


@app.websocket("/session")
async def session(ws: WebSocket):
    conn = await Conn.create(ws)

    await ConnectionHandler.join(conn)

    while True:
        try:
            message = await conn.receive()

            client_event = message.event
            # print(client_event) # debug 용
            await ConnectionHandler.publish_client_event(client_event)
        except (WebSocketDisconnect, ConnectionClosed) as e:
            # 연결 종료됨
            break

    await ConnectionHandler.quit(conn)


@app.get("/")
def health_check():
    return Response()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
