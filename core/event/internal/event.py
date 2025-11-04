from __future__ import annotations

from core.dataobj import DataObj
from typing import Generic, TypeVar, ClassVar


class Payload(DataObj):
    pass


PAYLOAD_TYPE = TypeVar("PAYLOAD_TYPE", bound=Payload)


class Event(Generic[PAYLOAD_TYPE], DataObj):
    event_name: str
    payload: PAYLOAD_TYPE
