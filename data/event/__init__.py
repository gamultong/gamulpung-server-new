from .internal.external import ServerEvent, ClientEvent
from .internal.internal import InternalEvent
from .internal.trigger import TriggerEvent


if __name__ == "__main__":
    print(ServerEvent.CHAT.get_scope())
    print(ServerEvent.CHAT)
    print(TriggerEvent.JOIN.get_scope())