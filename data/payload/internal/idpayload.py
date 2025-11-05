from core.dataobj import DataObj
from core.event import Payload
from typing import TypeVar, Generic

ID_TYPE = TypeVar("ID_TYPE")
DATA_TYPE = TypeVar("DATA_TYPE", bound=DataObj)


class IdPayload(Generic[ID_TYPE], Payload):
    id: ID_TYPE


class IdDataPayload(Generic[ID_TYPE, DATA_TYPE], Payload):
    id: ID_TYPE
    data: DATA_TYPE
