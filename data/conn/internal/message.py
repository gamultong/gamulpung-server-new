from typing import Generic, TypeVar, Type

from core.dataobj import DataObj
from core.event import Event, EventEnum
from data.payload import ClientMessage
from data.event import ClientEvent

from .exceptions import (
    InvalidFormat_Exception
)


EVENT_TYPE = TypeVar("EVENT_TYPE", bound=Event)


class MessageFormat(DataObj):
    class Header(DataObj):
        event: EventEnum

    header: Header
    payload: dict


def __exception_by_invalid_format(func):
    def wrapper(json: dict):
        try:
            return func(json)
        except KeyError:
            raise InvalidFormat_Exception(json)
    return wrapper


@__exception_by_invalid_format
def json_to_format(json: dict):
    header = json["header"]
    event = json["header"]["event"]

    header = MessageFormat.Header(event)

    payload = json["payload"]

    return MessageFormat(
        header=header,
        payload=payload
    )


def get_payload_by_event_name(event_name: EventEnum) -> Type[ClientMessage.Base]:  # type:ignore
    match event_name:
        case ClientEvent.CHAT:
            return ClientMessage.Chat
        case ClientEvent.CREATE_CURSOR:
            return ClientMessage.CreateCursor
        case ClientEvent.SET_WINDOW:
            return ClientMessage.SetWindow
        case ClientEvent.MOVE:
            return ClientMessage.Move
        case ClientEvent.OPEN_TILES:
            return ClientMessage.OpenTiles
        case ClientEvent.SET_FLAG:
            return ClientMessage.SetFlag
        case ClientEvent.DISMANTLE_MINE:
            return ClientMessage.DismantleMine
        case ClientEvent.INSTALL_BOMB:
            return ClientMessage.InstallBomb
    raise


class Message(Generic[EVENT_TYPE], DataObj):
    event: EVENT_TYPE

    def to_dict(self):
        return {
            "header": {
                "event": self.event.event_name
            },
            "payload": self.event.payload.to_dict()
        }

    @classmethod
    def from_json(cls, json: dict):
        form = json_to_format(json)

        event_name = form.header.event
        payload_type = get_payload_by_event_name(event_name)
        payload = payload_type.from_dict(form.payload)

        event = Event(
            event_name=event_name,
            payload=payload
        )
        return cls(event=event)  # type:ignore
