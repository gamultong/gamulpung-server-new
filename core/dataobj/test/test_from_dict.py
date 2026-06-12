# from __future__ import annotations 환경에서 from_dict가 동작해야 한다 (회귀 검증)
from __future__ import annotations

from core.dataobj import DataObj


class Inner(DataObj):
    value: int


class Outer(DataObj):
    name: str
    inner: Inner


class WithList(DataObj):
    items: list[Inner]


class WithOptional(DataObj):
    inner: Inner | None


class Base(DataObj):
    base_field: int


class Child(Base):
    child_field: str


class TestFromDict:
    def test_중첩_DataObj_필드를_객체로_복원한다(self):
        """문자열 어노테이션(future annotations)에서도 중첩 필드가 raw dict로 새지 않아야 한다"""
        outer = Outer.from_dict({"name": "a", "inner": {"value": 1}})

        assert isinstance(outer.inner, Inner)
        assert outer.inner.value == 1

    def test_list_제네릭_내부의_DataObj를_복원한다(self):
        obj = WithList.from_dict({"items": [{"value": 1}, {"value": 2}]})

        assert all(isinstance(i, Inner) for i in obj.items)
        assert [i.value for i in obj.items] == [1, 2]

    def test_union_필드는_None과_객체를_모두_처리한다(self):
        with_none = WithOptional.from_dict({"inner": None})
        with_value = WithOptional.from_dict({"inner": {"value": 3}})

        assert with_none.inner is None
        assert isinstance(with_value.inner, Inner)
        assert with_value.inner.value == 3

    def test_상속받은_필드도_복원한다(self):
        """raw __annotations__는 부모 필드를 누락하므로 get_type_hints 해석을 검증한다"""
        child = Child.from_dict({"base_field": 1, "child_field": "x"})

        assert child.base_field == 1
        assert child.child_field == "x"

    def test_to_dict_from_dict_왕복이_동등하다(self):
        outer = Outer(name="a", inner=Inner(value=1))

        assert Outer.from_dict(outer.to_dict()) == outer
