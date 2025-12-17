import os
from dodoenv import load_dotenv, Env  # type:ignore <= 이거 정상임

load_dotenv("game.env")
load_dotenv(".env")


class BoardConfig:
    LENGTH = Env[int](func=int)
    MINE_RATIO = Env[float](func=float)
    DB_PATH = Env[str]()


class CursorConfig:
    REVIVE_SECONDS = Env[int](func=int)


class SentryConfig:
    # SENTRY_DSN은 선택적 (없으면 Sentry 비활성화)
    _sentry_dsn = os.getenv("SENTRY_DSN", "")
    SENTRY_DSN = _sentry_dsn
