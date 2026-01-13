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
        DismantleMine
    )


class ServerMessage:
    from .internal.base import ServerMessage as Base

    from .internal.server import (
        Chat,
        MyCursor,
        CursorsState,
        TilesState,
        Explosion,
        ScoreBoardState,
        QuitCursor
    )
