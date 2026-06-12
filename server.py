from loguru import logger
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi import WebSocket, Response, WebSocketDisconnect
from websockets.exceptions import ConnectionClosed
from core.broker import EventBroker
from data.conn import InvalidFormat_Exception, InvalidEvent_Exception
from handler.connection import ConnectionHandler, Conn
from handler.board import initialize_board
from handler.bomb import start_bomb_scheduler, stop_bomb_scheduler
from handler.board.storage import get_db, set_table, set_cursor_table
import sentry_sdk
from config import SentryConfig
from asyncio import sleep
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

# SENTRY_DSN이 있을 때만 Sentry 초기화
if SentryConfig.SENTRY_DSN:
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
    async with get_db() as db:
        # 테이블 생성은 IF NOT EXISTS로 멱등하다
        await set_table(db)
        await set_cursor_table(db)

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
        raise RuntimeError(f"처리 중인 이벤트가 남아 종료 대기 {timeout}초를 초과함")

app = FastAPI(lifespan=lifespan)


@app.websocket("/session")
async def session(ws: WebSocket):
    conn = await Conn.create(ws)

    await ConnectionHandler.join(conn)

    try:
        while True:
            try:
                message = await conn.receive()
            except (InvalidFormat_Exception, InvalidEvent_Exception) as e:
                # 잘못된 메시지는 연결을 끊지 않고 무시한다
                logger.warning(f"[{conn.id}]잘못된 client-message 수신 | {e}")
                continue
            logger.debug(f"[{conn.id}]client-message : \n{message}")

            client_event = message.event
            await ConnectionHandler.publish_client_event(client_event)

    except (WebSocketDisconnect, ConnectionClosed):
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
    1 / 0


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
