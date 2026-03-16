from .internal.base import ExternalMessageBase


class ClientMessage:
    from .internal.base import ClientMessage as Base

    from .internal.client import (
        Chat,
        CreateCursor,
        SetWindow,
        Move,
        OpenTiles,
        SetFlag,
        DismantleMine,
        InstallBomb,
    )


class ServerMessage:
    from .internal.base import ServerMessage as Base

    from .internal.server import (
        Chat,
        MyCursor,
        CursorsState,
        TilesState,
        ColoredTilesState,
        BombPosition,
        Explosion,
        ScoreBoardState,
        QuitCursor
    )
