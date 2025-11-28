from typing import Generic, TypeVar, Type

from core.dataobj import DataObj
from core.event import Event, ExternalC2SEvent, EventEnum
from data.payload import ClientMessage

from .exceptions import (
    InvalidFormat_Exception,
    InvalidEvent_Exception
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
        case ExternalC2SEvent.CHAT:
            return ClientMessage.Chat
        case ExternalC2SEvent.SET_WINDOW:
            return ClientMessage.SetWindow
        case ExternalC2SEvent.MOVE:
            return ClientMessage.Move
        case ExternalC2SEvent.OPEN_TILES:
            return ClientMessage.OpenTiles
        case ExternalC2SEvent.SET_FLAG:
            return ClientMessage.SetFlag
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
