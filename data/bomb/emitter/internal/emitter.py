from core.event import Event
from data.bomb import InstalledBomb


class BombEmitter:
    @classmethod
    def get_installed_events(cls, bomb: InstalledBomb) -> list[Event]:
        from data.event import InternalEvent
        from data.payload import IdDataPayload

        return [
            Event(
                event_name=InternalEvent.INSTALLED_BOMB,
                payload=IdDataPayload(
                    id=bomb.cur_id,
                    data=bomb,
                ),
            )
        ]

    @classmethod
    def get_draw_events(cls, bomb: InstalledBomb) -> list[Event]:
        from data.event import TriggerEvent
        from data.payload import IdDataPayload

        return [
            Event(
                event_name=TriggerEvent.DRAW_BOARD,
                payload=IdDataPayload(
                    id=bomb.cur_id,
                    data=bomb,
                ),
            )
        ]
