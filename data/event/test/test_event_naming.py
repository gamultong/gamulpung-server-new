import unittest
from data.event.internal.internal import InternalEvent
from data.event.internal.external import ClientEvent, ServerEvent
from data.event.internal.trigger import TriggerEvent
from core.event.internal.event import EventEnum


class EventNaming_TestCase(unittest.TestCase):
    def assertEnumHasNames(self, enum_cls: type[EventEnum], expected_names):
        """EventEnum에 지정된 name만이 들어갔는지 검사"""
        self.assertCountEqual(enum_cls.__members__.keys(), expected_names)

    def assertEnumValuesUnique(self, enum_cls: type[EventEnum]):
        """alias 포함 value 전체를 검사하여 중복 검사"""
        values = [m.value for m in enum_cls.__members__.values()]
        self.assertEqual(
            len(values), len(set(values)),
            f"{enum_cls.__name__} has duplicated values (including aliases)"
        )

    def test_scope_parts(self):
        self.assertEqual(ClientEvent.__scope_part__, "CLIENT")
        self.assertEqual(ServerEvent.__scope_part__, "SERVER")
        self.assertEqual(InternalEvent.__scope_part__, "INTERNAL")
        self.assertEqual(TriggerEvent.__scope_part__, "TRIGGER")

    def test_client_event_members(self):
        self.assertEnumHasNames(
            ClientEvent,
            ["CHAT", "CREATE_CURSOR", "MOVE", "OPEN_TILES", "SET_FLAG", "SET_WINDOW", "DISMANTLE_MINE", "INSTALL_BOMB"],
        )
        self.assertEnumValuesUnique(ClientEvent)

    def test_server_event_members(self):
        self.assertEnumHasNames(
            ServerEvent,
            ["CHAT", "CURSORS_STATE", "EXPLOSION", "SCOREBOARD_STATE", "TILES_STATE", "MY_CURSOR", "QUIT_CURSOR"],
        )
        self.assertEnumValuesUnique(ServerEvent)

    def test_internal_event_members(self):
        self.assertEnumHasNames(
            InternalEvent,
            ["NOTIFY_CURSORS", "NOTIFY_EXPLOSION", "NOTIFY_SCOREBOARD", "NOTIFY_TILES", "SETTED_WINDOW"],
        )
        self.assertEnumValuesUnique(InternalEvent)

    def test_trigger_event_members(self):
        self.assertEnumHasNames(TriggerEvent, ["JOIN", "QUIT"])
        self.assertEnumValuesUnique(TriggerEvent)

    def test_value_format_is_kebab_case(self):
        """EventEnum.__new__에서 "_"를 "-"로 바꾸는 규칙 검증"""
        self.assertEqual(ClientEvent.OPEN_TILES.value, "OPEN-TILES")
        self.assertEqual(ServerEvent.CURSORS_STATE.value, "CURSORS-STATE")
        self.assertEqual(InternalEvent.NOTIFY_SCOREBOARD.value, "NOTIFY-SCOREBOARD")

    def test_scope_is_accumulated(self):
        """ScopedBase __init_subclass__ 규칙: 부모 scope + 자신의 __scope_part__가 누적되는지 검증"""
        self.assertEqual(ClientEvent.CHAT.get_scope(), "EXTERNAL.CLIENT")
        self.assertEqual(ServerEvent.CHAT.get_scope(), "EXTERNAL.SERVER")
        self.assertEqual(InternalEvent.NOTIFY_TILES.get_scope(), "INTERNAL")
        self.assertEqual(TriggerEvent.JOIN.get_scope(), "TRIGGER")


if __name__ == "__main__":
    from unittest import main
    main()
