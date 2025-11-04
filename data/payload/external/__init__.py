from .internal.base import ExternalMessageBase


class ClientMessage:
    from .internal.base import ClientMessage as Base

    from .internal.client import (
        Chat
    )


class ServerMessage:
    from .internal.base import ServerMessage as Base

    from .internal.server import (
        Chat,
        MyCursor
    )
