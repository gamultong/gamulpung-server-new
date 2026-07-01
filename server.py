from loguru import logger
from fastapi import FastAPI
from contextlib import asynccontextmanager
import os
from fastapi import WebSocket, Response, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from websockets.exceptions import ConnectionClosed
from core.broker import EventBroker
from core.lifecycle import add_lifecycle_sink, remove_lifecycle_sink
from data.conn import InvalidFormat_Exception, InvalidEvent_Exception
from handler.connection import ConnectionHandler, Conn
from handler.board import initialize_board
from handler.bomb import start_bomb_scheduler, stop_bomb_scheduler
from handler.cursor import CursorHandler
from utils.stats import ActiveCursor, CursorWindow, get_dashboard
from handler.board.storage import (
    get_db,
    set_cursor_table,
    set_table,
)
import sentry_sdk
from config import SentryConfig
from datetime import datetime, timezone
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from utils.logging import AppLogDbSink, set_app_log_table, set_stat_event_table
from utils.stats import record_lifecycle, start_stat_event_worker, stop_stat_event_worker

SERVER_STARTED_AT: datetime | None = None
BROKER_IDLE_TIMEOUT_SECONDS = 10
DEFAULT_STATS_RANGE = "all"
DEFAULT_STATS_BUCKET = "1m"
DEFAULT_STATS_LIMIT = 50
DEFAULT_HOST = "0.0.0.0"

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
    global SERVER_STARTED_AT

    # setup
    SERVER_STARTED_AT = datetime.now(timezone.utc)

    logger.debug("init start")
    async with get_db() as db:
        # 테이블 생성은 IF NOT EXISTS로 멱등하다
        await set_table(db)
        await set_cursor_table(db)
        await set_app_log_table(db)
        await set_stat_event_table(db)

        await initialize_board(db)

    file_log_sink_id = logger.add("log.log")
    db_log_sink = AppLogDbSink()
    await db_log_sink.start(get_db)
    db_log_sink_id = logger.add(
        db_log_sink,
        level="DEBUG",
        enqueue=True,
    )
    await start_stat_event_worker(get_db)
    lifecycle_sink = add_lifecycle_sink(record_lifecycle)

    logger.debug("init end")
    await start_bomb_scheduler()

    yield  # app 실행

    # teardown
    await stop_bomb_scheduler()

    await EventBroker.wait_until_idle(timeout=BROKER_IDLE_TIMEOUT_SECONDS)

    remove_lifecycle_sink(lifecycle_sink)
    await stop_stat_event_worker()
    logger.remove(db_log_sink_id)
    await db_log_sink.stop()
    logger.remove(file_log_sink_id)

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# receiver 등록 (import 부수효과) — app을 import하면 항상 등록되도록 보장한다
import receiver  # noqa: E402, F401


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


@app.get("/stats/dashboard")
async def stats_dashboard(
    range: str = DEFAULT_STATS_RANGE,
    bucket: str = DEFAULT_STATS_BUCKET,
    limit: int = DEFAULT_STATS_LIMIT,
):
    async with get_db() as db:
        return await get_dashboard(
            db,
            range_value=range,
            bucket=bucket,
            limit=limit,
            active_cursors=_active_cursors(),
            current_connections=len(ConnectionHandler.conn_dict),
            uptime=_uptime(),
        )


def _active_cursors():
    cursors = []
    connection_ids = set(ConnectionHandler.conn_dict.keys())

    for cursor_id, cursor in list(CursorHandler.cursor_dict.items()):
        if cursor_id not in connection_ids:
            continue

        position = cursor.position
        cursors.append(
            ActiveCursor(
                connection_id=cursor_id,
                cursor_id=cursor_id,
                color=int(cursor.color),
                tile_id=f"tile:{position.x}:{position.y}",
                x=position.x,
                y=position.y,
                score=cursor.score,
                is_alive=cursor.is_alive,
                active_at=cursor.active_at.isoformat(),
                window=CursorWindow(width=cursor.width, height=cursor.height),
            )
        )

    return sorted(cursors, key=lambda cursor: cursor.cursor_id)


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


def _required_port() -> int:
    port = os.getenv("PORT")
    if not port:
        raise RuntimeError("PORT is required")
    try:
        return int(port)
    except ValueError as e:
        raise RuntimeError("PORT must be an integer") from e


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=DEFAULT_HOST, port=_required_port())
