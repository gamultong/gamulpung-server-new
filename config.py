from dodoenv import load_dotenv, Env  # type:ignore <= 이거 정상임

load_dotenv("game.env")


class BoardConfig:
    LENGTH = Env[int](func=int)
    MINE_RATIO = Env[float](func=float)
    DB_PATH = Env[str]()
