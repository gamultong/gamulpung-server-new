from core.event import Event
from data.bomb import InstalledBomb


class BombEmitter:
    @classmethod
    def get_installed_events(cls, owner_id: str, bomb: InstalledBomb) -> list[Event]:
        from data.event import InternalEvent
        from data.payload import IdDataPayload

        return [
            Event(
                event_name=InternalEvent.INSTALLED_BOMB,
                payload=IdDataPayload(
                    id=owner_id,
                    data=bomb,
                ),
            )
        ]

    @classmethod
    def get_draw_events(cls, owner_id: str, bomb: InstalledBomb) -> list[Event]:
        from data.event import TriggerEvent
        from data.payload import IdDataPayload

        return [
            Event(
                event_name=TriggerEvent.DRAW_BOARD,
                payload=IdDataPayload(
                    id=owner_id,
                    data=bomb,
                ),
            )
        ]
