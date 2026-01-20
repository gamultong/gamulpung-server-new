from core.event import Event
from data.cursor import Cursor
from data.payload import IdPayload, IdDataPayload
from data.event import InternalEvent


def get_cursor_create_events(cursor: Cursor) -> list[Event]:
    """Cursor 생성 시 Event 목록 반환"""
    events: list[Event] = []

    # Cursor 생성 시 NOTIFY_CURSORS 발행
    events.append(Event(
        event_name=InternalEvent.NOTIFY_CURSORS,
        payload=IdPayload(id=cursor.id)
    ))

    # Cursor 생성 시 SETTED_WINDOW 발행
    events.append(Event(
        event_name=InternalEvent.SETTED_WINDOW,
        payload=IdPayload(id=cursor.id)
    ))

    return events


def get_cursor_move_events(old: Cursor, new: Cursor) -> list[Event]:
    """Cursor 이동 시 Event 목록 반환"""
    events: list[Event] = []

    # Cursor 이동 시 NOTIFY_CURSORS 발행
    events.append(Event(
        event_name=InternalEvent.NOTIFY_CURSORS,
        payload=IdDataPayload(id=new.id, data=old)
    ))

    # Cursor 이동 시 SETTED_WINDOW 발행
    events.append(Event(
        event_name=InternalEvent.SETTED_WINDOW,
        payload=IdDataPayload(id=new.id, data=old)
    ))

    return events


def get_cursor_death_events(old: Cursor, new: Cursor) -> list[Event]:
    """Cursor 사망 시 Event 목록 반환"""
    events: list[Event] = []

    # Cursor 사망 시 NOTIFY_CURSORS 발행
    events.append(Event(
        event_name=InternalEvent.NOTIFY_CURSORS,
        payload=IdDataPayload(id=new.id, data=old)
    ))

    return events


def get_cursor_score_events(old: Cursor, new: Cursor) -> list[Event]:
    """Cursor 점수 증가 시 Event 목록 반환"""
    events: list[Event] = []

    # Cursor 점수 증가 시 NOTIFY_CURSORS 발행
    events.append(Event(
        event_name=InternalEvent.NOTIFY_CURSORS,
        payload=IdDataPayload(id=new.id, data=old)
    ))

    return events


def get_cursor_window_events(old: Cursor, new: Cursor) -> list[Event]:
    """Cursor window 변경 시 Event 목록 반환"""
    events: list[Event] = []

    # Cursor window 변경 시 SETTED_WINDOW 발행
    events.append(Event(
        event_name=InternalEvent.SETTED_WINDOW,
        payload=IdPayload(id=new.id)
    ))

    return events


def get_mine_grant_events(old: Cursor, new: Cursor) -> list[Event]:
    """Cursor 점수 증가 시 Event 목록 반환"""
    events: list[Event] = []

    # Cursor 점수 증가 시 NOTIFY_CURSORS 발행
    events.append(Event(
        event_name=InternalEvent.NOTIFY_CURSORS,
        payload=IdDataPayload(id=new.id, data=old)
    ))

    return events
