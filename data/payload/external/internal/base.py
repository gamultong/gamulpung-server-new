from core.event import Payload


class ExternalMessageBase(Payload):
    pass


class ServerMessage(ExternalMessageBase):
    pass


class ClientMessage(ExternalMessageBase):
    pass
