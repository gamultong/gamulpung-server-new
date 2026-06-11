from loguru import logger
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, Response, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from websockets.exceptions import ConnectionClosed
from core.broker import EventBroker
from handler.connection import ConnectionHandler, Conn
from handler.board import initialize_board
from handler.bomb import start_bomb_scheduler, stop_bomb_scheduler
from handler.cursor import CursorHandler
from handler.stats import get_dashboard
from handler.board.storage import (
    _get_db,
    set_app_log_table,
    set_cursor_table,
    set_stat_event_table,
    set_table,
)
import sentry_sdk
from config import BoardConfig, SentryConfig
from asyncio import sleep
from datetime import datetime, timezone
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from utils.logging import AppLogDbSink

SERVER_STARTED_AT: datetime | None = None

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
    global SERVER_STARTED_AT

    # setup
    SERVER_STARTED_AT = datetime.now(timezone.utc)

    # TODO : is table 같은거 구현 S
    async with _get_db() as db:
        try:
            await set_table(db)
            await set_cursor_table(db)
            await set_app_log_table(db)
            await set_stat_event_table(db)
        except:
            pass

    file_log_sink_id = logger.add("log.log")
    db_log_sink = AppLogDbSink(BoardConfig.DB_PATH, buffer_size=100)
    db_log_sink_id = logger.add(
        db_log_sink,
        level="DEBUG",
        enqueue=True,
    )

    logger.debug("init start")
    async with _get_db() as db:
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

    logger.remove(db_log_sink_id)
    db_log_sink.stop()
    logger.remove(file_log_sink_id)

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/stats/dashboard")
def stats_dashboard(range: str = "24h", bucket: str = "1m", limit: int = 50):
    return get_dashboard(
        BoardConfig.DB_PATH,
        range_value=range,
        bucket=bucket,
        limit=limit,
        active_cursors=_active_cursors(),
        current_connections=len(ConnectionHandler.conn_dict),
        uptime=_uptime(),
    )


def _active_cursors():
    cursors = []
    now = datetime.now(timezone.utc)
    connections = dict(ConnectionHandler.conn_dict)
    connection_ids = set(connections.keys())

    for cursor_id, cursor in list(CursorHandler.cursor_dict.items()):
        if cursor_id not in connection_ids:
            continue

        conn = connections[cursor_id]
        connected_at = _ensure_aware(conn.connected_at)
        position = cursor.position
        cursors.append(
            {
                "connection_id": cursor_id,
                "cursor_id": cursor_id,
                "connected_at": connected_at.isoformat(),
                "session_seconds": max(0, int((now - connected_at).total_seconds())),
                "color": int(cursor.color),
                "tile_id": f"tile:{position.x}:{position.y}",
                "x": position.x,
                "y": position.y,
                "score": cursor.score,
                "is_alive": cursor.is_alive,
                "active_at": cursor.active_at.isoformat(),
                "window": {
                    "width": cursor.width,
                    "height": cursor.height,
                },
            }
        )

    return sorted(cursors, key=lambda cursor: cursor["cursor_id"])


def _uptime():
    if SERVER_STARTED_AT is None:
        return {
            "started_at": None,
            "uptime_seconds": 0,
        }

    started_at = _ensure_aware(SERVER_STARTED_AT)
    return {
        "started_at": started_at.isoformat(),
        "uptime_seconds": max(0, int((datetime.now(timezone.utc) - started_at).total_seconds())),
    }


def _ensure_aware(value: datetime):
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
