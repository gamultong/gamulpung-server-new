from loguru import logger
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, Response, WebSocketDisconnect
from websockets.exceptions import ConnectionClosed
from core.broker import EventBroker
from handler.connection import ConnectionHandler, Conn
from handler.board import initialize_board
from handler.bomb import start_bomb_scheduler, stop_bomb_scheduler
from handler.board.storage import _get_db, set_table, set_cursor_table
import sentry_sdk
from config import SentryConfig
from asyncio import sleep
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

# SENTRY_DSN이 있을 때만 Sentry 초기화
if hasattr(SentryConfig, 'SENTRY_DSN') and SentryConfig.SENTRY_DSN:
    sentry_sdk.init(
        dsn=SentryConfig.SENTRY_DSN,
        # Add data like request headers and IP for users,
        # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
        send_default_pii=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # setup

    logger.add("log.log")

    logger.debug("init start")
    # TODO : is table 같은거 구현 S
    async with _get_db() as db:
        try:
            await set_table(db)
            await set_cursor_table(db)
        except:
            pass

        await initialize_board(db)
    logger.debug("init end")
    await start_bomb_scheduler()

    yield  # app 실행

    # teardown
    await stop_bomb_scheduler()

    elapsed = 0
    step = 0.1
    timeout = 10
    while elapsed < timeout:
        if EventBroker.is_end():
            break
        await sleep(step)
        elapsed += step
    else:
        raise "문제 있음"

app = FastAPI(lifespan=lifespan)


@app.websocket("/session")
async def session(ws: WebSocket):
    conn = await Conn.create(ws)

    await ConnectionHandler.join(conn)

    try:
        while True:
            message = await conn.receive()
            logger.debug(f"[{conn.id}]client-message : \n{message}")

            client_event = message.event
            await ConnectionHandler.publish_client_event(client_event)

    except (WebSocketDisconnect, ConnectionClosed) as e:
        # 연결 종료됨
        pass

    finally:
        logger.debug(f"[{conn.id}]client-quit")
        await ConnectionHandler.quit(conn.id)


@app.get("/")
def health_check():
    return Response()


@app.get("/sentry-debug")
def div_zero():
    error = 1 / 0


@app.get("/metrics")
def metrics():
    """Prometheus 메트릭 엔드포인트"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
